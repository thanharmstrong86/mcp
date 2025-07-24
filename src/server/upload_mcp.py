import os
import json
import argparse
import uvicorn
import logging
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = "/app/uploaded" if os.getenv("DOCKER_ENV") else os.path.join(PROJECT_ROOT, "uploaded")
PROCESSED_LIST = "/app/processed_files.json" if os.getenv("DOCKER_ENV") else os.path.join(PROJECT_ROOT, "processed_files.json")

mcp = FastMCP("upload_mcp_server")
app = mcp.streamable_http_app()  # Get Starlette app from FastMCP

# Create the upload directory and processed files list if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
if not os.path.exists(PROCESSED_LIST):
    with open(PROCESSED_LIST, "w") as f:
        json.dump([], f)

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
def file_status(filename: str) -> dict:
    """Checks the existence of an uploaded file."""
    logger.info(f"file_status called with filename: {filename}")
    exists = os.path.exists(os.path.join(UPLOAD_DIR, filename))
    return {"exists": exists}

@mcp.tool()
def list_processed_files() -> list:
    """Lists all files that have been processed and recorded."""
    logger.info("list_processed_files called")
    with open(PROCESSED_LIST, "r") as f:
        return json.load(f)

def main():
    """Run the MCP PDF upload server."""
    parser = argparse.ArgumentParser(description="MCP PDF Upload Server")
    parser.add_argument("--db-path", default="/app/db/example.db", help="Path to database (not used)")
    args = parser.parse_args()
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting MCP PDF Upload server on {host}:{port}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"Processed files list: {PROCESSED_LIST}")
    logger.info("MCP endpoint will be available at the server URL + /mcp")
    
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)

if __name__ == "__main__":
    main()