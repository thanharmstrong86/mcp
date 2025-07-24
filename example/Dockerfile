# Build stage: Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

# Set working directory
WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy from cache instead of linking for mounted volumes
ENV UV_LINK_MODE=copy

# Install project dependencies using uv.lock
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Add project source code and install it
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Runtime stage: Use a minimal Python image
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Copy virtual environment from build stage
COPY --from=uv --chown=app:app /app/.venv /app/.venv

# Add virtual environment executables to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set default host and port (can be overridden)
ENV HOST="0.0.0.0"
ENV PORT="8000"

# Expose port 8000
EXPOSE 8000

# Run the mcp-server script
ENTRYPOINT ["mcp-server"]