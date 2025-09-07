#!/usr/bin/env python3
"""
Test environment variable loading for vector_mcp.
"""

import os
import sys
from dotenv import load_dotenv

def test_env_loading():
    """Test environment variable loading."""
    
    print("🧪 Testing Environment Variable Loading")
    print("=" * 50)
    
    # Test 1: Check .env file exists
    env_file = "src/vector_mcp/.env"
    print(f"1. Checking .env file: {env_file}")
    if os.path.exists(env_file):
        print(f"   ✅ File exists")
        
        # Read and show content (masked)
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        print("   Content preview:")
        for line in lines[:10]:  # First 10 lines
            if line.strip() and not line.startswith('#'):
                key = line.split('=')[0]
                print(f"     {key}=***")
    else:
        print(f"   ❌ File not found")
        return
    
    # Test 2: Load environment
    print(f"\n2. Loading environment from {env_file}")
    load_dotenv(env_file, override=True)
    
    # Test 3: Check variables
    print("\n3. Checking environment variables:")
    vars_to_check = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'OPENAI_API_KEY']
    
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: Set (length: {len(value)})")
        else:
            print(f"   ❌ {var}: Missing")
    
    # Test 4: Test vector config
    print("\n4. Testing VectorIndexingConfig:")
    sys.path.insert(0, 'src/vector_mcp')
    
    try:
        from src.vector_config import VectorIndexingConfig
        config = VectorIndexingConfig.from_environment()
        
        if config:
            print(f"   ✅ Config created: {config}")
            if config.is_valid():
                print(f"   ✅ Config is valid")
            else:
                print(f"   ❌ Config is invalid")
                errors = config.get_validation_errors()
                for error in errors:
                    print(f"     - {error}")
        else:
            print(f"   ❌ Config is None")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_env_loading()