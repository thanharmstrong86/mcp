import json
import os
from dotenv import load_dotenv
import asyncio
import tempfile
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# Define the project root (one level up from src/client)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

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

async def main():
    try:
        # Fetch available tools from the MCP server
        tools = await client.get_tools()
        print("Available Tools:", [tool.name for tool in tools])
        # Debug: Print tool schema
        for tool in tools:
            print(f"Tool Schema for {tool.name}: {tool.__dict__}")

        # Create a reactive agent with the model and tools
        agent = create_react_agent(model, tools)

        # Natural language input for the list_processed_files tool
        list_input = {
            "messages": [
                {
                    "role": "user",
                    "content": "Use the list_processed_files tool to list all processed files"
                }
            ]
        }
        print("Listing processed files...")
        list_response = await agent.ainvoke(list_input)
        print("Processed Files Response:")
        messages = list_response.get("messages", [])
        for msg in messages:
            msg_type = getattr(msg, "type", getattr(msg, "role", "unknown"))
            msg_content = getattr(msg, "content", "No content")
            print(f"  Message Type: {msg_type}, Content: {msg_content}")
            print(f"  Message Attributes: {vars(msg)}")

    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    asyncio.run(main())