# Imagen de la API nexo-ai (workspace uv). Build desde la raíz del repo:
#   docker build -f infrastructure/docker/Dockerfile -t nexo-api .
FROM python:3.12-slim

# uv desde la imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copiar el workspace (los miembros se instalan desde su fuente)
COPY pyproject.toml uv.lock ./
COPY a2ui/ ./a2ui/
COPY backend/ ./backend/
COPY contracts/ ./contracts/
COPY integrations/ ./integrations/
COPY mcp/ ./mcp/
COPY observability/ ./observability/
COPY orchestration/ ./orchestration/
COPY rag/ ./rag/

# Instalar dependencias del workspace sin las de desarrollo
RUN uv sync --frozen --all-packages --no-dev

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"

CMD ["uv", "run", "--no-dev", "uvicorn", "nexo_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
