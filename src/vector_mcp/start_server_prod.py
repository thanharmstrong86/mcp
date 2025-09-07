#!/usr/bin/env python3
"""
Production startup script for Vector MCP Server.
"""

if __name__ == "__main__":
    import sys
    import os
    
    # Force production mode
    os.environ["DOCKER_ENV"] = "true"
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Import and execute the main function
    from src.vector_mcp import main
    main()