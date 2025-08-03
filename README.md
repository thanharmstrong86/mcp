# MCP PDF to Markdown Converter 📄➡️📝

This project provides a robust system to convert PDF documents into Markdown format using a Multi-Server Communication Protocol (MCP) architecture. It comprises two FastMCP servers for uploading and converting files, and a client application that orchestrates these operations using a reactive agent.

## Project Structure

The core components of this project are:
* **`upload_mcp`**: A FastMCP server (running on `http://127.0.0.1:8000`) responsible for handling PDF file uploads.
* **`convert_mcp`**: A FastMCP server (running on `http://127.0.0.1:8001`) responsible for converting uploaded PDFs to Markdown.
* **`client_convert`**: A client application that acts as an intelligent agent. It uses Langchain and LangGraph to interact with the MCP servers, upload PDFs, and trigger their conversion.

## Getting Started 🚀

Follow these steps to set up and run the project:

### 1. Prerequisites
* **Python 3.9+**
* **uv**: A fast Python package installer and resolver. If you don't have `uv` installed, you can get it via `pip`:
    ```bash
    pip install uv
    ```

### 2. Project Setup

1.  **Clone the repository (if applicable) or navigate to your project root.**
    ```bash
    cd /path/to/your/MCP/project
    ```

2.  **Create and Sync Virtual Environment:**
    `uv` will create a `.venv` directory and install all necessary dependencies based on your `pyproject.toml`.
    ```bash
    uv sync
    ```

3.  **Activate the Virtual Environment:**
    This step is crucial to ensure all commands run within your isolated environment.
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

4.  **Create `.env` file:**
    Create a file named `.env` in the project root (`MCP/`) and add your Google Gemini API key:
    ```env
    GEMINI_API_KEY_2="YOUR_GEMINI_API_KEY_HERE"
    ```
    Replace `"YOUR_GEMINI_API_KEY_HERE"` with your actual API key.

### 3. Running the Servers and Client

You need to run the two MCP servers in separate terminal windows/tabs, and then run the client in a third.

**Terminal 1: Run `upload_mcp` Server**

Navigate to your project root (`/path/to/your/MCP/`) and run:
```bash
uv run python -m src.server.upload.mcp

### 4. Docker

2 services :
- mcp-upload-server : port 8000
- mcp-convert-server : port 8001

docker-compose up --build -d

### 5. Client

uv run python -m src.client.client_upload
uv run python -m src.client.client_convert