#!/usr/bin/env python3
"""
Jarvis Slack Bridge - Because Slack needs some hive-mind wisdom too
Simplest possible integration: Slash commands → Jarvis MCP → Slack responses
"""

import os
import json
import asyncio
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("Error: FastAPI not installed. Run: pip install fastapi uvicorn")
    exit(1)

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("Error: Slack SDK not installed. Run: pip install slack-sdk")
    exit(1)

# Import Jarvis MCP functions
try:
    from .server import (
        generate_embedding,
        qdrant_client,
        COLLECTION_NAME,
        check_overseer,
        generate_point_id
    )
    from .resource_monitor import get_system_info, get_resource_status
    from .task_coordinator import TaskCoordinator
except ImportError:
    from server import (
        generate_embedding,
        qdrant_client,
        COLLECTION_NAME,
        check_overseer,
        generate_point_id
    )
    from resource_monitor import get_system_info, get_resource_status
    from task_coordinator import TaskCoordinator

from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, MatchAny

# Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
BRIDGE_PORT = int(os.getenv("SLACK_BRIDGE_PORT", "3000"))
DEFAULT_BRANCH = os.getenv("DEFAULT_SLACK_BRANCH", "slack")

if not SLACK_BOT_TOKEN:
    print("Warning: SLACK_BOT_TOKEN not set. Slack responses will be limited.")
    slack_client = None
else:
    slack_client = WebClient(token=SLACK_BOT_TOKEN)

app = FastAPI(title="Jarvis Slack Bridge")
task_coordinator = TaskCoordinator()


def format_slack_response(text: str, response_type: str = "ephemeral") -> dict:
    """Format response for Slack"""
    return {
        "response_type": response_type,  # "ephemeral" (only user) or "in_channel"
        "text": text
    }


def parse_jarvis_command(text: str) -> tuple[str, dict]:
    """Parse Slack command into Jarvis MCP action

    Examples:
        /jarvis search terraform patterns
        /jarvis store I learned that X works better than Y
        /jarvis stats
        /jarvis resources
    """
    text = text.strip()
    parts = text.split(maxsplit=1)

    if not parts:
        return "help", {}

    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if command in ["search", "find", "query"]:
        return "search", {"query": args, "limit": 5}

    elif command in ["store", "remember", "save"]:
        return "store", {"text": args, "branch_id": DEFAULT_BRANCH}

    elif command in ["stats", "status", "branch"]:
        return "stats", {}

    elif command in ["resources", "system", "capacity"]:
        return "resources", {}

    elif command in ["help", "?"]:
        return "help", {}

    else:
        # Default: treat entire text as search query
        return "search", {"query": text, "limit": 5}


