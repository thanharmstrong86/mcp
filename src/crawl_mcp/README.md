Crawl MCP Project
Overview
The crawl_mcp project is a lightweight web crawling service that uses crawl4ai to scrape websites and save their content as Markdown files. It leverages the mcp library’s FastMCP to expose a crawl_website_tool via a JSON-RPC API over streamable-http transport, served by uvicorn. The project includes a client script for testing the API and supports Docker for easy deployment.
Prerequisites

Python: >=3.10
Docker: For containerized deployment
uv: For dependency management
Dependencies (specified in pyproject.toml):
crawl4ai==0.7.0
mcp>=0.1.43
uvicorn>=0.30.6



Project Structure
crawl_mcp/
├── output/                  # Directory for storing crawled Markdown files
├── src/
│   ├── crawl_mcp.py        # Main server script with FastMCP and crawl4ai
│   └── client.py           # Client script to test the crawl_website_tool
├── pyproject.toml          # Project dependencies and configuration
├── uv.lock                 # Dependency lock file managed by uv
├── Dockerfile              # Docker configuration for the server
└── docker-compose.yml      # Docker Compose configuration

Setup

Clone the Repository (if applicable):
git clone <repository-url>
cd crawl_mcp


Create Output Directory:
mkdir -p output


Install Dependencies:Use uv to install dependencies:
uv sync

This creates a virtual environment (.venv) and installs crawl4ai, mcp, and uvicorn.

Set Up Playwright (required by crawl4ai):
source .venv/bin/activate
crawl4ai-setup



Running the Server
Option 1: Docker (Recommended)

Build the Docker Image:
docker-compose build


Start the Server:
docker-compose up -d


Check Logs:
docker-compose logs crawl4ai-mcp-server

Look for: INFO: Uvicorn running on http://0.0.0.0:8002.


Option 2: Local Python

Activate Virtual Environment:
source .venv/bin/activate
( please add these lib to run : uv add langchain_google_genai ( langchain_openai), langchain_mcp_adapters, langchain_community )

Run the Server:
uv run python src/crawl_mcp.py

Testing the Server
The server exposes a crawl_website_tool at http://localhost:8002/mcp, which crawls a specified URL and saves the content as Markdown in the