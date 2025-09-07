# Design Document

## Overview

This design implements optional Supabase PostgreSQL vector database indexing for the convert PDF module. The solution extends the existing LangGraph workflow with a new conditional node that handles vector indexing when Supabase configuration is available. The design maintains backward compatibility and ensures the main PDF conversion workflow remains unaffected by indexing operations.

## Architecture

### High-Level Architecture

The vector indexing functionality integrates into the existing LangGraph workflow as an optional final step:

```
PDF Input → Check PDF Type → Extract Text → Process to Markdown → Save Markdown → [Vector Indexing] → End
```

The vector indexing step is conditional and only executes when:
1. Supabase configuration is present and valid
2. The previous steps completed successfully
3. An embedding service is available

### Component Integration

The solution adds minimal components to the existing system:
- **SupabaseVectorStore**: Handles Supabase connection and vector operations
- **EmbeddingService**: Generates embeddings for document content
- **VectorIndexingNode**: LangGraph node that orchestrates the indexing process
- **Configuration Manager**: Validates and manages Supabase settings

## Components and Interfaces

### SupabaseVectorStore

```python
class SupabaseVectorStore:
    def __init__(self, supabase_url: str, supabase_key: str, table_name: str = "documents")
    def connect(self) -> bool
    def create_table_if_not_exists(self) -> bool
    def insert_document(self, content: str, metadata: dict, embedding: list) -> bool
    def check_connection(self) -> bool
```

**Responsibilities:**
- Manage Supabase client connection
- Create and manage the documents table with vector column
- Insert document records with embeddings
- Handle connection validation and error recovery

### EmbeddingService

```python
class EmbeddingService:
    def __init__(self, provider: str = "openai", model: str = "text-embedding-3-small")
    def generate_embedding(self, text: str) -> list[float]
    def chunk_text(self, text: str, max_tokens: int = 8000) -> list[str]
    def is_available(self) -> bool
```

**Responsibilities:**
- Generate vector embeddings for text content
- Handle text chunking for large documents
- Support multiple embedding providers (OpenAI, local models)
- Validate embedding service availability

### Configuration Manager

```python
class VectorIndexingConfig:
    @classmethod
    def from_environment(cls) -> Optional['VectorIndexingConfig']
    def is_valid(self) -> bool
    
    supabase_url: str
    supabase_anon_key: str
    table_name: str
    embedding_provider: str
    embedding_model: str
```

**Responsibilities:**
- Load and validate environment configuration
- Provide default values for optional settings
- Determine if vector indexing should be enabled

## Data Models

### Supabase Documents Table Schema

```sql
CREATE TABLE IF NOT EXISTS documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    filename VARCHAR NOT NULL,
    content TEXT NOT NULL,
    file_path VARCHAR NOT NULL,
    file_hash VARCHAR NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    embedding VECTOR(1536)  -- Dimension depends on embedding model
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create index for filename lookups
CREATE INDEX IF NOT EXISTS documents_filename_idx ON documents (filename);
```

### Document Metadata Structure

```python
DocumentMetadata = {
    "filename": str,           # Original PDF filename
    "file_path": str,         # Full path to converted markdown
    "file_hash": str,         # SHA-256 hash of original PDF
    "conversion_timestamp": str,  # ISO timestamp of conversion
    "chunk_index": int,       # Chunk number for large documents
    "total_chunks": int,      # Total number of chunks
    "content_length": int,    # Length of this chunk's content
}
```

## Error Handling

### Error Categories and Responses

1. **Configuration Errors**
   - Missing environment variables → Disable indexing, log warning
   - Invalid Supabase credentials → Disable indexing, log error
   - Missing embedding API key → Disable indexing, log warning

2. **Connection Errors**
   - Supabase connection failure → Log error, continue without indexing
   - Embedding service unavailable → Log error, continue without indexing
   - Network timeouts → Retry once, then continue without indexing

3. **Data Processing Errors**
   - Embedding generation failure → Log error for specific chunk, continue
   - Database insertion failure → Log error, continue without indexing
   - Text chunking errors → Log warning, attempt with full text

### Error Recovery Strategy

- All vector indexing errors are non-fatal to the main workflow
- Failed indexing attempts are logged with appropriate detail levels
- The system gracefully degrades to the original workflow when indexing fails
- Retry logic is implemented for transient network issues

## Testing Strategy

### Unit Tests

1. **SupabaseVectorStore Tests**
   - Connection establishment and validation
   - Table creation and schema verification
   - Document insertion with various content types
   - Error handling for connection failures

2. **EmbeddingService Tests**
   - Embedding generation for different text lengths
   - Text chunking with various document sizes
   - Provider availability checking
   - Error handling for API failures

3. **Configuration Tests**
   - Environment variable loading and validation
   - Default value assignment
   - Invalid configuration handling

### Integration Tests

1. **End-to-End Workflow Tests**
   - PDF conversion with successful vector indexing
   - PDF conversion with indexing disabled (no config)
   - PDF conversion with indexing failure (graceful degradation)

2. **Database Integration Tests**
   - Supabase table creation and management
   - Document insertion and retrieval
   - Vector similarity search functionality

### Mock Testing Strategy

- Mock Supabase client for unit tests
- Mock embedding API responses
- Test configuration scenarios without external dependencies
- Simulate network failures and recovery

## Implementation Considerations

### Performance Optimization

- **Asynchronous Operations**: Use async/await for Supabase and embedding API calls
- **Batch Processing**: Process multiple chunks in parallel when possible
- **Connection Pooling**: Reuse Supabase connections across requests
- **Caching**: Cache embedding service availability checks

### Security Considerations

- **API Key Management**: Store sensitive keys in environment variables only
- **Input Validation**: Sanitize all user inputs before database operations
- **SQL Injection Prevention**: Use parameterized queries for all database operations
- **Rate Limiting**: Respect embedding API rate limits

### Scalability Considerations

- **Chunking Strategy**: Implement intelligent text chunking for large documents
- **Database Indexing**: Optimize vector similarity search performance
- **Memory Management**: Process large documents in streaming fashion
- **Error Isolation**: Ensure single document failures don't affect batch processing

### Backward Compatibility

- **Zero Configuration Impact**: System works identically when Supabase config is absent
- **API Compatibility**: No changes to existing API endpoints or responses
- **Dependency Management**: New dependencies are optional and don't affect core functionality
- **Graceful Degradation**: System continues normal operation when vector indexing fails