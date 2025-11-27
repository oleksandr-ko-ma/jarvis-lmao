# Jarvis LMAO - Quick Start

*"The 5-minute setup because we're too lazy for N8N"*

## TL;DR

```bash
# 1. Build and run
cd ~/Documents/GitHub/jarvis-lmao
bash scripts/build_and_run.sh

# 2. Initialize schema
podman exec jarvis-lmao python scripts/init_schema.py

# 3. Verify it works
podman logs jarvis-lmao

# 4. Done! The global CLAUDE.md rules are already in place.
# All future Claude Code sessions will use the hive-mind.
```

## What Just Happened?

1. **Jarvis MCP Server** is running in Podman (port 8001)
2. **Global Rules** added to `~/.claude/CLAUDE.md`
3. **Skilltree** initialized at `~/.claude/skills/skilltree.md`
4. **Qdrant Schema** created for hive-mind memory

## Next Time You Use Claude Code

The system is already active! Every session will:

1. **Check skilltree** before implementing patterns
2. **Search memory** before solving problems
3. **Store learnings** automatically
4. **Use branch context** to track parallel work

## MCP Tools Available

Once Claude Code connects:

- `store_memory` - Save knowledge to hive-mind
- `search_memory` - Find prior solutions
- `merge_branches` - Sync parallel thinking-branches
- `get_branch_stats` - View memory stats
- `overseer_check` - Validate actions for safety

## Manual MCP Configuration (Optional)

If tools aren't auto-detected, configure manually:

```bash
# Check current MCP config
claude mcp list

# Add jarvis-lmao if needed
# See docs/SETUP.md for full config
```

## Test the System

In your next Claude Code session:

```
"Store a memory that says: Jarvis LMAO is operational"
"Search for: Jarvis operational"
```

You should see the memory stored and retrieved.

## Philosophy

- **Hive-Mind**: All sessions share one memory
- **Branch Context**: Track parallel conversations
- **Skilltree**: Don't repeat patterns, script them
- **Silent Overseer**: Safety layer prevents disasters
- **Token Economy**: Upfront MCP calls save thousands later

## Files You Care About

- `~/.claude/CLAUDE.md` - Global rules (already updated)
- `~/.claude/skills/skilltree.md` - Skill registry
- `~/.claude/skills/*.sh|py` - Executable skills

## When Something Breaks

```bash
# Check container status
podman ps | grep jarvis-lmao

# View logs
podman logs -f jarvis-lmao

# Restart container
podman restart jarvis-lmao

# Rebuild from scratch
bash scripts/build_and_run.sh
```

## The N8N Question

*"Why didn't we just use N8N?"*

Because:
- We wanted semantic vector search (N8N would need this anyway)
- Hive-mind architecture requires custom logic
- Silent Overseer needs agent-level integration
- We enjoy pain (apparently)

But hey, at least we learned something! 🤷‍♂️

---

**You're done.** Go use Claude Code. The hive-mind is watching. 👁️
