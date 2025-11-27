FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY .env.example .env.example

# Default environment variables
ENV QDRANT_URL=http://host.containers.internal:6333
ENV COLLECTION_NAME=jarvis_hivemind
ENV EMBEDDING_PROVIDER=ollama
ENV OLLAMA_BASE_URL=http://host.containers.internal:11434
ENV OLLAMA_MODEL=nomic-embed-text
ENV OVERSEER_ENABLED=true

# Keep container running (MCP server will be invoked via exec)
CMD ["tail", "-f", "/dev/null"]
