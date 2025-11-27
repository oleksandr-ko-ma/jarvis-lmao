#!/usr/bin/env python3
"""
Jarvis LMAO - Hive-Mind Memory System
Because we could've used N8N, but that wouldn't be fun enough
"""

import os
import json
import asyncio
import hashlib
from typing import Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import sys

load_dotenv()

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError:
    print("Error: MCP library not installed. Run: pip install mcp", file=sys.stderr)
    exit(1)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct, Filter,
        FieldCondition, MatchValue, MatchAny
    )
except ImportError:
    print("Error: qdrant-client not installed. Run: pip install qdrant-client", file=sys.stderr)
    exit(1)

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "jarvis_hivemind")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
OVERSEER_ENABLED = os.getenv("OVERSEER_ENABLED", "true").lower() == "true"

# Initialize clients
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedding_client = None
embedding_model = None

# Overseer configuration
DANGEROUS_PATTERNS = [
    "rm -rf", "sudo", "chmod 777", "curl | sh", "wget | bash",
    "DROP TABLE", "DELETE FROM", "TRUNCATE", "--force", "force push",
    "git push --force origin master", "git push --force origin main"
]

# Initialize embedding provider
if EMBEDDING_PROVIDER == "ollama":
    try:
        import ollama
        OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        embedding_model = os.getenv("OLLAMA_MODEL", "nomic-embed-text")
        embedding_client = ollama.Client(host=OLLAMA_BASE_URL)
        print(f"✓ Using Ollama embeddings: {embedding_model}", file=sys.stderr)
    except ImportError:
        print("Error: ollama library not installed. Run: pip install ollama", file=sys.stderr)
        exit(1)
elif EMBEDDING_PROVIDER == "openai":
    try:
        from openai import OpenAI
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            print("Error: OPENAI_API_KEY not set in .env", file=sys.stderr)
            exit(1)
        embedding_model = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
        embedding_client = OpenAI(api_key=OPENAI_API_KEY)
        print(f"✓ Using OpenAI embeddings: {embedding_model}", file=sys.stderr)
    except ImportError:
        print("Error: openai library not installed. Run: pip install openai", file=sys.stderr)
        exit(1)
else:
    print(f"Error: Unknown EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}", file=sys.stderr)
    exit(1)

server = Server("jarvis-lmao")

