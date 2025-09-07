# Build stage: Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock* README.md /app/

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy application files
COPY src/ src/

# Runtime stage
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

# Copy from build stage
COPY --from=uv --chown=app:app /app/.venv /app/.venv
COPY --from=uv --chown=app:app /app/src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV HOST=0.0.0.0
ENV PORT=8003
ENV DOCKER_ENV=true

# Create directories
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the server
CMD ["python", "-m", "src.vector_mcp"]