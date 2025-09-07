#!/usr/bin/env python3
"""
Startup script for Vector MCP Server.
"""

import sys
import os

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the script directory to Python path so we can import from src/
sys.path.insert(0, script_dir)

# Import and run the main function
from src.vector_mcp import main

if __name__ == "__main__":
    main()