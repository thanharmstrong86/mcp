import json
import os
from dotenv import load_dotenv
import asyncio
import requests
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool 

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the project root (one level up from src/client)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_DIR = os.path.join(PROJECT_ROOT, "input")
INPUT_FILE = os.path.join(INPUT_DIR, "input.pdf")

# Load environment variables from .env in the project root
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

# Initialize the Gemini model
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY_2")
)

# Configure the MultiServerMCPClient for the upload_mcp_server
client = MultiServerMCPClient(
    {
        "upload": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable_http",
        }
    }
)

@tool
async def upload_file(file_path, delete_after=False):
    """Upload file content to the server via Starlette endpoint."""
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "application/pdf")}
            data = {"delete_after": str(delete_after).lower()}
            response = requests.post("http://127.0.0.1:8001/upload/mcp/upload_pdf_tool", files=files, data=data)
            response.raise_for_status()
            logger.info(f"File {file_name} uploaded successfully")
            return file_name
    except Exception as e:
        logger.error(f"File upload failed for {file_name}: {str(e)}")
        raise

async def main():
    try:
        # Fetch available tools from the MCP server
        tools = await client.get_tools()
        tools.append(upload_file)
        logger.info("Available Tools: %s", [tool.name for tool in tools])
        for tool in tools:
            logger.info("Tool Schema for %s: %s", tool.name, tool.__dict__)

        # Create a reactive agent with the model and tools
        agent = create_react_agent(model, tools)

        # Check if input.pdf exists in the input directory
        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(f"PDF file {INPUT_FILE} not found in {INPUT_DIR}")

        # Upload the file to the server
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
        print("Upload Response:")
        messages = upload_response.get("messages", [])
        for msg in messages:
            msg_type = getattr(msg, "type", getattr(msg, "role", "unknown"))
            msg_content = getattr(msg, "content", "No content")
            print(f"  Message Type: {msg_type}, Content: {msg_content[:200]}...") # Truncate content for display
            print(f"  Message Attributes: {vars(msg)}")

        # Natural language input for the file_status tool
        status_input = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Use the file_status tool to check the status of the file {file_name}"
                }
            ]
        }

        logger.info("Checking file status...")
        status_response = await agent.ainvoke(status_input)
        logger.info("File Status Response:")
        messages = status_response.get("messages", [])
        for msg in messages:
            msg_type = getattr(msg, "type", getattr(msg, "role", "unknown"))
            msg_content = getattr(msg, "content", "No content")
            logger.info(" Message Type: %s, Content: %s", msg_type, msg_content)
            logger.debug(" Message Attributes: %s", vars(msg))

        # Optional: List processed files
        list_input = {
            "messages": [
                {
                    "role": "user",
                    "content": "Use the list_processed_files tool to list all processed files"
                }
            ]
        }

        logger.info("Listing processed files...")
        list_response = await agent.ainvoke(list_input)
        logger.info("List Processed Files Response:")
        messages = list_response.get("messages", [])
        for msg in messages:
            msg_type = getattr(msg, "type", getattr(msg, "role", "unknown"))
            msg_content = getattr(msg, "content", "No content")
            logger.info(" Message Type: %s, Content: %s", msg_type, msg_content)
            logger.debug(" Message Attributes: %s", vars(msg))

    except Exception as e:
        logger.error("Error: %s", str(e))
        raise

if __name__ == "__main__":
    asyncio.run(main())