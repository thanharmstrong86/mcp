# MCP PDF to Markdown Converter and Crawler 📄➡️📝

This project provides a robust system for converting PDF documents to Markdown format and crawling web content using a Multi-Server Communication Protocol (MCP) architecture. It comprises two main modules: `convert_pdf` for PDF upload and conversion, and `crawl_mcp` for web crawling, along with a client application that orchestrates operations using a reactive agent.

## Project Structure

The core components of this project are:
* **`convert_pdf`**: A FastMCP server (running on `http://127.0.0.1:8001`) responsible for handling PDF file uploads and converting them to Markdown. It includes two endpoints:
  - `/upload/mcp/upload_pdf_tool`: Handles PDF file uploads via multipart form data.
  - `/mcp`: Converts uploaded PDFs to Markdown using the `convert_pdf_to_markdown_tool`.
* **`crawl_mcp`**: A server module for crawling web content. For details on running this module, see [src/crawl_mcp/README.md](src/crawl_mcp/README.md).
* **`client`**: A client application that acts as an intelligent agent. It uses LangChain and LangGraph to interact with the MCP servers, upload PDFs, and trigger conversions or crawling tasks.

## Getting Started 🚀

Follow these steps to set up and run the project:

### 1. Prerequisites
* **Python 3.9+**
* **uv**: A fast Python package installer and resolver. Install it via `pip` if not already present:
    ```bash
    pip install uv
    ```

### 2. Project Setup

1. **Clone the repository (if applicable) or navigate to your project root.**
    ```bash
    cd /path/to/your/MCP
    ```

2. **Create and Sync Virtual Environment:**
   `uv` will create a `.venv` directory and install all necessary dependencies based on your `pyproject.toml`.
    ```bash
    uv sync
    ```

3. **Activate the Virtual Environment:**
   This ensures all commands run within your isolated environment.
   * **macOS/Linux:**
       ```bash
       source .venv/bin/activate
       ```
   * **Windows (Command Prompt):**
       ```bash
       .venv\Scripts\activate.bat
       ```
   * **Windows (PowerShell):**
       ```powershell
       .venv\Scripts\Activate.ps1
       ```

4. **Create `.env` file:**
   Create a file named `.env` in the project root (`MCP/`) and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY_2="YOUR_GEMINI_API_KEY_HERE"
   ```
   Replace `"YOUR_GEMINI_API_KEY_HERE"` with your actual API key.

### 3. Running the Modules

Each module has its own setup and running instructions. Refer to the module-specific READMEs for details:
- **Convert PDF Module**: See [src/convert_pdf/README.md](src/convert_pdf/README.md) for instructions on running the `convert_pdf` server.
- **Crawl MCP Module**: See [src/crawl_mcp/README.md](src/crawl_mcp/README.md) for instructions on running the `crawl_mcp` server.

### 4. Docker

The `convert_pdf` module can be run using Docker Compose with a single service:
- **Service**: `mcp-convert-server` (port 8001)
- **Functionality**: Handles PDF uploads and conversion to Markdown.

To run:
```bash
cd src/convert_pdf
docker-compose up --build -d
```

For `crawl_mcp` Docker instructions, refer to [src/crawl_mcp/README.md](src/crawl_mcp/README.md).

### 5. Testing with Client

To test the modules, use the client application located in `src/client/`. Ensure the relevant servers are running, then execute:
```bash
uv run python src/client/*
```

For example, to test the `convert_pdf` module, ensure a PDF file (e.g., `input/sample.pdf`) exists in the project’s input directory and run:
```bash
uv run python src/client/test_client.py
```

For testing `crawl_mcp`, refer to its README for specific client instructions.

### 6. Directory Structure
```
MCP/
├── src/
│   ├── convert_pdf/
│   │   ├── README.md
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── convert_mcp.py
│   │   │   ├── pdf2md.py
│   │   │   └── upload_api.py
│   │   ├── uploaded/
│   │   ├── output/
│   │   ├── processed_files.json
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   ├── crawl_mcp/
│   │   ├── README.md
│   │   └── (other module files)
│   ├── client/
│   │   ├── test_client.py
│   │   └── (other client scripts)
├── .env
└── README.md
```

### Notes
- Ensure the `.env` file is correctly configured with your API key.
- The `convert_pdf` module handles both upload and conversion on port 8001, consolidating functionality for efficiency.
- For detailed module configurations, refer to the respective READMEs.
- If encountering issues (e.g., `ClientDisconnect` or import errors), check logs with:
  ```bash
  docker-compose logs mcp-convert-server
  ```