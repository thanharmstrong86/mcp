from mcp.server.fastmcp import FastMCP
import os
import shutil
import json

# Define paths relative to the project root (one level up from src/server)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploaded")
PROCESSED_LIST = os.path.join(PROJECT_ROOT, "processed_files.json")

mcp = FastMCP("upload_mcp_server")

# Create the upload directory and processed files list if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
if not os.path.exists(PROCESSED_LIST):
    with open(PROCESSED_LIST, "w") as f:
        json.dump([], f)

@mcp.tool()
def upload_pdf(file_path: str, delete_after: bool = False) -> dict:
    print(f"upload_pdf called with file_path: {file_path}, delete_after: {delete_after}")
    if not file_path.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are allowed")
    file_name = os.path.basename(file_path)
    dst_path = os.path.join(UPLOAD_DIR, file_name)
    shutil.copyfile(file_path, dst_path)

    if delete_after:
        os.remove(file_path)

    with open(PROCESSED_LIST, "r+") as f:
        data = json.load(f)
        if file_name not in data:
            data.append(file_name)
            f.seek(0)
            json.dump(data, f)
            f.truncate()

    return {"status": "uploaded", "filename": file_name}

@mcp.tool()
def file_status(filename: str) -> dict:
    print(f"file_status called with filename: {filename}")
    exists = os.path.exists(os.path.join(UPLOAD_DIR, filename))
    return {"exists": exists}

@mcp.tool()
def list_processed_files() -> list:
    print("list_processed_files called")
    with open(PROCESSED_LIST, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")