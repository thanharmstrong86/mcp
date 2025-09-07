#!/usr/bin/env python3
"""
Direct startup script for Vector MCP Server.
"""

if __name__ == "__main__":
    # Direct execution of the main module
    import sys
    import os
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Import and execute the main function directly
    from src.vector_mcp import main
    main()