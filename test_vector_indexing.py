#!/usr/bin/env python3
"""
Test client for vector indexing functionality.
Reads a markdown file and indexes it directly.
"""

import os
import hashlib
import logging
from dotenv import load_dotenv
from src.convert_pdf.src.vector_config import VectorIndexingConfig
from src.convert_pdf.src.embedding_service import EmbeddingService
from src.convert_pdf.src.supabase_vector_store import SupabaseVectorStore

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_vector_indexing():
    """Test vector indexing with a markdown file."""
    
    # Check for markdown files in output directory
    output_dir = "output"
    if not os.path.exists(output_dir):
        print(f"Output directory {output_dir} not found")
        return
    
    # Find markdown files
    md_files = [f for f in os.listdir(output_dir) if f.endswith('.md')]
    if not md_files:
        print(f"No markdown files found in {output_dir}")
        return
    
    # Use the first markdown file
    md_file = md_files[0]
    md_path = os.path.join(output_dir, md_file)
    
    print(f"Testing vector indexing with: {md_path}")
    
    # Read the markdown content
    with open(md_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    print(f"Markdown content length: {len(markdown_content)} characters")
    
    # Check vector indexing configuration
    config = VectorIndexingConfig.from_environment()
    if not config or not config.is_valid():
        print("Vector indexing configuration not available or invalid")
        print("Please set SUPABASE_URL, SUPABASE_ANON_KEY, and OPENAI_API_KEY environment variables")
        return
    
    print("Vector indexing configuration is valid")
    
    try:
        # Initialize embedding service
        print("Initializing embedding service...")
        embedding_service = EmbeddingService(
            provider=config.embedding_provider,
            model=config.embedding_model
        )
        
        # Check embedding service health
        if not embedding_service.check_service_health():
            print("Embedding service health check failed")
            return
        
        print("Embedding service is healthy")
        
        # Initialize Supabase vector store
        print("Initializing Supabase vector store...")
        vector_store = SupabaseVectorStore(
            supabase_url=config.supabase_url,
            supabase_key=config.supabase_anon_key,
            table_name=config.table_name
        )
        
        # Connect to Supabase
        if not vector_store.connect():
            print("Failed to connect to Supabase")
            return
        
        print("Connected to Supabase successfully")
        
        # Ensure table exists
        if not vector_store.create_table_if_not_exists():
            print("Failed to create/verify Supabase table")
            return
        
        print("Supabase table verified")
        
        # Generate file hash for deduplication
        file_hash = hashlib.sha256(markdown_content.encode('utf-8')).hexdigest()
        print(f"File hash: {file_hash[:16]}...")
        
        # Check if document already exists
        if vector_store.document_exists(file_hash):
            print("Document already indexed, skipping")
            return
        
        # Chunk the markdown content
        print("Chunking markdown content...")
        chunks = embedding_service.chunk_text(markdown_content)
        total_chunks = len(chunks)
        
        if not chunks:
            print("No content chunks generated")
            return
        
        print(f"Generated {total_chunks} chunks")
        
        # Process each chunk
        successful_chunks = 0
        failed_chunks = 0
        
        for chunk_index, chunk_content in enumerate(chunks):
            print(f"Processing chunk {chunk_index + 1}/{total_chunks}...")
            
            try:
                # Generate embedding for this chunk
                embedding = embedding_service.generate_embedding(chunk_content)
                print(f"Generated embedding of dimension {len(embedding)}")
                
                # Prepare metadata for this chunk
                chunk_metadata = {
                    "filename": md_file,
                    "file_path": md_path,
                    "file_hash": file_hash,
                    "chunk_index": chunk_index,
                    "total_chunks": total_chunks,
                    "content_length": len(chunk_content)
                }
                
                # Insert chunk into vector store
                if vector_store.insert_document(chunk_content, chunk_metadata, embedding):
                    successful_chunks += 1
                    print(f"Successfully indexed chunk {chunk_index + 1}")
                else:
                    print(f"Failed to insert chunk {chunk_index + 1}")
                    failed_chunks += 1
                    
            except Exception as e:
                print(f"Error processing chunk {chunk_index + 1}: {str(e)}")
                failed_chunks += 1
                continue
        
        # Print final results
        print(f"\nIndexing completed:")
        print(f"  Successful chunks: {successful_chunks}")
        print(f"  Failed chunks: {failed_chunks}")
        print(f"  Total chunks: {total_chunks}")
        
        if successful_chunks > 0:
            success_rate = (successful_chunks / total_chunks) * 100
            print(f"  Success rate: {success_rate:.1f}%")
            
            # Get table info
            table_info = vector_store.get_table_info()
            if table_info:
                print(f"  Total documents in database: {table_info['row_count']}")
        
        print("Vector indexing test completed!")
        
    except Exception as e:
        print(f"Error during vector indexing test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vector_indexing()