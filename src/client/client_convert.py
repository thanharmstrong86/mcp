import json
import os
from dotenv import load_dotenv
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# Define the project root (one level up from src/client)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_DIR = os.path.join(PROJECT_ROOT, "input")
INPUT_FILE = os.path.join(INPUT_DIR, "input.pdf")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Load environment variables from .env in the project root
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

# Initialize the Gemini model
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY_2")
)

# Configure the MultiServerMCPClient for both servers
client = MultiServerMCPClient(
    {
        "upload": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable_http",
        },
        "pdf2md": {
            "url": "http://127.0.0.1:8001/mcp",
            "transport": "streamable_http",
        }
    }
)

async def main():
    try:
        # Fetch available tools from the MCP servers
        tools = await client.get_tools()
        print("Available Tools:", [tool.name for tool in tools])

        # Create a reactive agent with the model and tools
        agent = create_react_agent(model, tools)

        # Check if input.pdf exists in the input directory
        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(f"PDF file {INPUT_FILE} not found in {INPUT_DIR}")
        file_path = INPUT_FILE
        file_name = os.path.basename(file_path)
        print(f"Using input file: {file_path}")

        # Upload the PDF file
        upload_input = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Use the upload_pdf tool to upload the file at {file_path} with delete_after set to False"
                }
            ]
        }
        print("Sending upload request...")
        upload_response = await agent.ainvoke(upload_input)
        print("Upload Response:")
        messages = upload_response.get("messages", [])
        for msg in messages:
            msg_type = getattr(msg, "type", getattr(msg, "role", "unknown"))
            msg_content = getattr(msg, "content", "No content")
            print(f"  Message Type: {msg_type}, Content: {msg_content}")

        # Convert the uploaded PDF to Markdown
        convert_input = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Use the convert_pdf_to_markdown_tool to convert the file {file_name} and save it to {OUTPUT_DIR}"
                }
            ]
        }
        print("Converting PDF to Markdown...")
        convert_response = await agent.ainvoke(convert_input)
        print("Conversion Response:")
        messages = convert_response.get("messages", [])
        for msg in messages:
            msg_type = getattr(msg, "type", getattr(msg, "role", "unknown"))
            msg_content = getattr(msg, "content", "No content")
            print(f"  Message Type: {msg_type}, Content: {msg_content}")

    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    asyncio.run(main())