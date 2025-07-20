from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MyServer",host="0.0.0.0",port=8001)

@mcp.tool()
async def greet(name: str) -> str:
    """Greet the user."""
    return f"Hello, {name}! How are you?"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")