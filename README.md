# Jarvis LMAO 🤖

*"Yes, we could've just used N8N... but where's the fun in that?"*

## What is this?

A hive-mind memory system for Claude Code that makes AI agents actually remember stuff across conversations and parallel thinking branches. Built because apparently we enjoy overengineering things instead of using workflow automation tools.

## Architecture

```
Claude Code (Multiple Agents/Branches)
    ↓
Silent Overseer (Safety Layer)
    ↓
Jarvis MCP Server (Hive-Mind Coordinator)
    ↓
Qdrant Vector DB (Shared Memory)
```

### Components

1. **Hive-Mind Memory System**: Vector memory with branch/session tracking
2. **Thinking-Branches**: Parallel conversation contexts (like Mixture-of-Experts)
3. **Silent Overseer**: Background safety monitor that prevents stupid decisions
4. **Skilltree Integration**: Links to executable skills at `~/.claude/skills/`

## Features

### Hive-Mind Architecture
- **Multi-Branch Context**: Each agent/conversation has a thinking-branch ID
- **Shared Memory Pool**: All branches can access and contribute to shared knowledge
- **Branch Merging**: Sync insights across parallel conversation threads
- **Session Tracking**: Know which agent learned what, when

### Silent Overseer
- Monitors all agent actions silently
- Detects dangerous/idiotic patterns
- Asks for user approval when needed
- Learns from approved/rejected actions

### Skilltree Integration
- Auto-logs skill usage to memory
- Tracks success/failure patterns
- Suggests skills based on context
- Updates learning log automatically

## Setup

### 1. Prerequisites
```bash
# Qdrant running in Podman
podman ps | grep qdrant

# Ollama for embeddings (or OpenAI)
ollama list | grep nomic-embed-text
```

### 2. Install
```bash
cd ~/Documents/GitHub/jarvis-lmao
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/init_schema.py
```

### 3. Configure Claude Code
```bash
# Add to Claude Code MCP config
claude mcp add jarvis-lmao
```

### 4. Set Global Rules
The system auto-updates `~/.claude/CLAUDE.md` with Jarvis rules on first run.

## Usage

### Store Memory with Branch Context
```json
{
  "tool": "store_memory",
  "args": {
    "text": "Learned that Terraform requires explicit depends_on for PD schedules",
    "branch_id": "terraform-refactor-2024",
    "metadata": {
      "type": "skill",
      "skill_name": "terraform_dependency_pattern",
      "success": true
    }
  }
}
```

### Search Across All Branches
```json
{
  "tool": "search_memory",
  "args": {
    "query": "PagerDuty schedule dependencies",
    "include_branches": ["all"]
  }
}
```

### Merge Branch Knowledge
```json
{
  "tool": "merge_branches",
  "args": {
    "source_branch": "experiment-a",
    "target_branch": "main",
    "strategy": "smart"
  }
}
```

## Why Not N8N?

Good question. We ask ourselves this daily.

Benefits of this overengineered solution:
- ✅ Deep integration with Claude Code workflow
- ✅ Vector semantic search (N8N would need external service anyway)
- ✅ Branch-aware memory (N8N doesn't understand hive-mind)
- ✅ Silent Overseer safety layer (N8N can't read agent intent)
- ✅ We learned a lot (expensive way to learn)

What N8N would've given us:
- ✅ Visual workflow builder
- ✅ No code maintenance
- ✅ Pre-built integrations
- ✅ More time for actual work

*Choose your poison* ☠️

## License

MIT - Do whatever you want with this. If you're smart, you'll use N8N instead.
