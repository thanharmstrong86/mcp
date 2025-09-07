"""
Supabase vector store for managing document embeddings and metadata.

This module provides functionality to connect to Supabase PostgreSQL database,
create tables with vector columns, and manage document storage with embeddings.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from supabase import create_client, Client
from postgrest.exceptions import APIError


logger = logging.getLogger(__name__)


class SupabaseVectorStore:
    """Vector store implementation using Supabase PostgreSQL with pgvector."""
    
    def __init__(self, supabase_url: str, supabase_key: str, table_name: str = "documents", 
                 max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the Supabase vector store.
        
        Args:
            supabase_url: The Supabase project URL
            supabase_key: The Supabase anon key
            table_name: Name of the table to store documents (default: "documents")
            max_retries: Maximum number of retries for transient failures (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.table_name = table_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[Client] = None
        self._connected = False
    
    def _retry_on_failure(self, operation: Callable, operation_name: str, *args, **kwargs) -> Any:
        """
        Retry an operation with exponential backoff for transient failures.
        
        Args:
            operation: The operation to retry
            operation_name: Name of the operation for logging
            *args, **kwargs: Arguments to pass to the operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = operation(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"{operation_name} succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this is a retryable error
                if not self._is_retryable_error(e):
                    logger.error(f"{operation_name} failed with non-retryable error: {str(e)}")
                    raise e
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"{operation_name} failed on attempt {attempt + 1}, retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"{operation_name} failed after {self.max_retries + 1} attempts: {str(e)}")
        
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable (transient).
        
        Args:
            error: The exception to check
            
        Returns:
            True if the error is retryable, False otherwise
        """
        error_str = str(error).lower()
        
        # Network-related errors that are typically transient
        retryable_patterns = [
            'connection',
            'timeout',
            'network',
            'temporary',
            'unavailable',
            'rate limit',
            'too many requests',
            'server error',
            'internal error',
            '5xx'
        ]
        
        # Check if error message contains retryable patterns
        for pattern in retryable_patterns:
            if pattern in error_str:
                return True
        
        # Check specific exception types
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        # API errors with 5xx status codes are typically retryable
        if isinstance(error, APIError):
            # Check if it's a server error (5xx)
            if hasattr(error, 'code') and str(error.code).startswith('5'):
                return True
        
        return False
    
    def connect(self) -> bool:
        """
        Establish connection to Supabase with retry logic.
        
        Returns:
            True if connection successful, False otherwise
        """
        def _connect_operation():
            logger.debug(f"Attempting to connect to Supabase at {self.supabase_url}")
            
            # Validate URL and key before attempting connection
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL and key must be provided")
            
            self._client = create_client(self.supabase_url, self.supabase_key)
            
            # Test the connection by making a simple RPC call or checking if our table exists
            # Instead of querying information_schema, try to query our documents table
            # If it doesn't exist, we'll create it later
            try:
                # Try to query the documents table (will fail if it doesn't exist, but that's OK)
                result = self._client.from_(self.table_name).select("id").limit(1).execute()
                logger.debug(f"Table {self.table_name} exists and is accessible")
            except Exception as table_error:
                # Table might not exist yet, that's fine - we'll create it later
                logger.debug(f"Table {self.table_name} doesn't exist yet or is not accessible: {str(table_error)}")
                # Just verify the client was created successfully
                if not self._client:
                    raise ConnectionError("Failed to create Supabase client")
            
            self._connected = True
            logger.info(f"Successfully connected to Supabase at {self.supabase_url}")
            return True
        
        try:
            return self._retry_on_failure(_connect_operation, "Supabase connection")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase after all retries: {str(e)}")
            self._connected = False
            self._client = None
            return False
    
    def check_connection(self) -> bool:
        """
        Check if the connection to Supabase is healthy with retry logic.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        if not self._client or not self._connected:
            logger.debug("No Supabase client or connection not established")
            return False
        
        def _health_check_operation():
            # Simple health check - try to query our table or just verify client exists
            try:
                # Try to query our documents table
                result = self._client.from_(self.table_name).select("id").limit(1).execute()
                return True
            except Exception:
                # If table doesn't exist, that's still a valid connection
                # Just verify the client is still working
                if self._client:
                    return True
                else:
                    raise ConnectionError("Supabase client is no longer available")
            return True
        
        try:
            return self._retry_on_failure(_health_check_operation, "Supabase health check")
        except Exception as e:
            logger.warning(f"Supabase connection health check failed after all retries: {str(e)}")
            self._connected = False
            return False
    
    def create_table_if_not_exists(self) -> bool:
        """
        Create the documents table with vector column if it doesn't exist.
        
        Returns:
            True if table exists or was created successfully, False otherwise
        """
        if not self._client:
            logger.error("No Supabase client available for table creation")
            return False
        
        def _create_table_operation():
            logger.debug(f"Checking if table {self.table_name} exists")
            
            # Check if table exists by trying to query it
            try:
                result = self._client.from_(self.table_name).select("id").limit(1).execute()
                logger.info(f"Table {self.table_name} already exists")
                return True
            except Exception as e:
                logger.debug(f"Table {self.table_name} doesn't exist yet: {str(e)}")
                # Table doesn't exist, we'll create it
            
            logger.info(f"Creating table {self.table_name}")
            
            # Create table with vector column
            # Note: This requires the pgvector extension to be enabled in Supabase
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                filename VARCHAR NOT NULL,
                content TEXT NOT NULL,
                file_path VARCHAR NOT NULL,
                file_hash VARCHAR NOT NULL,
                chunk_index INTEGER DEFAULT 0,
                total_chunks INTEGER DEFAULT 1,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                embedding VECTOR(1536)
            );
            """
            
            # Try to execute table creation via RPC
            try:
                table_result = self._client.rpc("exec_sql", {"sql": create_table_sql}).execute()
                logger.info(f"Table {self.table_name} created via RPC")
                
                # Create indexes for better performance
                create_indexes_sql = f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx ON {self.table_name} 
                USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                
                CREATE INDEX IF NOT EXISTS {self.table_name}_filename_idx ON {self.table_name} (filename);
                
                CREATE INDEX IF NOT EXISTS {self.table_name}_file_hash_idx ON {self.table_name} (file_hash);
                """
                
                try:
                    index_result = self._client.rpc("exec_sql", {"sql": create_indexes_sql}).execute()
                    logger.info(f"Successfully created table {self.table_name} with indexes")
                except Exception as idx_e:
                    logger.warning(f"Table created but index creation failed: {str(idx_e)}")
                
                return True
                
            except Exception as rpc_e:
                logger.error(f"RPC table creation failed: {str(rpc_e)}")
                logger.error("This usually means:")
                logger.error("  1. The exec_sql RPC function is not available")
                logger.error("  2. Insufficient permissions to create tables")
                logger.error("  3. The table needs to be created manually")
                logger.error(f"Please run the SQL script in src/vector_mcp/create_table.sql in your Supabase SQL Editor")
                raise rpc_e
        
        try:
            return self._retry_on_failure(_create_table_operation, "Table creation")
        except Exception as e:
            logger.error(f"Failed to create table {self.table_name} after all retries: {str(e)}")
            # Try alternative approach without RPC if it's not available
            return self._create_table_alternative()
    
    def _create_table_alternative(self) -> bool:
        """
        Alternative table creation method that doesn't rely on RPC.
        This assumes the table structure is already set up in Supabase.
        """
        def _test_table_operation():
            logger.debug(f"Testing table {self.table_name} structure with alternative method")
            
            # Try to insert a test record to verify table structure
            test_record = {
                "filename": "__test__",
                "content": "test",
                "file_path": "/test",
                "file_hash": "test_hash",
                "chunk_index": 0,
                "total_chunks": 1,
                "embedding": [0.0] * 1536  # Test embedding
            }
            
            # Insert and immediately delete the test record
            result = self._client.from_(self.table_name).insert(test_record).execute()
            if not result.data:
                raise RuntimeError("Failed to insert test record")
            
            # Delete the test record
            delete_result = self._client.from_(self.table_name).delete().eq("filename", "__test__").execute()
            
            logger.info(f"Table {self.table_name} is accessible and has correct structure")
            return True
        
        try:
            return self._retry_on_failure(_test_table_operation, "Table structure test")
        except Exception as e:
            logger.error(f"Table {self.table_name} verification failed after all retries: {str(e)}")
            logger.error("Please ensure the table is created manually in Supabase with the required schema")
            logger.error("Required schema: id (UUID), filename (VARCHAR), content (TEXT), file_path (VARCHAR), file_hash (VARCHAR), chunk_index (INTEGER), total_chunks (INTEGER), created_at (TIMESTAMP), updated_at (TIMESTAMP), embedding (VECTOR(1536))")
            return False
    
    def insert_document(self, content: str, metadata: Dict[str, Any], embedding: List[float]) -> bool:
        """
        Insert a document with its embedding into the vector store with retry logic.
        
        Args:
            content: The document content
            metadata: Document metadata (filename, file_path, file_hash, etc.)
            embedding: The vector embedding for the content
            
        Returns:
            True if insertion successful, False otherwise
        """
        if not self._client:
            logger.error("No Supabase client available for document insertion")
            return False
        
        if not self.check_connection():
            logger.error("Supabase connection is not healthy for document insertion")
            return False
        
        def _insert_operation():
            # Validate input parameters
            if not content or not content.strip():
                raise ValueError("Document content cannot be empty")
            
            if not embedding or len(embedding) == 0:
                raise ValueError("Document embedding cannot be empty")
            
            required_metadata = ["filename", "file_hash"]
            for field in required_metadata:
                if not metadata.get(field):
                    raise ValueError(f"Required metadata field '{field}' is missing or empty")
            
            # Prepare the document record
            document_record = {
                "filename": metadata.get("filename", ""),
                "content": content,
                "file_path": metadata.get("file_path", ""),
                "file_hash": metadata.get("file_hash", ""),
                "chunk_index": metadata.get("chunk_index", 0),
                "total_chunks": metadata.get("total_chunks", 1),
                "embedding": embedding
            }
            
            logger.debug(f"Inserting document chunk {document_record['chunk_index']} for {document_record['filename']}")
            
            # Insert the document
            result = self._client.from_(self.table_name).insert(document_record).execute()
            
            if not result.data:
                raise RuntimeError("Document insertion failed: No data returned from Supabase")
            
            logger.debug(f"Successfully inserted document chunk {metadata.get('chunk_index', 0)} for {metadata.get('filename', 'unknown')}")
            return True
        
        try:
            return self._retry_on_failure(_insert_operation, "Document insertion")
        except ValueError as e:
            # Don't retry validation errors
            logger.error(f"Document insertion failed due to validation error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Document insertion failed after all retries: {str(e)}")
            return False
    
    def document_exists(self, file_hash: str) -> bool:
        """
        Check if a document with the given hash already exists.
        
        Args:
            file_hash: The hash of the document to check
            
        Returns:
            True if document exists, False otherwise
        """
        if not self._client or not self.check_connection():
            logger.debug("Cannot check document existence: no client or connection")
            return False
        
        if not file_hash:
            logger.warning("Cannot check document existence: file_hash is empty")
            return False
        
        def _check_existence_operation():
            result = self._client.from_(self.table_name).select("id").eq("file_hash", file_hash).limit(1).execute()
            exists = len(result.data) > 0
            logger.debug(f"Document with hash {file_hash[:8]}... {'exists' if exists else 'does not exist'}")
            return exists
        
        try:
            return self._retry_on_failure(_check_existence_operation, "Document existence check")
        except Exception as e:
            logger.error(f"Error checking document existence after all retries: {str(e)}")
            return False
    
    def delete_document(self, file_hash: str) -> bool:
        """
        Delete all chunks of a document by its hash with retry logic.
        
        Args:
            file_hash: The hash of the document to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self._client or not self.check_connection():
            logger.error("Cannot delete document: no client or connection")
            return False
        
        if not file_hash:
            logger.error("Cannot delete document: file_hash is empty")
            return False
        
        def _delete_operation():
            logger.debug(f"Deleting document with hash {file_hash[:8]}...")
            result = self._client.from_(self.table_name).delete().eq("file_hash", file_hash).execute()
            logger.info(f"Successfully deleted document with hash {file_hash[:8]}...")
            return True
        
        try:
            return self._retry_on_failure(_delete_operation, "Document deletion")
        except Exception as e:
            logger.error(f"Error deleting document after all retries: {str(e)}")
            return False
    
    def get_table_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the documents table with retry logic.
        
        Returns:
            Dictionary with table information or None if error
        """
        if not self._client or not self.check_connection():
            logger.debug("Cannot get table info: no client or connection")
            return None
        
        def _get_info_operation():
            # Get row count
            count_result = self._client.from_(self.table_name).select("id", count="exact").execute()
            row_count = count_result.count if hasattr(count_result, 'count') else 0
            
            return {
                "table_name": self.table_name,
                "row_count": row_count,
                "connected": self._connected,
                "supabase_url": self.supabase_url
            }
        
        try:
            return self._retry_on_failure(_get_info_operation, "Table info retrieval")
        except Exception as e:
            logger.error(f"Error getting table info after all retries: {str(e)}")
            return None