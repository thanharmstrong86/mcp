#!/usr/bin/env python3
"""
Debug startup script for Vector MCP Server with detailed error reporting.
"""

import sys
import os
import traceback

def debug_startup():
    """Debug the server startup process."""
    
    print("🔍 Vector MCP Server Debug Startup")
    print("=" * 50)
    
    try:
        # Step 1: Check Python path
        print("1. Checking Python path...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"   Current directory: {current_dir}")
        sys.path.insert(0, current_dir)
        print(f"   Added to Python path: {current_dir}")
        
        # Step 2: Check environment file
        print("\n2. Checking environment file...")
        env_file = os.path.join(current_dir, ".env")
        if os.path.exists(env_file):
            print(f"   ✅ Found .env file: {env_file}")
            # Load and check key variables
            from dotenv import load_dotenv
            load_dotenv(env_file)
            
            supabase_url = os.getenv('SUPABASE_URL')
            openai_key = os.getenv('OPENAI_API_KEY')
            
            print(f"   SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
            print(f"   OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Missing'}")
        else:
            print(f"   ❌ .env file not found: {env_file}")
        
        # Step 3: Try importing modules
        print("\n3. Testing imports...")
        try:
            from src.vector_mcp import main
            print("   ✅ Successfully imported main function")
        except ImportError as e:
            print(f"   ❌ Import error: {e}")
            print("   Trying alternative import...")
            try:
                from src.vector_config import VectorIndexingConfig
                print("   ✅ Can import VectorIndexingConfig")
                from src.embedding_service import EmbeddingService
                print("   ✅ Can import EmbeddingService")
                from src.supabase_vector_store import SupabaseVectorStore
                print("   ✅ Can import SupabaseVectorStore")
            except ImportError as e2:
                print(f"   ❌ Alternative import error: {e2}")
                return False
        
        # Step 4: Try starting the server
        print("\n4. Starting server...")
        from src.vector_mcp import main
        main()
        
    except Exception as e:
        print(f"\n❌ Error during startup: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_startup()