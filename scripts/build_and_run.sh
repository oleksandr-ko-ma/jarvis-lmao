#!/usr/bin/env bash
# Build and run Jarvis LMAO in Podman

set -e

echo "🤖 Building Jarvis LMAO container..."

# Build image
podman build -t jarvis-lmao:latest -f Containerfile .

echo "✓ Image built"

# Check if container exists and remove it
if podman ps -a | grep -q jarvis-lmao; then
    echo "Removing existing container..."
    podman rm -f jarvis-lmao
fi

# Run container
echo "🚀 Starting Jarvis LMAO..."
podman run -d \
    --name jarvis-lmao \
    -p 8001:8001 \
    --network host \
    --add-host=host.containers.internal:host-gateway \
    jarvis-lmao:latest

echo "✓ Container started"
echo ""
echo "📊 Status:"
podman ps | grep jarvis-lmao

echo ""
echo "📝 Logs:"
echo "   podman logs -f jarvis-lmao"
echo ""
echo "🔧 Test connection:"
echo "   podman exec jarvis-lmao python -c 'from qdrant_client import QdrantClient; print(QdrantClient(url=\"http://host.containers.internal:6333\").get_collections())'"
