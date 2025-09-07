#!/usr/bin/env python3
"""
Test client for Vector MCP server.
Tests vector indexing functionality by reading markdown files and indexing them.
"""

import asyncio
import os
import json
import sys
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Load environment variables
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

# Initialize the Gemini model
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY_2")
)

# Configure the MCP client for vector server
client = MultiServerMCPClient(
    {
        "vector": {
            "url": "http://127.0.0.1:8003/mcp",
            "transport": "streamable_http",
        }
    }
)

async def test_vector_indexing():
    """Test vector indexing functionality."""
    try:
        print("🔗 Connecting to Vector MCP server...")
        
        # Fetch available tools from the MCP server
        try:
            tools = await client.get_tools()
            print(f"✅ Available tools: {[tool.name for tool in tools]}")
        except Exception as e:
            print(f"❌ Error getting tools from Vector MCP server: {e}")
            return
        
        # Create a reactive agent with the model and tools
        print("🤖 Creating reactive agent...")
        agent = create_react_agent(model, tools)
        
        # Test 1: Get vector store info
        print("\n📊 Test 1: Getting vector store information...")
        info_input = {
            "messages": [
                {
                    "role": "user",
                    "content": "Please get information about the vector store using get_vector_store_info"
                }
            ]
        }
        
        try:
            info_response = await agent.ainvoke(info_input)
            print("Vector store info response:")
            for msg in info_response.get("messages", []):
                if hasattr(msg, 'content'):
                    print(f"  {msg.content}")
        except Exception as e:
            print(f"❌ Error getting vector store info: {e}")
        
        # Test 2: Find and index markdown files
        print(f"\n📁 Test 2: Looking for markdown files in {OUTPUT_DIR}...")
        
        if not os.path.exists(OUTPUT_DIR):
            print(f"❌ Output directory {OUTPUT_DIR} not found")
            return
        
        # Find markdown files
        md_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.md')]
        if not md_files:
            print(f"❌ No markdown files found in {OUTPUT_DIR}")
            return
        
        print(f"✅ Found {len(md_files)} markdown file(s): {md_files}")
        
        # Test indexing the first markdown file
        md_file = md_files[0]
        md_path = os.path.join(OUTPUT_DIR, md_file)
        
        print(f"\n🔍 Test 3: Indexing markdown file: {md_file}")
        
        index_input = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Please index the markdown file at '{md_path}' using index_markdown_file"
                }
            ]
        }
        
        try:
            index_response = await agent.ainvoke(index_input)
            print("Indexing response:")
            for msg in index_response.get("messages", []):
                if hasattr(msg, 'content'):
                    print(f"  {msg.content}")
        except Exception as e:
            print(f"❌ Error indexing file: {e}")
        
        # Test 4: Get updated vector store info
        print(f"\n📊 Test 5: Getting updated vector store information...")
        
        try:
            final_info_response = await agent.ainvoke(info_input)
            print("Updated vector store info:")
            for msg in final_info_response.get("messages", []):
                if hasattr(msg, 'content'):
                    print(f"  {msg.content}")
        except Exception as e:
            print(f"❌ Error getting updated vector store info: {e}")
        
        print("\n✅ Vector indexing tests completed!")
        
    except Exception as e:
        print(f"❌ Error during vector indexing tests: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function."""
    print("🚀 Starting Vector MCP Client Tests")
    print("=" * 50)
    
    # Check if required environment variables are set
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY_2"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return
    
    print("✅ All required environment variables are set")
    
    await test_vector_indexing()

if __name__ == "__main__":
    asyncio.run(main())