async def execute_jarvis_action(action: str, params: dict) -> str:
    """Execute Jarvis MCP action and return formatted response"""

    if action == "help":
        return """🤖 *Jarvis Slack Commands*

*Search hive-mind:*
`/jarvis search <query>` - Search shared memory
`/jarvis <query>` - Quick search (default action)

*Store knowledge:*
`/jarvis store <text>` - Save to hive-mind memory

*System info:*
`/jarvis stats` - View hive-mind statistics
`/jarvis resources` - Check system resources

*Examples:*
• `/jarvis search terraform patterns`
• `/jarvis store Always validate Terraform before apply`
• `/jarvis authentication logic`
"""

    elif action == "search":
        query = params["query"]
        if not query:
            return "❌ Search query cannot be empty. Try: `/jarvis search <query>`"

        # Generate embedding and search
        query_embedding = generate_embedding(query)
        search_response = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=params.get("limit", 5)
        )
        results = search_response.points

        if not results:
            return f"🔍 No memories found for: `{query}`"

        output = f"🧠 *Found {len(results)} memories for:* `{query}`\n\n"
        for i, result in enumerate(results, 1):
            branch = result.payload.get('branch_id', 'unknown')
            text_preview = result.payload.get('text', '')[:200]
            timestamp = result.payload.get('timestamp', 'N/A')

            output += f"*{i}. [{result.score:.2f}]* `[{branch}]`\n"
            output += f"{text_preview}...\n"
            output += f"_Stored: {timestamp}_\n\n"

        return output

    elif action == "store":
        text = params["text"]
        if not text:
            return "❌ Cannot store empty memory. Try: `/jarvis store <text>`"

        branch_id = params.get("branch_id", DEFAULT_BRANCH)

        # Overseer check
        overseer_result = check_overseer(text, "store_memory")
        if not overseer_result["safe"]:
            return f"⚠️ *Overseer Alert:* {overseer_result['reason']}\n\nRequires approval to store."

        # Generate embedding and store
        embedding = generate_embedding(text)
        timestamp = datetime.now().isoformat()
        point_id = generate_point_id(text, branch_id)

        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "text": text,
                "branch_id": branch_id,
                "timestamp": timestamp,
                "source": "slack",
                "overseer_status": overseer_result["reason"]
            }
        )

        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=[point])

        return f"✅ *Memory stored in hive-mind*\n\nBranch: `{branch_id}`\nID: `{point_id}`"

    elif action == "stats":
        # Get branch statistics
        collection = qdrant_client.get_collection(collection_name=COLLECTION_NAME)

        scroll_result = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,
            with_vectors=False
        )

        branches = {}
        for point in scroll_result[0]:
            branch = point.payload.get("branch_id", "unknown")
            branches[branch] = branches.get(branch, 0) + 1

        output = f"📊 *Hive-Mind Statistics*\n\n"
        output += f"Total Memories: {collection.points_count}\n"
        output += f"Total Branches: {len(branches)}\n\n"
        output += "*Branch Breakdown:*\n"
        for branch, count in sorted(branches.items(), key=lambda x: x[1], reverse=True):
            output += f"• `{branch}`: {count} memories\n"

        return output

    elif action == "resources":
        info = get_system_info()
        current_agents = len([t for t in task_coordinator.tasks.values() if t.status.value == "running"])
        status = get_resource_status(current_agents)

        output = f"💻 *System Resources*\n\n"
        output += f"*CPU:* {info['cpu']['percent']}% ({info['cpu']['count']} cores)\n"
        output += f"*RAM:* {info['ram']['percent']}% ({info['ram']['available_gb']:.1f}GB available)\n\n"
        output += f"*Parallelization:*\n"
        output += f"• Zone: `{status.zone.upper()}`\n"
        output += f"• Max Agents: {status.max_agents}\n"
        output += f"• Can Spawn: {'✅' if status.can_spawn else '❌'}\n"

        return output

    else:
        return f"❌ Unknown action: `{action}`. Try `/jarvis help`"


@app.post("/slack/command")
async def handle_slack_command(request: Request):
    """Handle Slack slash command"""
    form_data = await request.form()

    # Extract Slack command data
    command = form_data.get("command", "")
    text = form_data.get("text", "")
    user_name = form_data.get("user_name", "unknown")
    channel_id = form_data.get("channel_id", "")

    print(f"📨 Slack command from @{user_name}: {command} {text}")

    # Parse and execute Jarvis action
    action, params = parse_jarvis_command(text)
    response_text = await execute_jarvis_action(action, params)

    # Return response to Slack
    return format_slack_response(response_text, response_type="ephemeral")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "jarvis-slack-bridge",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint with usage info"""
    return {
        "service": "Jarvis Slack Bridge",
        "version": "1.0.0",
        "endpoints": {
            "/slack/command": "Slack slash command webhook",
            "/health": "Health check"
        },
        "usage": "Configure Slack app to POST to /slack/command"
    }


def main():
    """Run the Slack bridge server"""
    print(f"🚀 Starting Jarvis Slack Bridge on port {BRIDGE_PORT}")
    print(f"📡 Webhook endpoint: http://localhost:{BRIDGE_PORT}/slack/command")
    print(f"🔧 Configure your Slack app to use this URL")

    if not SLACK_BOT_TOKEN:
        print("⚠️  Warning: SLACK_BOT_TOKEN not set")

    uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT)


if __name__ == "__main__":
    main()
