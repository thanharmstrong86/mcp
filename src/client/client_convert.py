import json
import os
from dotenv import load_dotenv
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
import logging
from langchain.tools import tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@tool
async def upload_file(file_path, delete_after=False):
    """Upload file content to the MCP upload server via Starlette endpoint."""
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "application/pdf")}
            data = {"delete_after": str(delete_after).lower()}
            response = requests.post("http://127.0.0.1:8000/mcp/upload_pdf_tool", files=files, data=data)
            response.raise_for_status()
            server_response_data = response.json()
            logger.info(f"File {file_name} uploaded successfully to MCP upload server")
            return json.dumps(server_response_data)
    except Exception as e:
        logger.error(f"File upload failed for {file_name}: {str(e)}")
        raise

async def main():
    try:
        # Fetch available tools from the MCP servers
        tools = await client.get_tools()
        tools.append(upload_file)
        print("Available Tools:", [tool.name for tool in tools])

        # Create a reactive agent with the model and tools
        agent = create_react_agent(model, tools)

        # Check if input.pdf exists in the input directory
        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(f"PDF file {INPUT_FILE} not found in {INPUT_DIR}")

        # Upload the file to the MCP upload server
        file_name = os.path.basename(INPUT_FILE)
        print(f"Using input file: {INPUT_FILE}")

        # Natural language input for the agent to use the custom upload_file_via_api tool
        upload_input = {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Please upload the file located at '{INPUT_FILE}' to the server "
                        f"and do not delete it after upload."
                    )
                }
            ]
        }
        print("Sending upload request via agent...")
        upload_response = await agent.ainvoke(upload_input)
         # Extract the tool output from the response to get the server-side path
        server_file_path = None
        for msg in upload_response.get("messages", []):
            if msg.type == "tool" and msg.name == "upload_file":
                try:
                    tool_output_json = json.loads(msg.content)
                    if tool_output_json.get("status") == "uploaded":
                        server_file_path = tool_output_json.get("path")
                        logger.info(f"Successfully extracted server file path: {server_file_path}")
                        break
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from upload_file tool output: {msg.content}")

        if not server_file_path:
            logger.error("Failed to get server file path from upload response. Cannot proceed with conversion.")
            return # Exit if we don't have the path

        # Print detailed upload response for debugging
        print("Upload Response:")
        for msg in upload_response.get("messages", []):
            msg_type = getattr(msg, "type", getattr(msg, "role", "unknown"))
            msg_content = getattr(msg, "content", "No content")
            print(f"  Message Type: {msg_type}, Content: {msg_content[:200]}...")
            print(f"  Message Attributes: {vars(msg)}")

        # Convert the uploaded PDF to Markdown
        convert_input = {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Now, use the convert_pdf_to_markdown_tool to convert the file "
                        f"'{server_file_path}' (which is already on the server)."
                    )
                }
            ]
        }
        print("\n--- Converting PDF to Markdown via agent ---")
        convert_response = await agent.ainvoke(convert_input)
        print("Conversion Response:")
        for msg in convert_response.get("messages", []):
            msg_type = getattr(msg, "type", getattr(msg, "role", "unknown"))
            msg_content = getattr(msg, "content", "No content")
            print(f"  Message Type: {msg_type}, Content: {msg_content}")

    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    asyncio.run(main())