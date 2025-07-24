from mcp.server.fastmcp import FastMCP
import os
import uvicorn
import argparse
from .pdf2md import convert_pdf_to_markdown, UPLOAD_DIR, OUTPUT_DIR

mcp = FastMCP("pdf2md_mcp_server", host="0.0.0.0", port=8001)

@mcp.tool()
def convert_pdf_to_markdown_tool(pdf_path: str) -> dict:
    """Convert a PDF file to Markdown format and save it to the specified output directory."""
    print(f"convert_pdf_to_markdown_tool called with pdf_path: {pdf_path}")
    
    # Resolve relative pdf_path to UPLOAD_DIR (uploaded)
    pdf_abs_path = pdf_path
    if not os.path.isabs(pdf_path):
        logger.error("No file provided in upload")
        return {"status": "error", "message": "No file provided"}
    
    # Call convert_pdf_to_markdown from pdf2md.py
    result = convert_pdf_to_markdown(pdf_abs_path)
    
    return result

def main():
    """Run the MCP PDF to Markdown conversion server."""
    parser = argparse.ArgumentParser(description="MCP PDF to Markdown Conversion Server")
    parser.add_argument("--db-path", default="/app/db/example.db", help="Path to database (not used)")
    args = parser.parse_args()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))

    print(f"Starting MCP PDF to Markdown Conversion server with db-path: {args.db_path}")
    print(f"HOST: {host}")
    print(f"PORT: {port}")
    print("MCP endpoint will be available at the server URL + /mcp")

    if host == "0.0.0.0" or os.getenv("RAILWAY_ENVIRONMENT"):
        print("🚀 PRODUCTION MODE: Using FastMCP's streamable_http_app directly")
        try:
            app = mcp.streamable_http_app()
            if app is None:
                raise AttributeError("streamable_http_app() returned None")
            print(f"✅ SUCCESS: Got streamable_http_app from FastMCP!")
            print(f"App type: {type(app)}")
            print(f"Running Uvicorn on {host}:{port}")
            uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)
        except Exception as e:
            print(f"❌ Could not get streamable_http_app: {e}")
            print("🔄 Falling back to FastMCP default...")
            mcp.run(transport="streamable-http")
    else:
        print("🏠 LOCAL DEVELOPMENT: Using FastMCP default")
        mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()