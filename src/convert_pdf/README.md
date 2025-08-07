# Convert PDF Module 📄➡️📝

The `convert_pdf` module is a FastMCP server that handles both PDF file uploads and conversion to Markdown format, running on `http://127.0.0.1:8001`. It is part of the larger MCP PDF to Markdown Converter and Crawler project, providing a self-contained service for processing PDF documents.

## Overview

This module includes two main endpoints:
- **`/upload/mcp/upload_pdf_tool`**: Accepts multipart form data to upload PDF files to the server.
- **`/mcp`**: Converts uploaded PDFs to Markdown using the `convert_pdf_to_markdown_tool`.

The module is designed for efficiency, using direct FastAPI endpoints for uploads (avoiding the `mcp.tool()` overhead) and integrates with a client application for orchestration.

For the broader project context, see the [main project README](../../README.md).

## Module Structure

```
convert_pdf/
├── src/
│   ├── __init__.py
│   ├── convert_mcp.py
│   ├── pdf2md.py
│   └── upload_api.py
├── uploaded/
├── output/
├── processed_files.json
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

- **`src/convert_mcp.py`**: Main server script that initializes the FastMCP server and mounts the upload and conversion endpoints.
- **`src/pdf2md.py`**: Contains the logic for converting PDFs to Markdown.
- **`src/upload_api.py`**: Defines the `/upload/mcp/upload_pdf_tool` endpoint for handling PDF uploads.
- **`uploaded/`**: Directory where uploaded PDFs are stored (`/app/uploaded` in Docker).
- **`output/`**: Directory where converted Markdown files are saved (`/app/output` in Docker).
- **`processed_files.json`**: Tracks uploaded PDF filenames.

## Prerequisites

- **Python 3.9+**
- **uv**: Install via `pip` if not present:
  ```bash
  pip install uv
  ```
- **Docker and Docker Compose**: For containerized deployment.
- **Google Gemini API Key**: Required for the client application.

## Setup

1. **Navigate to the module directory**:
   ```bash
   cd /path/to/your/MCP/src/convert_pdf
   ```

2. **Sync dependencies**:
   Use `uv` to install dependencies from `pyproject.toml`:
   ```bash
   uv sync
   ```

3. **Activate the virtual environment**:
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

4. **Set up `.env`**:
   Ensure a `.env` file exists in the project root (`/path/to/your/MCP/`) with:
   ```env
   GEMINI_API_KEY_2="YOUR_GEMINI_API_KEY_HERE"
   ```
   Replace `"YOUR_GEMINI_API_KEY_HERE"` with your actual API key.

5. **Initialize `processed_files.json`**:
   Create an empty processed files list if it doesn’t exist:
   ```bash
   echo "[]" > processed_files.json
   ```

## Running the Module

### Using Docker (Recommended)

1. **Build and run the server**:
   ```bash
   docker-compose up --build -d
   ```
   This starts the `mcp-convert-server` service on port 8001, exposing:
   - `http://localhost:8001/upload/mcp/upload_pdf_tool` (upload endpoint)
   - `http://localhost:8001/mcp` (conversion endpoint)
   - `http://localhost:8001/output/` (static file server for converted Markdown files)

2. **View logs**:
   ```bash
   docker-compose logs mcp-convert-server
   ```

### Running Locally

1. **Run the server**:
   ```bash
   uv run python -m src.convert_mcp
   ```

## Testing the Module

### Manual Testing

1. **Upload a PDF**:
   Place a test PDF (e.g., `sample.pdf`) in `uploaded/` or another accessible location, then:
   ```bash
   curl -X POST http://localhost:8001/upload/mcp/upload_pdf_tool \
     -F "file=@uploaded/sample.pdf" \
     -F "delete_after=false"
   ```
   Expected response:
   ```json
   {
     "status": "uploaded",
     "filename": "sample.pdf",
     "path": "/app/uploaded/sample.pdf",
     "delete_after": false
   }
   ```

2. **Convert a PDF to Markdown**:
   Use the path returned from the upload response (e.g., `/app/uploaded/sample.pdf`):
   ```bash
   curl -X POST http://localhost:8001/mcp \
     -H "Content-Type: application/json" \
     -d '{"pdf_path": "/app/uploaded/sample.pdf"}'
   ```
   Expected response:
   ```json
   {
     "status": "success",
     "markdown_path": "/app/output/sample.md",
     "download_url": "http://localhost:8001/output/sample.md"
   }
   ```

3. **Download the Markdown**:
   Access the converted file via the `download_url` (e.g., `http://localhost:8001/output/sample.md`).

### Client Testing

Use the client application in `src/client/` to test the module:
```bash
cd /path/to/your/MCP
uv run python src/client/test_client.py
```

Ensure a PDF file (e.g., `input/sample.pdf`) exists in the project’s `input/` directory. The client will:
- Upload the PDF to `http://localhost:8001/upload/mcp/upload_pdf_tool`.
- Trigger conversion via `http://localhost:8001/mcp`.

## Troubleshooting

- **ClientDisconnect Error**:
  - Check logs for details:
    ```bash
    docker-compose logs mcp-convert-server
    ```
  - Ensure the client sends valid JSON to `/mcp` (e.g., `{"pdf_path": "/app/uploaded/sample.pdf"}`).
  - Verify the PDF file exists in `uploaded/`.

- **Import Errors** (e.g., `name 'upload_app' is not defined`):
  - Confirm `upload_api.py` defines `app = FastAPI(...)`.
  - Ensure `src/__init__.py` exists.
  - Verify `PYTHONPATH=/app/src/convert_pdf/src` in `docker-compose.yml`.

- **File Not Found**:
  - Ensure `uploaded/` and `output/` directories exist and are writable.
  - Check `processed_files.json` is initialized with `[]`.

## Notes

- The module consolidates upload and conversion on port 8001 for efficiency, aligning with the Modular MCP Architecture.
- The `/upload/mcp/upload_pdf_tool` endpoint uses FastAPI directly for performance, avoiding MCP tool overhead.
- For additional modules (e.g., `crawl_mcp`), refer to the [main project README](../../README.md).