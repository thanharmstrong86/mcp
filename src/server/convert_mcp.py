from mcp.server.fastmcp import FastMCP
import os
from .pdf2md import convert_pdf_to_markdown, INPUT_DIR, OUTPUT_DIR

mcp = FastMCP("pdf2md_mcp_server",host="0.0.0.0",port=8001)

@mcp.tool()
def convert_pdf_to_markdown_tool(pdf_path: str, output_dir: str = OUTPUT_DIR) -> dict:
    """Convert a PDF file to Markdown format and save it to the specified output directory."""
    print(f"convert_pdf_to_markdown_tool called with pdf_path: {pdf_path}, output_dir: {output_dir}")
    
    # Resolve relative pdf_path to INPUT_DIR (uploaded)
    pdf_abs_path = pdf_path
    if not os.path.isabs(pdf_path):
        pdf_abs_path = os.path.join(INPUT_DIR, pdf_path)
    
    # Call convert_pdf_to_markdown from pdf2md.py
    result = convert_pdf_to_markdown(pdf_abs_path)
    
    # Adjust markdown_path if output_dir is different
    if output_dir != OUTPUT_DIR and result.get("status") == "success":
        original_md_path = result["markdown_path"]
        base_name = os.path.splitext(os.path.basename(pdf_abs_path))[0]
        new_md_path = os.path.join(output_dir, f"{base_name}.md")
        os.makedirs(output_dir, exist_ok=True)
        os.rename(original_md_path, new_md_path)
        result["markdown_path"] = new_md_path
    
    return result

if __name__ == "__main__":
    mcp.run(transport="streamable-http")