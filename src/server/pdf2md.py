import pdfplumber
import ocrmypdf
from langgraph.graph import StateGraph, END
from typing import Dict, TypedDict
import re
import os
from pathlib import Path

# Define the project root (two levels up from src/server)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = "/app/uploaded" if os.getenv("DOCKER_ENV") else os.path.join(PROJECT_ROOT, "uploaded")
OUTPUT_DIR = "/app/output" if os.getenv("DOCKER_ENV") else os.path.join(PROJECT_ROOT, "output")
TEMP_DIR = "/app/temp" if os.getenv("DOCKER_ENV") else os.path.join(PROJECT_ROOT, "temp")

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Define the state for the LangGraph workflow
class ConversionState(TypedDict):
    pdf_path: str
    raw_text: str
    markdown_text: str
    error: str
    is_scanned: bool

# Node to check if PDF is scanned (no selectable text)
def check_pdf_type(state: ConversionState) -> ConversionState:
    try:
        with pdfplumber.open(state["pdf_path"]) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            state["is_scanned"] = not bool(text and text.strip())
        return state
    except Exception as e:
        return {"error": f"Failed to check PDF type: {str(e)}", "is_scanned": False}

# Node to extract text from PDF (with OCR fallback for scanned PDFs)
def extract_text_from_pdf(state: ConversionState) -> ConversionState:
    if state["error"]:
        return state
    
    try:
        if state["is_scanned"]:
            # Perform OCR using ocrmypdf
            temp_pdf = os.path.join(TEMP_DIR, "temp_ocr.pdf")
            ocrmypdf.ocr(state["pdf_path"], temp_pdf, force_ocr=True, language="vie+eng")
            pdf_path = temp_pdf
        else:
            pdf_path = state["pdf_path"]
        
        with pdfplumber.open(pdf_path) as pdf:
            raw_text = ""
            for page in pdf.pages:
                raw_text += page.extract_text(layout=True) + "\n"
                # Extract tables if present
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        raw_text += "\n" + format_table_to_markdown(table) + "\n"
        
        if state["is_scanned"] and os.path.exists(temp_pdf):
            os.remove(temp_pdf)
        
        return {"raw_text": raw_text, "error": ""}
    except Exception as e:
        return {"raw_text": "", "error": f"Failed to extract text: {str(e)}"}

# Helper function to format tables as Markdown
def format_table_to_markdown(table):
    if not table:
        return ""
    # Calculate max width for each column
    col_widths = [max(len(str(cell or "")) for cell in col) for col in zip(*table)]
    # Create header
    header = "| " + " | ".join(str(cell or "").ljust(width) for cell, width in zip(table[0], col_widths)) + " |"
    separator = "| " + " | ".join("-" * width for width in col_widths) + " |"
    # Create rows
    rows = [header, separator]
    for row in table[1:]:
        rows.append("| " + " | ".join(str(cell or "").ljust(width) for cell, width in zip(row, col_widths)) + " |")
    return "\n".join(rows)

# Node to process raw text into Markdown
def process_to_markdown(state: ConversionState) -> ConversionState:
    if state["error"]:
        return state
    
    raw_text = state["raw_text"]
    
    # Replace multiple newlines with double newline for Markdown paragraphs
    text = re.sub(r'\n\s*\n+', '\n\n', raw_text.strip())
    
    # Enhanced heading detection
    lines = text.split('\n')
    markdown_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Heading detection: short lines, all caps, title case, or starting with numbers
        if len(line) < 60 and (line.isupper() or line.istitle() or re.match(r'^\d+\.\s+', line)):
            markdown_lines.append(f"## {line}")
        # List detection: lines starting with bullets, numbers, or symbols
        elif re.match(r'^\s*[-*•]\s+|^\d+\.\s+', line):
            markdown_lines.append(line)
        else:
            markdown_lines.append(line)
    
    markdown_text = '\n'.join(markdown_lines)
    return {"markdown_text": markdown_text, "error": ""}

# Node to save Markdown to file
def save_markdown(state: ConversionState) -> ConversionState:
    if state["error"]:
        return state
    
    try:
        # Save Markdown in OUTPUT_DIR with the same base name
        base_name = os.path.splitext(os.path.basename(state["pdf_path"]))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(state["markdown_text"])
        return {"error": "", "markdown_path": output_path}
    except Exception as e:
        return {"error": f"Failed to save Markdown: {str(e)}"}

# Define the LangGraph workflow
def build_workflow():
    workflow = StateGraph(ConversionState)
    
    workflow.add_node("check_pdf_type", check_pdf_type)
    workflow.add_node("extract_text", extract_text_from_pdf)
    workflow.add_node("process_to_markdown", process_to_markdown)
    workflow.add_node("save_markdown", save_markdown)
    
    workflow.add_edge("check_pdf_type", "extract_text")
    workflow.add_edge("extract_text", "process_to_markdown")
    workflow.add_edge("process_to_markdown", "save_markdown")
    workflow.add_edge("save_markdown", END)
    
    workflow.set_entry_point("check_pdf_type")
    return workflow.compile()

# Main function to run the conversion
def convert_pdf_to_markdown(pdf_path: str) -> dict:
    if not pdf_path.lower().endswith(".pdf"):
        return {"status": "error", "message": "Only PDF files are allowed"}
    
    if not os.path.exists(pdf_path):
        return {"status": "error", "message": f"PDF file {pdf_path} not found"}
    
    workflow = build_workflow()
    initial_state = {
        "pdf_path": pdf_path,
        "raw_text": "",
        "markdown_text": "",
        "error": "",
        "is_scanned": False
    }
    result = workflow.invoke(initial_state)
    
    if result["error"]:
        return {"status": "error", "message": result["error"]}
    else:
        return {
            "status": "success",
            "message": f"Successfully converted {pdf_path} to Markdown",
            "markdown_path": result.get("markdown_path", os.path.join(OUTPUT_DIR, f"{os.path.splitext(os.path.basename(pdf_path))[0]}.md"))
        }

if __name__ == "__main__":
    # Example usage
    pdf_file = os.path.join(UPLOAD_DIR, "input.pdf")
    result = convert_pdf_to_markdown(pdf_file)
    print(result)