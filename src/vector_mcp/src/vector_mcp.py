"""
Vector MCP Server for indexing markdown content.

This module provides MCP tools for vector indexing functionality,
allowing clients to index markdown content into Supabase vector store.
"""

import os
import hashlib
import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from pathlib import Path
from dotenv import load_dotenv

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from project root (like other modules do)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

def load_environment():
    """Load environment variables from .env file (for tool calls)."""
    # Reload from project root .env
    load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"), override=True)
    logger.debug(f"Reloaded environment from: {os.path.join(PROJECT_ROOT, '.env')}")
    return True

# Import vector indexing components from local module
from .vector_config import VectorIndexingConfig
from .embedding_service import EmbeddingService
from .supabase_vector_store import SupabaseVectorStore

# Initialize FastMCP server
mcp = FastMCP()

# Get the Starlette app for additional routes
app = mcp.streamable_http_app()

@app.route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint."""
    from starlette.responses import JSONResponse
    
    try:
        # Quick health check
        config = VectorIndexingConfig.from_environment()
        if config and config.is_valid():
            return JSONResponse({
                "status": "healthy",
                "service": "vector-mcp",
                "version": "0.1.0",
                "configuration": "valid"
            })
        else:
            return JSONResponse({
                "status": "degraded",
                "service": "vector-mcp", 
                "version": "0.1.0",
                "configuration": "invalid"
            }, status_code=503)
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "service": "vector-mcp",
            "version": "0.1.0",
            "error": str(e)
        }, status_code=503)

@mcp.tool()
def index_markdown_content(content: str, filename: str, file_path: str = "") -> Dict[str, Any]:
    """
    Index markdown content into the vector store.
    
    Args:
        content: The markdown content to index
        filename: Name of the file (for metadata)
        file_path: Path to the file (optional, for metadata)
    
    Returns:
        Dictionary with indexing results
    """
    try:
        # Ensure environment is loaded for this tool call
        load_environment()
        
        logger.info(f"Starting vector indexing for: {filename}")
        
        # Debug environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        openai_key = os.getenv('OPENAI_API_KEY')
        logger.debug(f"SUPABASE_URL: {'Set' if supabase_url else 'Missing'}")
        logger.debug(f"OPENAI_API_KEY: {'Set' if openai_key else 'Missing'}")
        
        # Validate inputs
        if not content or not content.strip():
            return {"status": "error", "message": "Content cannot be empty"}
        
        if not filename:
            return {"status": "error", "message": "Filename cannot be empty"}
        
        # Check vector indexing configuration
        config = VectorIndexingConfig.from_environment()
        if not config or not config.is_valid():
            logger.error("Configuration validation failed")
            if config:
                errors = config.get_validation_errors()
                logger.error(f"Validation errors: {errors}")
            return {
                "status": "error", 
                "message": "Vector indexing configuration not available or invalid"
            }
        
        # Initialize embedding service
        embedding_service = EmbeddingService(
            provider=config.embedding_provider,
            model=config.embedding_model
        )
        
        # Check embedding service health
        if not embedding_service.check_service_health():
            return {
                "status": "error",
                "message": "Embedding service health check failed"
            }
        
        # Initialize Supabase vector store
        vector_store = SupabaseVectorStore(
            supabase_url=config.supabase_url,
            supabase_key=config.supabase_anon_key,
            table_name=config.table_name
        )
        
        # Connect to Supabase
        if not vector_store.connect():
            return {
                "status": "error",
                "message": "Failed to connect to Supabase"
            }
        
        # Ensure table exists
        if not vector_store.create_table_if_not_exists():
            return {
                "status": "error",
                "message": "Failed to create/verify Supabase table"
            }
        
        # Generate file hash for deduplication
        file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Check if document already exists
        if vector_store.document_exists(file_hash):
            return {
                "status": "skipped",
                "message": f"Document {filename} already indexed",
                "file_hash": file_hash[:16] + "..."
            }
        
        # Chunk the content
        chunks = embedding_service.chunk_text(content)
        total_chunks = len(chunks)
        
        if not chunks:
            return {
                "status": "error",
                "message": "No content chunks generated"
            }
        
        # Process each chunk
        successful_chunks = 0
        failed_chunks = 0
        
        for chunk_index, chunk_content in enumerate(chunks):
            try:
                # Generate embedding for this chunk
                embedding = embedding_service.generate_embedding(chunk_content)
                
                # Prepare metadata for this chunk
                chunk_metadata = {
                    "filename": filename,
                    "file_path": file_path,
                    "file_hash": file_hash,
                    "chunk_index": chunk_index,
                    "total_chunks": total_chunks,
                    "content_length": len(chunk_content)
                }
                
                # Insert chunk into vector store
                if vector_store.insert_document(chunk_content, chunk_metadata, embedding):
                    successful_chunks += 1
                else:
                    failed_chunks += 1
                    
            except Exception as e:
                logger.error(f"Error processing chunk {chunk_index}: {str(e)}")
                failed_chunks += 1
                continue
        
        # Determine final status
        if successful_chunks == 0:
            return {
                "status": "error",
                "message": f"Failed to insert any chunks (0/{total_chunks})",
                "successful_chunks": successful_chunks,
                "failed_chunks": failed_chunks,
                "total_chunks": total_chunks
            }
        elif successful_chunks < total_chunks:
            return {
                "status": "partial_success",
                "message": f"Partially indexed: {successful_chunks}/{total_chunks} chunks",
                "successful_chunks": successful_chunks,
                "failed_chunks": failed_chunks,
                "total_chunks": total_chunks,
                "file_hash": file_hash[:16] + "..."
            }
        else:
            return {
                "status": "success",
                "message": f"Successfully indexed all {successful_chunks} chunks",
                "successful_chunks": successful_chunks,
                "failed_chunks": failed_chunks,
                "total_chunks": total_chunks,
                "file_hash": file_hash[:16] + "..."
            }
            
    except Exception as e:
        logger.exception(f"Unexpected error during vector indexing: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
def index_markdown_file(file_path: str) -> Dict[str, Any]:
    """
    Index a markdown file from the filesystem.
    
    Args:
        file_path: Path to the markdown file to index
    
    Returns:
        Dictionary with indexing results
    """
    try:
        # Ensure environment is loaded for this tool call
        load_environment()
        
        # Validate file path
        if not file_path:
            return {"status": "error", "message": "File path cannot be empty"}
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}
        
        # Check if it's a markdown file
        if not file_path.lower().endswith(('.md', '.markdown')):
            return {"status": "error", "message": "File must be a markdown file (.md or .markdown)"}
        
        # Read the file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"status": "error", "message": f"Failed to read file: {str(e)}"}
        
        # Get filename
        filename = os.path.basename(file_path)
        
        # Index the content
        return index_markdown_content(content, filename, file_path)
        
    except Exception as e:
        logger.exception(f"Unexpected error indexing file {file_path}: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
def get_vector_store_info() -> Dict[str, Any]:
    """
    Get information about the vector store.
    
    Returns:
        Dictionary with vector store information
    """
    try:
        # Ensure environment is loaded for this tool call
        load_environment()
        
        # Debug environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        logger.info(f"Environment check - SUPABASE_URL: {'Set' if supabase_url else 'Missing'}")
        logger.info(f"Environment check - SUPABASE_ANON_KEY: {'Set' if supabase_key else 'Missing'}")
        logger.info(f"Environment check - OPENAI_API_KEY: {'Set' if openai_key else 'Missing'}")
        
        # Check vector indexing configuration
        config = VectorIndexingConfig.from_environment()
        if not config or not config.is_valid():
            logger.error("Vector store info: Configuration validation failed")
            if config:
                errors = config.get_validation_errors()
                logger.error(f"Validation errors: {errors}")
            return {
                "status": "error",
                "message": "Vector indexing configuration not available or invalid"
            }
        
        # Initialize Supabase vector store
        vector_store = SupabaseVectorStore(
            supabase_url=config.supabase_url,
            supabase_key=config.supabase_anon_key,
            table_name=config.table_name
        )
        
        # Connect to Supabase
        if not vector_store.connect():
            return {
                "status": "error",
                "message": "Failed to connect to Supabase"
            }
        
        # Get table info
        table_info = vector_store.get_table_info()
        if not table_info:
            return {
                "status": "error",
                "message": "Failed to get table information"
            }
        
        return {
            "status": "success",
            "table_name": table_info["table_name"],
            "row_count": table_info["row_count"],
            "connected": table_info["connected"],
            "supabase_url": config.supabase_url,
            "embedding_provider": config.embedding_provider,
            "embedding_model": config.embedding_model
        }
        
    except Exception as e:
        logger.exception(f"Error getting vector store info: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

def main():
    """Run the Vector MCP server."""
    import argparse
    import uvicorn
    from dotenv import load_dotenv
    
    # Load environment variables from project root .env (same as other modules)
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        logger.info(f"✅ Loaded environment from: {env_path}")
    else:
        logger.warning(f"⚠️ No .env file found at: {env_path}")
        logger.info("Using system environment variables only")
    
    parser = argparse.ArgumentParser(description="Vector MCP Server")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"), help="Host to bind to")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8003")), help="Port to bind to")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"), help="Log level")
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Starting Vector MCP server on {args.host}:{args.port}")
    logger.info("Available tools: index_markdown_content, index_markdown_file, get_vector_store_info")
    logger.info(f"Health check available at: http://{args.host}:{args.port}/health")
    
    # Debug environment variables
    logger.info("🔍 Checking environment variables:")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    logger.info(f"   SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    logger.info(f"   SUPABASE_ANON_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
    logger.info(f"   OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Missing'}")
    
    # Check configuration at startup
    config = VectorIndexingConfig.from_environment()
    if config and config.is_valid():
        logger.info("✅ Vector indexing configuration is valid")
    else:
        logger.warning("⚠️ Vector indexing configuration is invalid - server will run in degraded mode")
        if config:
            errors = config.get_validation_errors()
            for error in errors:
                logger.warning(f"   - {error}")
    
    # Run the server
    # Always use production mode to have control over host/port
    logger.info(f"🚀 Starting server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level.lower())

if __name__ == "__main__":
    main()