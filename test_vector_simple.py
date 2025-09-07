#!/usr/bin/env python3
"""
Simple test for Vector MCP server without complex dependencies.
"""

import requests
import json

def test_vector_mcp():
    """Simple test of Vector MCP server."""
    
    print("🧪 Testing Vector MCP Server")
    print("=" * 40)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8002/health")
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        print("   Make sure the server is running: uv run python src/vector_mcp/start_server.py")
        return
    
    # Test 2: MCP endpoint
    print("\n2. Testing MCP endpoint...")
    try:
        response = requests.get("http://localhost:8002/mcp")
        print(f"   MCP endpoint status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ MCP endpoint error: {e}")
    
    print("\n✅ Basic server tests completed!")
    print("If health check passed, the server is running correctly.")
    print("You can now test with the full MCP client.")

if __name__ == "__main__":
    test_vector_mcp()