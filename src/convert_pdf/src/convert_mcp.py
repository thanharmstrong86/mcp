from .pdf2md import convert_pdf_to_markdown, OUTPUT_DIR, UPLOAD_DIR, PROJECT_ROOT
from urllib.parse import quote
import os
import uvicorn
import argparse
from mcp.server.fastmcp import FastMCP
from starlette.staticfiles import StaticFiles
import logging
import json
from starlette.requests import Request
from starlette.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROCESSED_LIST = "/app/processed_files.json" if os.getenv("DOCKER_ENV") else os.path.join(PROJECT_ROOT, "processed_files.json")

# Initialize FastMCP server
mcp = FastMCP()

app = mcp.streamable_http_app()

# Use @mcp.tool() will cost tokens of llm model and inefficient. API for upload pdf file is more efficient.
@app.route("/mcp/upload_pdf_tool", methods=["POST"])
async def upload_pdf_tool(request: Request) -> JSONResponse:
    """Handles raw binary PDF file uploads."""
    logger.info("upload_pdf_tool endpoint called")
    
    try:
        # Parse multipart form data
        form = await request.form()
        file = form.get("file")
        delete_after = form.get("delete_after", "false").lower() == "true"
        
        if not file:
            logger.error("No file provided in upload")
            return JSONResponse({"status": "error", "message": "No file provided"}, status_code=400)
        
        file_name = file.filename
        if not file_name.lower().endswith(".pdf"):
            logger.error(f"Invalid file type for {file_name}: only PDF files are allowed")
            return JSONResponse({"status": "error", "message": "Only PDF files are allowed"}, status_code=400)
        
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logger.info(f"File '{file_name}' saved to {file_path}")
        
        # Update processed files list
        with open(PROCESSED_LIST, "r+") as f_list:
            data = json.load(f_list)
            if file_name not in data:
                data.append(file_name)
                f_list.seek(0)
                json.dump(data, f_list, indent=4)
                f_list.truncate()
        logger.info(f"'{file_name}' added to processed list")
        
        if delete_after:
            os.remove(file_path)
            logger.info(f"File '{file_name}' deleted after processing")
        
        return JSONResponse({
            "status": "uploaded",
            "filename": file_name,
            "path": file_path,
            "delete_after": delete_after
        })
    except Exception as e:
        logger.exception(f"Error during upload_pdf_tool execution for {file_name}: {str(e)}")
        return JSONResponse({"status": "error", "message": f"Failed to upload file: {str(e)}"}, status_code=500)

@mcp.tool()
def convert_pdf_to_markdown_tool(pdf_path: str) -> dict:
    """Convert a PDF file to Markdown format and save it to the specified output directory."""
    logger.info(f"convert_pdf_to_markdown_tool called with pdf_path: {pdf_path}")
    
    # Resolve relative pdf_path to UPLOAD_DIR (uploaded)
    pdf_abs_path = pdf_path
    if not os.path.isabs(pdf_path):
        logger.error("No file provided in upload")
        return {"status": "error", "message": "No file provided"}
    
    # Call convert_pdf_to_markdown from pdf2md.py
    result = convert_pdf_to_markdown(pdf_abs_path)
    if result["status"] == "success":
        markdown_path = result["markdown_path"]
        filename = os.path.basename(markdown_path)
        host = os.getenv("PUBLIC_HOST", "localhost")  # Use "localhost" for external access
        port = os.getenv("PORT", "8001")
        public_url = f"http://{host}:{port}/output/{quote(filename)}"
        result["download_url"] = public_url
    return result

def main():
    """Run the MCP PDF to Markdown conversion server."""
    parser = argparse.ArgumentParser(description="MCP PDF to Markdown Conversion Server")
    parser.add_argument("--db-path", default="/app/db/example.db", help="Path to database (not used)")
    args = parser.parse_args()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))

    logger.info(f"Starting MCP PDF to Markdown Conversion server with db-path: {args.db_path}")
    logger.info(f"HOST: {host}")
    logger.info(f"PORT: {port}")
    logger.info("MCP endpoint will be available at the server URL + /mcp")

    if host == "0.0.0.0" or os.getenv("RAILWAY_ENVIRONMENT"):
        logger.info("🚀 PRODUCTION MODE: Using FastMCP's streamable_http_app directly")
        try:
            if app is None:
                raise AttributeError("streamable_http_app() returned None")
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")
            logger.info(f"✅ SUCCESS: Got streamable_http_app from FastMCP!")
            logger.info(f"Running Uvicorn on {host}:{port}")
            uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)
        except Exception as e:
            logger.error(f"❌ Could not get streamable_http_app: {e}")
            mcp.run(transport="streamable-http")
    else:
        logger.info("🏠 LOCAL DEVELOPMENT: Using FastMCP default")
        mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()