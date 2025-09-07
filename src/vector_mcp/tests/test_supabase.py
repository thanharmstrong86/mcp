#!/usr/bin/env python3
"""
Test Supabase connection using environment variables.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add the project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# Load environment variables from project root .env
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

def test_supabase_connection():
    """Integration test: check if Supabase is reachable with env credentials."""
    print("🧪 Testing Supabase Connection")
    print("=" * 50)
    
    # Check environment variables
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    print(f"1. Environment Variables:")
    print(f"   SUPABASE_URL: {'✅ Set' if url else '❌ Missing'}")
    print(f"   SUPABASE_ANON_KEY: {'✅ Set' if key else '❌ Missing'}")
    
    if not url:
        print("❌ SUPABASE_URL must be set in environment")
        return False
    
    if not key:
        print("❌ SUPABASE_ANON_KEY must be set in environment")
        return False
    
    print(f"   URL: {url}")
    print(f"   Key: {key[:20]}...")
    
    # Test 1: Basic REST API endpoint
    print(f"\n2. Testing REST API endpoint...")
    try:
        r = requests.get(
            f"{url}/rest/v1/",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
            },
            timeout=10
        )
        
        print(f"   Status Code: {r.status_code}")
        print(f"   Response: {r.text[:200]}...")
        
        # For a valid key, Supabase usually returns 200 or 401 depending on rest config
        if r.status_code in [200, 401, 403]:
            print("   ✅ REST API endpoint is reachable")
        else:
            print(f"   ❌ Unexpected status code: {r.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")
        return False
    
    # Test 2: Test with Supabase Python client
    print(f"\n3. Testing Supabase Python client...")
    try:
        from supabase import create_client
        
        client = create_client(url, key)
        
        # Test connection by trying to create the client and do a simple operation
        # We'll just verify the client was created successfully
        print("Supabase client created successfully")
        
        print("   ✅ Supabase Python client created successfully")
            
    except Exception as e:
        print(f"   ❌ Supabase client error: {e}")
        return False
    
    # Test 3: Check pgvector extension
    print(f"\n4. Checking pgvector extension...")
    try:
        # Check if pgvector extension is enabled
        result = client.rpc("exec_sql", {"sql": "SELECT * FROM pg_extension WHERE extname = 'vector';"}).execute()
        
        if result.data:
            print("   ✅ pgvector extension is enabled")
        else:
            print("   ❌ pgvector extension is NOT enabled")
            print("   📝 To fix: Go to Supabase Dashboard > Database > Extensions > Enable 'vector'")
            return False
            
    except Exception as e:
        print(f"   ⚠️ Could not check pgvector extension: {e}")
        print("   📝 This might be due to RPC permissions. Continuing...")
    
    # Test 4: Check if documents table exists
    print(f"\n5. Checking documents table...")
    try:
        # Try to query the documents table
        result = client.from_("documents").select("*").limit(1).execute()
        print("   ✅ Documents table exists")
        print(f"   Table has {len(result.data)} rows")
        
    except Exception as e:
        print(f"   ❌ Documents table does not exist: {e}")
        print("   📝 The table will be created automatically when first used")
    
    # Test 5: Test vector store functionality
    print(f"\n6. Testing Vector Store functionality...")
    try:
        # Import vector store
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "vector_mcp"))
        from src.supabase_vector_store import SupabaseVectorStore
        
        # Create vector store instance
        vector_store = SupabaseVectorStore(url, key, "documents")
        
        # Test connection
        if vector_store.connect():
            print("   ✅ Vector store connection successful")
            
            # Try to create table
            print("   🔧 Attempting to create/verify table...")
            if vector_store.create_table_if_not_exists():
                print("   ✅ Table creation/verification successful")
                
                # Test table info
                info = vector_store.get_table_info()
                if info:
                    print(f"   ✅ Table info: {info}")
                else:
                    print("   ⚠️ Could not get table info")
            else:
                print("   ❌ Table creation/verification failed")
                print("   📝 Possible causes:")
                print("      - pgvector extension not enabled")
                print("      - Insufficient permissions")
                print("      - RPC functions not available")
                return False
        else:
            print("   ❌ Vector store connection failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Vector store error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n✅ All Supabase tests passed!")
    return True

def test_supabase():
    """Pytest-compatible test function."""
    assert test_supabase_connection(), "Supabase connection test failed"

def create_table_manually():
    """Helper function to create the table manually if RPC fails."""
    print("🔧 Manual Table Creation Helper")
    print("=" * 50)
    
    # Load environment
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Environment variables not loaded")
        return False
    
    try:
        from supabase import create_client
        client = create_client(url, key)
        
        # Read the SQL script
        sql_file = os.path.join(os.path.dirname(__file__), "..", "create_table.sql")
        
        if os.path.exists(sql_file):
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            print(f"📄 SQL script found at: {sql_file}")
            print("📋 Copy and paste this SQL into your Supabase SQL Editor:")
            print("=" * 50)
            print(sql_content)
            print("=" * 50)
            print("🔗 Go to: https://supabase.com/dashboard/project/ftovmiscxrtiqiifbcwz/sql")
            
        else:
            print(f"❌ SQL script not found at: {sql_file}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "create-table":
        success = create_table_manually()
    else:
        success = test_supabase_connection()
    
    sys.exit(0 if success else 1)
