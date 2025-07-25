# Build stage: Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY src/ src/
COPY uploaded/ uploaded/
COPY processed_files.json* processed_files.json*

# Runtime stage
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

COPY --from=uv --chown=app:app /app/.venv /app/.venv
COPY --from=uv --chown=app:app /app/src /app/src
COPY --from=uv --chown=app:app /app/uploaded /app/uploaded
COPY --from=uv --chown=app:app /app/processed_files.json* /app/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

ENV HOST="0.0.0.0"
ENV PORT="8000"
ENV PORT2="8001"

EXPOSE 8000 8001

CMD ["python", "src/server/upload_mcp.py"]