def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector for text"""
    if EMBEDDING_PROVIDER == "ollama":
        response = embedding_client.embeddings(model=embedding_model, prompt=text)
        return response['embedding']
    elif EMBEDDING_PROVIDER == "openai":
        response = embedding_client.embeddings.create(model=embedding_model, input=text)
        return response.data[0].embedding
    else:
        raise ValueError(f"Unknown embedding provider: {EMBEDDING_PROVIDER}")

def check_overseer(text: str, action_type: str = "unknown") -> dict:
    """Silent Overseer: Check if action is safe"""
    if not OVERSEER_ENABLED:
        return {"safe": True, "reason": "overseer_disabled"}

    # Check for dangerous patterns
    text_lower = text.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in text_lower:
            return {
                "safe": False,
                "reason": f"Detected dangerous pattern: {pattern}",
                "severity": "high",
                "requires_approval": True
            }

    # Check for rapid destructive actions
    # TODO: Implement rate limiting and pattern detection

    return {"safe": True, "reason": "passed_overseer_checks"}

def generate_point_id(text: str, branch_id: str, timestamp: str) -> int:
    """Generate deterministic ID from content + branch + time"""
    content = f"{text}{branch_id}{timestamp}"
    hash_obj = hashlib.sha256(content.encode())
    return int(hash_obj.hexdigest()[:16], 16)  # Use first 16 hex chars as int

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="store_memory",
            description="Store memory in hive-mind with branch context",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Content to store"},
                    "branch_id": {
                        "type": "string",
                        "description": "Thinking-branch ID (e.g., 'terraform-refactor', 'main')",
                        "default": "main"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Metadata (type, skill_name, tags, etc.)",
                        "properties": {
                            "type": {"type": "string", "description": "Memory type: skill, incident, learning, context"},
                            "skill_name": {"type": "string", "description": "Skill identifier if type=skill"},
                            "success": {"type": "boolean", "description": "Success/failure for skills"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "session_id": {"type": "string", "description": "Optional session identifier"}
                        }
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="search_memory",
            description="Search hive-mind memory with branch filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results", "default": 5},
                    "branch_filter": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by branch IDs (empty = all branches)"
                    },
                    "type_filter": {"type": "string", "description": "Filter by memory type"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="merge_branches",
            description="Merge memories from one branch into another",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_branch": {"type": "string", "description": "Source branch ID"},
                    "target_branch": {"type": "string", "description": "Target branch ID"},
                    "strategy": {
                        "type": "string",
                        "description": "Merge strategy: 'copy' (duplicate) or 'smart' (dedupe)",
                        "enum": ["copy", "smart"],
                        "default": "smart"
                    }
                },
                "required": ["source_branch", "target_branch"]
            }
        ),
        Tool(
            name="get_branch_stats",
            description="Get statistics about thinking branches",
            inputSchema={
                "type": "object",
                "properties": {
                    "branch_id": {
                        "type": "string",
                        "description": "Optional: specific branch (empty = all branches)"
                    }
                }
            }
        ),
        Tool(
            name="overseer_check",
            description="Check if an action is safe before executing",
            inputSchema={
                "type": "object",
                "properties": {
                    "action_text": {"type": "string", "description": "Action to check"},
                    "action_type": {"type": "string", "description": "Type: bash, edit, delete, etc."}
                },
                "required": ["action_text"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "store_memory":
        text = arguments["text"]
        branch_id = arguments.get("branch_id", "main")
        metadata = arguments.get("metadata", {})

        # Overseer check
        overseer_result = check_overseer(text, "store_memory")
        if not overseer_result["safe"]:
            return [TextContent(
                type="text",
                text=f"⚠️ Overseer Alert: {overseer_result['reason']}\nRequires user approval to proceed."
            )]

        # Generate embedding
        embedding = generate_embedding(text)
        timestamp = datetime.now().isoformat()

        # Create point with hive-mind metadata
        point_id = generate_point_id(text, branch_id, timestamp)
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "text": text,
                "branch_id": branch_id,
                "timestamp": timestamp,
                "overseer_status": overseer_result["reason"],
                **metadata
            }
        )

        # Store in Qdrant
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[point])

        return [TextContent(
            type="text",
            text=f"✓ Memory stored in branch '{branch_id}'\nID: {point_id}\nOverseer: {overseer_result['reason']}"
        )]

    elif name == "search_memory":
        query = arguments["query"]
        limit = arguments.get("limit", 5)
        branch_filter = arguments.get("branch_filter", [])
        type_filter = arguments.get("type_filter")

        # Generate query embedding
        query_embedding = generate_embedding(query)

        # Build filters
        filter_conditions = []
        if branch_filter:
            filter_conditions.append(
                FieldCondition(key="branch_id", match=MatchAny(any=branch_filter))
            )
        if type_filter:
            filter_conditions.append(
                FieldCondition(key="type", match=MatchValue(value=type_filter))
            )

        query_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Search
        search_response = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=limit,
            query_filter=query_filter
        )
        results = search_response.points

        if not results:
            return [TextContent(type="text", text="No memories found.")]

        output = f"🧠 Found {len(results)} memories across hive-mind:\n\n"
        for i, result in enumerate(results, 1):
            branch = result.payload.get('branch_id', 'unknown')
            memory_type = result.payload.get('type', 'unknown')
            text_preview = result.payload.get('text', '')[:150]
            timestamp = result.payload.get('timestamp', 'N/A')

            output += f"{i}. [{result.score:.3f}] [{branch}] {memory_type}\n"
            output += f"   {text_preview}...\n"
            output += f"   {timestamp}\n\n"

        return [TextContent(type="text", text=output)]

    elif name == "merge_branches":
        source_branch = arguments["source_branch"]
        target_branch = arguments["target_branch"]
        strategy = arguments.get("strategy", "smart")

        # Fetch all points from source branch
        scroll_result = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="branch_id", match=MatchValue(value=source_branch))]
            ),
            limit=1000
        )

        source_points = scroll_result[0]

        if not source_points:
            return [TextContent(type="text", text=f"No memories found in branch '{source_branch}'")]

        merged_count = 0
        for point in source_points:
            new_payload = point.payload.copy()
            new_payload["branch_id"] = target_branch
            new_payload["merged_from"] = source_branch
            new_payload["merged_at"] = datetime.now().isoformat()

            # Generate new ID for target branch
            new_id = generate_point_id(
                new_payload["text"],
                target_branch,
                new_payload["merged_at"]
            )

            new_point = PointStruct(
                id=new_id,
                vector=point.vector,
                payload=new_payload
            )

            qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[new_point])
            merged_count += 1

        return [TextContent(
            type="text",
            text=f"✓ Merged {merged_count} memories from '{source_branch}' → '{target_branch}'\nStrategy: {strategy}"
        )]

    elif name == "get_branch_stats":
        branch_id = arguments.get("branch_id")

        # Get collection info
        collection = qdrant_client.get_collection(collection_name=COLLECTION_NAME)

        if branch_id:
            # Count points in specific branch
            scroll_result = qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[FieldCondition(key="branch_id", match=MatchValue(value=branch_id))]
                ),
                limit=1,
                with_payload=False,
                with_vectors=False
            )
            count = len(scroll_result[0])

            stats = {
                "branch_id": branch_id,
                "memory_count": count,
                "collection_total": collection.points_count
            }
        else:
            # Get all branches
            # This is a simple implementation - in production, use proper aggregation
            scroll_result = qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                with_vectors=False
            )

            branches = {}
            for point in scroll_result[0]:
                branch = point.payload.get("branch_id", "unknown")
                branches[branch] = branches.get(branch, 0) + 1

            stats = {
                "total_branches": len(branches),
                "total_memories": collection.points_count,
                "branches": branches
            }

        return [TextContent(
            type="text",
            text=f"📊 Hive-Mind Statistics:\n{json.dumps(stats, indent=2)}"
        )]

    elif name == "overseer_check":
        action_text = arguments["action_text"]
        action_type = arguments.get("action_type", "unknown")

        result = check_overseer(action_text, action_type)

        if result["safe"]:
            output = f"✅ Overseer: Action approved\nReason: {result['reason']}"
        else:
            output = f"⚠️ Overseer: Action flagged\n"
            output += f"Reason: {result['reason']}\n"
            output += f"Severity: {result.get('severity', 'unknown')}\n"
            output += f"Requires approval: {result.get('requires_approval', False)}"

        return [TextContent(type="text", text=output)]

    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the MCP server"""
    try:
        # Verify Qdrant connection
        collections = qdrant_client.get_collections()
        print(f"✓ Connected to Qdrant at {QDRANT_URL}", file=sys.stderr)
        print(f"✓ Collection: {COLLECTION_NAME}", file=sys.stderr)
        print(f"✓ Overseer: {'enabled' if OVERSEER_ENABLED else 'disabled'}", file=sys.stderr)

        # Run server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        print(f"✗ Failed to start server: {e}", file=sys.stderr)
        return

if __name__ == "__main__":
    asyncio.run(main())
