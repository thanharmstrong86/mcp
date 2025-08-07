# Crawl MCP Module 🕸️

The `crawl_mcp` module is a lightweight web crawling service that uses `crawl4ai` to scrape websites and save their content as Markdown files. It leverages the `mcp` library’s FastMCP to expose a `crawl_website_tool` via a JSON-RPC API over streamable HTTP transport, served by Uvicorn on `http://127.0.0.1:8002`. The module includes a client script for testing the API and supports Docker for easy deployment. It is part of the larger MCP PDF to Markdown Converter and Crawler project.

For the broader project context, see the [main project README](../../README.md).

## Overview

The `crawl_mcp` module provides a single endpoint:
- **`/mcp`**: Exposes the `crawl_website_tool`, which accepts a URL, crawls the website, and saves the content as Markdown in the `output/` directory.

The module is designed for efficiency, using the FastMCP framework for robust API handling and integration with client applications.

## Module Structure

```
crawl_mcp/
├── src/
│   ├── __init__.py
│   ├── crawl_mcp.py        # Main server script with FastMCP and crawl4ai
│   └── client.py           # Client script to test the crawl_website_tool
├── output/                 # Directory for storing crawled Markdown files
├── pyproject.toml          # Project dependencies and configuration
├── uv.lock                 # Dependency lock file managed by uv
├── Dockerfile              # Docker configuration for the server
├── docker-compose.yml      # Docker Compose configuration
└── README.md
```

- **`src/crawl_mcp.py`**: Initializes the FastMCP server and defines the `crawl_website_tool`.
- **`src/client.py`**: Tests the `crawl_website_tool` using LangChain and LangGraph.
- **`output/`**: Stores crawled Markdown files (`/app/output` in Docker).
- **`pyproject.toml`**: Specifies dependencies (`crawl4ai`, `mcp`, `uvicorn`, etc.).

## Prerequisites

- **Python 3.10+**
- **uv**: Install via `pip` if not present:
  ```bash
  pip install uv
  ```
- **Docker and Docker Compose**: For containerized deployment.
- **Google Gemini API Key**: Required for the client application.
- **Playwright**: Required by `crawl4ai` for web crawling.

## Setup

1. **Navigate to the module directory**:
   ```bash
   cd /path/to/your/MCP/src/crawl_mcp
   ```

2. **Create output directory**:
   ```bash
   mkdir -p output
   ```

3. **Sync dependencies**:
   Use `uv` to install dependencies from `pyproject.toml`:
   ```bash
   uv sync
   ```

4. **Activate the virtual environment**:
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```
   - **Windows (Command Prompt)**:
     ```bash
     .venv\Scripts\activate.bat
     ```
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```

5. **Install additional client dependencies**:
   The client script requires extra packages:
   ```bash
   uv add langchain_google_genai langchain_openai langchain_mcp_adapters langchain_community
   ```

6. **Set up Playwright for crawl4ai**:
   ```bash
   crawl4ai-setup
   ```

7. **Set up `.env`**:
   Ensure a `.env` file exists in the project root (`/path/to/your/MCP/`) with:
   ```env
   GEMINI_API_KEY_2="YOUR_GEMINI_API_KEY_HERE"
   ```
   Replace `"YOUR_GEMINI_API_KEY_HERE"` with your actual API key.

## Running the Module

### Using Docker (Recommended)

1. **Build and run the server**:
   ```bash
   docker-compose up --build -d
   ```
   This starts the `crawl4ai-mcp-server` service on port 8002, exposing:
   - `http://localhost:8002/mcp` (crawl endpoint)

2. **View logs**:
   ```bash
   docker-compose logs crawl4ai-mcp-server
   ```
   Look for: `INFO: Uvicorn running on http://0.0.0.0:8002`.

### Running Locally

1. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Run the server**:
   ```bash
   uv run python src/crawl_mcp.py
   ```

## Testing the Module

### Manual Testing

1. **Crawl a website**:
   Send a POST request to the `/mcp` endpoint with a URL to crawl:
   ```bash
   curl -X POST http://localhost:8002/mcp \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
   ```
   Expected response:
   ```json
   {
     "status": "success",
     "markdown_path": "/app/output/example_com.md",
     "download_url": "http://localhost:8002/output/example_com.md"
   }
   ```

2. **Download the Markdown**:
   Access the crawled Markdown file via the `download_url` (e.g., `http://localhost:8002/output/example_com.md`).

### Client Testing

Use the client application in `src/client/` to test the module:
```bash
cd /path/to/your/MCP
uv run python src/client/*
```

For example, to test with the provided client script:
```bash
uv run python src/client/client.py
```

The client will:
- Use LangChain and LangGraph to invoke the `crawl_website_tool`.
- Crawl a specified URL and save the output as Markdown.

Ensure the server is running before executing the client.

## Troubleshooting

- **ClientDisconnect Error**:
  - Check logs for details:
    ```bash
    docker-compose logs crawl4ai-mcp-server
    ```
  - Ensure the client sends valid JSON to `/mcp` (e.g., `{"url": "https://example.com"}`).
  - Verify network stability and server response time.

- **Playwright Issues**:
  - Ensure `crawl4ai-setup` was run successfully.
  - Check for browser installation errors in logs.

- **Dependency Errors**:
  - Verify all dependencies are installed:
    ```bash
    uv sync
    uv add langchain_google_genai langchain_openai langchain_mcp_adapters langchain_community
    ```
  - Ensure `pyproject.toml` includes:
    ```toml
    crawl4ai==0.7.0
    mcp>=0.1.43
    uvicorn>=0.30.6
    ```

- **File Not Found**:
  - Ensure the `output/` directory exists and is writable.
  - Check Docker volume mappings in `docker-compose.yml`.

## Notes

- The module runs on port 8002, distinct from the `convert_pdf` module (port 8001), ensuring modularity.
- The `crawl_website_tool` uses `crawl4ai` for efficient web scraping and integrates with FastMCP for robust API handling.
- For additional modules (e.g., `convert_pdf`), refer to the [main project README](../../README.md).