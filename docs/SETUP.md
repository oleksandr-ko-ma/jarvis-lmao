# Jarvis LMAO Setup Guide

## Prerequisites

1. **Qdrant** running in Podman:
   ```bash
   podman ps | grep qdrant
   ```

2. **Ollama** (or OpenAI API key):
   ```bash
   ollama list | grep nomic-embed-text
   # Or: export OPENAI_API_KEY=sk-...
   ```

## Option 1: Run in Podman (Recommended)

### Build and Run
```bash
cd ~/Documents/GitHub/jarvis-lmao
bash scripts/build_and_run.sh
```

### Initialize Schema
```bash
podman exec jarvis-lmao python scripts/init_schema.py
```

### Check Logs
```bash
podman logs -f jarvis-lmao
```

### Test Connection
```bash
# Test Qdrant connectivity
podman exec jarvis-lmao python -c "
from qdrant_client import QdrantClient
client = QdrantClient(url='http://host.containers.internal:6333')
print('Collections:', client.get_collections())
"
```

## Option 2: Run Locally

### Setup
```bash
cd ~/Documents/GitHub/jarvis-lmao
bash scripts/setup.sh
```

### Configure
```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

### Initialize Schema
```bash
source venv/bin/activate
python scripts/init_schema.py
```

### Run Server
```bash
python src/server.py
```

## Configure Claude Code

### Add MCP Server

Create or edit `~/.config/claude/mcp_settings.json`:

```json
{
  "mcpServers": {
    "jarvis-lmao": {
      "command": "podman",
      "args": [
        "exec",
        "-i",
        "jarvis-lmao",
        "python",
        "src/server.py"
      ],
      "env": {}
    }
  }
}
```

**Or** if running locally:

```json
{
  "mcpServers": {
    "jarvis-lmao": {
      "command": "/Users/YOUR_USERNAME/Documents/GitHub/jarvis-lmao/venv/bin/python",
      "args": [
        "/Users/YOUR_USERNAME/Documents/GitHub/jarvis-lmao/src/server.py"
      ],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "COLLECTION_NAME": "jarvis_hivemind",
        "EMBEDDING_PROVIDER": "ollama",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "nomic-embed-text",
        "OVERSEER_ENABLED": "true"
      }
    }
  }
}
```

### Restart Claude Code

The MCP server tools should now be available:
- `mcp__jarvis-lmao__store_memory`
- `mcp__jarvis-lmao__search_memory`
- `mcp__jarvis-lmao__merge_branches`
- `mcp__jarvis-lmao__get_branch_stats`
- `mcp__jarvis-lmao__overseer_check`

## Verify Setup

In Claude Code, test the integration:

```
Store a test memory:
- Text: "Jarvis LMAO is working!"
- Branch: "main"
- Type: "test"

Then search for it:
- Query: "jarvis working"
```

You should see the stored memory returned.

## Troubleshooting

### MCP Tools Not Available

1. Check MCP server is running:
   ```bash
   podman ps | grep jarvis-lmao
   ```

2. Check logs:
   ```bash
   podman logs jarvis-lmao
   ```

3. Verify Qdrant connection:
   ```bash
   podman exec jarvis-lmao python -c "from qdrant_client import QdrantClient; print(QdrantClient(url='http://host.containers.internal:6333').get_collections())"
   ```

### Qdrant Connection Failed

1. Verify Qdrant is running:
   ```bash
   podman ps | grep qdrant
   ```

2. Check network connectivity:
   ```bash
   podman exec jarvis-lmao curl http://host.containers.internal:6333/collections
   ```

### Embedding Errors

**Ollama**:
```bash
ollama list | grep nomic-embed-text
# If missing: ollama pull nomic-embed-text
```

**OpenAI**:
- Check OPENAI_API_KEY is set in .env
- Verify API key is valid

## Next Steps

1. ✅ Setup complete
2. 📖 Read the global rules in `~/.claude/CLAUDE.md`
3. 🎯 Check `~/.claude/skills/skilltree.md` for available skills
4. 🧠 Start using memory in your conversations!

The hive-mind is now active. All Claude Code sessions share the same memory pool.
