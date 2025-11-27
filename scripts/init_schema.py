#!/usr/bin/env python3
"""
Initialize Qdrant collection for Jarvis Hive-Mind
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
except ImportError:
    print("Error: qdrant-client not installed. Run: pip install qdrant-client")
    exit(1)

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "jarvis_hivemind")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()

# Vector dimensions based on embedding provider
VECTOR_DIMENSIONS = {
    "ollama": 768,  # nomic-embed-text default
    "openai": 1536  # text-embedding-3-small
}

def main():
    """Initialize or recreate the Qdrant collection"""

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    print(f"🔧 Initializing Jarvis Hive-Mind schema...")
    print(f"   Qdrant URL: {QDRANT_URL}")
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Embedding: {EMBEDDING_PROVIDER}")

    # Get vector dimension
    vector_size = VECTOR_DIMENSIONS.get(EMBEDDING_PROVIDER)
    if not vector_size:
        print(f"❌ Unknown embedding provider: {EMBEDDING_PROVIDER}")
        exit(1)

    # Check if collection exists
    try:
        existing = client.get_collection(collection_name=COLLECTION_NAME)
        print(f"\n⚠️  Collection '{COLLECTION_NAME}' already exists with {existing.points_count} points")

        response = input("   Recreate? This will DELETE all data (y/N): ").strip().lower()
        if response != 'y':
            print("   Aborted. Using existing collection.")
            return

        # Delete existing collection
        client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"   ✓ Deleted existing collection")

    except Exception:
        print(f"   Collection doesn't exist, creating new...")

    # Create collection with hive-mind schema
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )

    # Create payload indexes for efficient filtering
    print("\n📋 Creating payload indexes...")

    # Index for branch filtering
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="branch_id",
        field_schema="keyword"
    )
    print("   ✓ branch_id index")

    # Index for memory type filtering
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="type",
        field_schema="keyword"
    )
    print("   ✓ type index")

    # Index for skill name filtering
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="skill_name",
        field_schema="keyword"
    )
    print("   ✓ skill_name index")

    # Index for timestamp sorting
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="timestamp",
        field_schema="datetime"
    )
    print("   ✓ timestamp index")

    print(f"\n✅ Jarvis Hive-Mind schema initialized successfully!")
    print(f"\n📊 Collection details:")

    collection = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"   Name: {collection.config.params.vectors.size}")
    print(f"   Vectors: {collection.config.params.vectors.size}D")
    print(f"   Distance: {collection.config.params.vectors.distance}")
    print(f"   Points: {collection.points_count}")

    print("\n🚀 Ready to use! Start the MCP server:")
    print(f"   python src/server.py")

if __name__ == "__main__":
    main()
