FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY pokedex_mcp/ ./pokedex_mcp/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["pokedex-mcp-server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]