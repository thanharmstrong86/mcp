import json
import os
from dotenv import load_dotenv
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the project root (one level up from src/client)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Load environment variables from .env in the project root
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

# Initialize the Gemini model
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY_2")
)

# Configure the MultiServerMCPClient for the crawl_mcp server
client = MultiServerMCPClient(
    {
        "crawl": {
            "url": "http://127.0.0.1:8002/mcp",
            "transport": "streamable_http",
        }
    }
)

async def main():
    try:
        # Fetch available tools from the MCP server
        tools = await client.get_tools()
        print("Available Tools:", [tool.name for tool in tools])

        # Create a reactive agent with the model and tools
        agent = create_react_agent(model, tools)

        # Define the URL to crawl
        target_url = "https://chewychewy.vn"
        print(f"Using target URL: {target_url}")

        # Natural language input for the agent to use the crawl_website_tool
        crawl_input = {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Please crawl the website at '{target_url}' "
                        f"using the crawl_website_tool."
                    )
                }
            ]
        }
        print("Sending crawl request via agent...")
        crawl_response = await agent.ainvoke(crawl_input)

        # Extract the download URL from the response
        download_url = None
        for msg in crawl_response.get("messages", []):
            if msg.type == "tool" and msg.name == "crawl_website_tool":
                try:
                    tool_output_json = json.loads(msg.content)
                    if tool_output_json.get("status") == "success":
                        download_url = tool_output_json.get("download_url")
                        logger.info(f"Successfully extracted download URL: {download_url}")
                        break
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from crawl_website_tool output: {msg.content}")

        if not download_url:
            logger.error("Failed to get download URL from crawl response.")
            return

        # Print detailed crawl response for debugging
        print("Crawl Response:")
        for msg in crawl_response.get("messages", []):
            msg_type = getattr(msg, "type", getattr(msg, "role", "unknown"))
            msg_content = getattr(msg, "content", "No content")
            print(f"  Message Type: {msg_type}, Content: {msg_content[:200]}...")
            print(f"  Message Attributes: {vars(msg)}")

        # Optionally download the Markdown file
        print("\n--- Downloading Markdown file ---")
        response = requests.get(download_url)
        response.raise_for_status()
        output_file = os.path.join(OUTPUT_DIR, "crawled_output.md")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Markdown file saved to {output_file}")

    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    asyncio.run(main())