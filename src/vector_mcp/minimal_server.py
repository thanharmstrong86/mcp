#!/usr/bin/env python3
"""
Minimal Vector MCP Server for testing.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables
env_file = os.path.join(current_dir, ".env")
load_dotenv(env_file)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_minimal_server():
    """Create a minimal MCP server."""
    
    try:
        from mcp.server.fastmcp import FastMCP
        import uvicorn
        
        # Create FastMCP instance
        mcp = FastMCP()
        
        # Get the Starlette app
        app = mcp.streamable_http_app()
        
        # Add a simple health check
        @app.route("/health", methods=["GET"])
        async def health_check():
            from starlette.responses import JSONResponse
            return JSONResponse({
                "status": "healthy",
                "service": "vector-mcp-minimal",
                "version": "0.1.0"
            })
        
        # Add a simple MCP tool
        @mcp.tool()
        def test_tool() -> dict:
            """A simple test tool."""
            return {"status": "success", "message": "Test tool is working!"}
        
        logger.info("Starting minimal Vector MCP server on 127.0.0.1:8003")
        logger.info("Health check: http://127.0.0.1:8003/health")
        logger.info("MCP endpoint: http://127.0.0.1:8003/mcp")
        
        # Start the server
        uvicorn.run(app, host="127.0.0.1", port=8003, log_level="info")
        
    except Exception as e:
        logger.error(f"Failed to start minimal server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_minimal_server()