FROM python:3.12-slim

ARG PORT=8002

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock /app/

# Install dependencies and run crawl4ai-setup
RUN uv sync --frozen --no-dev && \
    .venv/bin/crawl4ai-setup

# Copy application files
COPY src/ src/
COPY output/ output/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PLAYWRIGHT_BROWSERS_PATH="/root/.cache/ms-playwright"
ENV FASTMCP_HOST="0.0.0.0"
ENV FASTMCP_PORT="8002"
ENV PUBLIC_HOST="localhost"
ENV PORT="8002"
EXPOSE ${PORT}

# Run the MCP server
CMD ["python", "src/crawl_mcp.py"]