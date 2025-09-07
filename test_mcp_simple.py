#!/usr/bin/env python3
"""
Simple test to check MCP server communication without vector indexing.
"""

import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_mcp_connection():
    """Test basic MCP connection and tool listing."""
    
    print("Testing MCP server connection...")
    
    # Configure the MultiServerMCPClient
    client = MultiServerMCPClient(
        {
            "pdf2md": {
                "url": "http://127.0.0.1:8001/mcp",
                "transport": "streamable_http",
            }
        }
    )
    
    try:
        print("Fetching available tools...")
        tools = await client.get_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Test a simple tool call if available
        for tool in tools:
            if tool.name == "convert_pdf_to_markdown_tool":
                print(f"Found convert tool: {tool.name}")
                print(f"Tool description: {tool.description}")
                break
        
        print("MCP connection test completed successfully!")
        
    except Exception as e:
        print(f"MCP connection test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())