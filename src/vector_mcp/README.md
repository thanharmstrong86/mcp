# Vector MCP Server

A Model Context Protocol (MCP) server for vector indexing functionality. This server provides tools to index markdown content into a Supabase vector store using OpenAI embeddings.

## Features

- **index_markdown_content**: Index markdown content directly
- **index_markdown_file**: Index a markdown file from the filesystem  
- **get_vector_store_info**: Get information about the vector store

## Prerequisites

1. **Environment Variables**: Set up the following in your `.env` file:
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   OPENAI_API_KEY=your_openai_api_key
   ```

2. **Supabase Setup**: 
   - Enable the `pgvector` extension in your Supabase project
   - The server will automatically create the required table structure

## Usage

### Quick Start

1. **Setup environment:**
   ```bash
   cd src/vector_mcp
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies:**
   ```bash
   make install
   # or: uv sync
   ```

3. **Start the server:**
   ```bash
   make run
   # or: uv run python -m src.vector_mcp.src.vector_mcp
   ```

### Development

```bash
# Install with dev dependencies
make dev

# Run tests
make test

# Format code
make format

# Run with debug logging
make run-dev
```

### Docker Deployment

```bash
# Build and run with Docker Compose
make docker-build
make docker-run

# With nginx reverse proxy
make docker-run-nginx

# View logs
make docker-logs

# Stop containers
make docker-stop
```

### Testing the Server

Run the test client to verify functionality:

```bash
# From the project root
uv run python src/client/client_vector_test.py
```

Check server health:
```bash
make health
# or: curl http://localhost:8002/health
```

### MCP Tools

#### 1. index_markdown_content
Index markdown content directly.

**Parameters:**
- `content` (str): The markdown content to index
- `filename` (str): Name of the file (for metadata)
- `file_path` (str, optional): Path to the file (for metadata)

**Returns:**
```json
{
  "status": "success|error|partial_success|skipped",
  "message": "Description of the result",
  "successful_chunks": 5,
  "failed_chunks": 0,
  "total_chunks": 5,
  "file_hash": "abc123..."
}
```

#### 2. index_markdown_file
Index a markdown file from the filesystem.

**Parameters:**
- `file_path` (str): Path to the markdown file to index

**Returns:** Same format as `index_markdown_content`

#### 3. get_vector_store_info
Get information about the vector store.

**Returns:**
```json
{
  "status": "success|error",
  "table_name": "documents",
  "row_count": 42,
  "connected": true,
  "supabase_url": "https://xxx.supabase.co",
  "embedding_provider": "openai",
  "embedding_model": "text-embedding-3-small"
}
```

## Error Handling

The server includes comprehensive error handling:
- Configuration validation
- Retry logic for transient failures
- Graceful degradation when services are unavailable
- Detailed error messages and logging

## Architecture

The vector MCP server uses the same robust components as the convert_pdf module:
- `VectorIndexingConfig`: Configuration management with validation
- `EmbeddingService`: OpenAI embedding generation with retry logic
- `SupabaseVectorStore`: Supabase integration with connection management

## Integration

This server can be integrated with any MCP-compatible client or used alongside other MCP servers in a multi-server setup.