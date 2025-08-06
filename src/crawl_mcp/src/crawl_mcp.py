import os
import logging
from datetime import datetime
from urllib.parse import quote
from mcp.server.fastmcp import FastMCP
from crawl4ai import AsyncWebCrawler
from starlette.staticfiles import StaticFiles
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP()
OUTPUT_DIR = "output"

@mcp.tool()
async def crawl_website_tool(url: str) -> dict:
    """Crawl a website and save its content as Markdown."""
    logger.info(f"crawl_website_tool called with url: {url}")
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            markdown_content = result.markdown
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crawl_{timestamp}.md"
            output_path = os.path.join(OUTPUT_DIR, filename)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            host = os.getenv("PUBLIC_HOST", "localhost")
            port = os.getenv("PORT", "8002")
            public_url = f"http://{host}:{port}/output/{quote(filename)}"
            logger.info(f"Generated Markdown file at {output_path}, download URL: {public_url}")
            return {
                "status": "success",
                "output_file": output_path,
                "markdown": markdown_content,
                "download_url": public_url
            }
    except Exception as e:
        logger.error(f"Error crawling {url}: {str(e)}")
        return {"status": "error", "message": str(e)}

def main():
    app = mcp.streamable_http_app()
    if app is None:
        raise AttributeError("streamable_http_app() returned None")
    """Run the MCP website crawling server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8002"))

    logger.info(f"Starting MCP Website Crawling server on {host}:{port}")
    logger.info("MCP endpoint will be available at the server URL + /mcp")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")
    uvicorn.run(app, host=host, port=port, log_level="info", loop="asyncio")

if __name__ == "__main__":
    main()