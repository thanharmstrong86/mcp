#!/usr/bin/env python3
"""MCP Server for Weather and Greetings using FastMCP"""

import os
import uvicorn
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Example")

@mcp.tool()
async def greet(name: str) -> str:
    """Greet the user."""
    return f"Hello, {name}! How are you?"

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    return f"It's always sunny in {location}"

def main():
    """Run the MCP server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print("Starting MCP Weather server...")
    print(f"HOST: {host}")
    print(f"PORT: {port}")
    print("MCP endpoint will be available at the server URL + /mcp")

    # For production (e.g., Docker) or when binding to 0.0.0.0, use Uvicorn directly
    if host == "0.0.0.0" or os.getenv("RAILWAY_ENVIRONMENT"):
        print("🚀 PRODUCTION MODE: Using FastMCP's streamable_http_app directly")

        try:
            # Get the streamable HTTP app from FastMCP
            app = mcp.streamable_http_app()

            if app is None:
                raise AttributeError("streamable_http_app() returned None")

            print(f"✅ SUCCESS: Got streamable_http_app from FastMCP!")
            print(f"App type: {type(app)}")
            print(f"Running Uvicorn on {host}:{port}")

            # Run with Uvicorn directly
            uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)

        except Exception as e:
            print(f"❌ Could not get streamable_http_app: {e}")
            print("🔄 Falling back to FastMCP default...")

            # Fallback to FastMCP's default run method
            mcp.run(transport="streamable-http")
    else:
        print("🏠 LOCAL DEVELOPMENT: Using FastMCP default")
        mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()