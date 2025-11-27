# Jarvis + Slack: Stealth Mode Setup

Sneak Jarvis into Slack using **your personal credentials** (no bot approval needed!)

## Why Stealth Mode?

Corporate Slack workspaces often block bot installations. This approach:
- ✅ Uses YOUR browser tokens (no admin approval)
- ✅ No scopes/permissions needed in workspace
- ✅ Appears as YOU in Slack (not a bot)
- ✅ Read channels, send messages, search history
- ✅ Works with Jarvis hive-mind memory

## Architecture

```
You in Slack
    ↑↓
Browser Tokens (xoxc + xoxd)
    ↑↓
Slack MCP Server (korotovsky/slack-mcp-server)
    ↑↓
Claude Code MCP Client
    ↑↓
Jarvis Hive-Mind Memory
```

## Step 1: Extract Your Slack Tokens

### Get XOXC Token

1. **Open Slack in browser** and log in to your workspace
2. **Open Developer Tools**:
   - Chrome: `⌘⌥I` (Mac) or `Ctrl+Shift+I` (Windows/Linux)
   - Firefox: `⌘⌥K` (Mac) or `Ctrl+Shift+K` (Windows/Linux)
3. **Go to Console tab**
4. **Type** `allow pasting` and press Enter (security bypass)
5. **Paste and run**:
   ```javascript
   JSON.parse(localStorage.localConfig_v2).teams[document.location.pathname.match(/^\/client\/([A-Z0-9]+)/)[1]].token
   ```
6. **Copy the token** (starts with `xoxc-`)

### Get XOXD Token

1. **Still in DevTools**, go to **Application** tab
2. **Left sidebar** → Cookies → Select your Slack domain
3. **Find cookie named** `d`
4. **Double-click the Value** column
5. **Copy the value** (`Ctrl+C` / `⌘C`)

**Save both tokens securely!**

## Step 2: Install Slack MCP Server

### Option A: NPX (Easiest)

The MCP server is a Go binary wrapped by NPX for easy distribution.

**No installation needed** - will run on-demand via npx.

### Option B: Docker (Isolated)

```bash
# Pull the Docker image
docker pull ghcr.io/korotovsky/slack-mcp-server:latest

# Run with environment variables
docker run -d \
  --name slack-mcp \
  -e SLACK_MCP_XOXC_TOKEN=xoxc-your-token \
  -e SLACK_MCP_XOXD_TOKEN=your-d-cookie \
  -e SLACK_MCP_PORT=13080 \
  ghcr.io/korotovsky/slack-mcp-server:latest
```

Or use docker-compose (create `docker-compose.slack.yml`):

```yaml
version: '3.8'

services:
  slack-mcp:
    image: ghcr.io/korotovsky/slack-mcp-server:latest
    container_name: slack-mcp
    env_file:
      - .env.slack
    ports:
      - "13080:13080"
    restart: unless-stopped
```

Create `.env.slack`:
```bash
SLACK_MCP_XOXC_TOKEN=xoxc-your-token-here
SLACK_MCP_XOXD_TOKEN=your-d-cookie-here
SLACK_MCP_PORT=13080
# Optional: Enable posting messages
SLACK_MCP_ADD_MESSAGE_TOOL=true
```

Start:
```bash
docker-compose -f docker-compose.slack.yml up -d
```

## Step 3: Configure Claude Code

Add to your `~/.config/ClaudeCode/mcp_config.json`:

### For NPX Method:

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": [
        "-y",
        "slack-mcp-server"
      ],
      "env": {
        "SLACK_MCP_XOXC_TOKEN": "xoxc-your-token-here",
        "SLACK_MCP_XOXD_TOKEN": "your-d-cookie-here",
        "SLACK_MCP_ADD_MESSAGE_TOOL": "true"
      }
    }
  }
}
```

### For Docker Method:

**Note**: Docker runs as a separate process. You'll need to expose it via SSE transport.

Use the NPX method instead for simpler Claude Code integration.

## Step 4: Restart Claude Code

```bash
# Restart Claude Code to load the new MCP server
# Or use the command palette: "Reload Window"
```

## Step 5: Verify Connection

In Claude Code, Jarvis should now have access to these tools:

- `mcp__slack__conversations_history` - Read channel messages
- `mcp__slack__conversations_replies` - Read thread replies
- `mcp__slack__conversations_search_messages` - Search across Slack
- `mcp__slack__conversations_add_message` - Send messages (if enabled)
- `mcp__slack__channels_list` - List all channels

Try:
```
Hey Jarvis, list my Slack channels
```

## Usage Examples

### Search Slack for Context

```
Jarvis, search Slack for "deployment pipeline" discussions from last week
```

Jarvis will:
1. Use `conversations_search_messages` to find relevant threads
2. Store important findings in hive-mind memory
3. Summarize key insights for you

### Monitor Specific Channels

```
Jarvis, check #engineering for any mentions of "production issues" today
```

Jarvis will:
1. Use `conversations_history` to fetch recent messages
2. Filter for keywords
3. Alert you to important threads

### Post Messages (if enabled)

```
Jarvis, send a message to #team-updates: "Deployment completed successfully"
```

**Warning**: This appears as YOU in Slack, not a bot!

### Cross-Reference with Hive-Mind

```
Jarvis, search Slack for terraform discussions and compare with what we have in hive-mind memory
```

Jarvis will:
1. Search Slack history
2. Search hive-mind memory
3. Find gaps or new learnings
4. Store missing context in hive-mind

## Jarvis Integration Patterns

### Pattern 1: Slack → Hive-Mind Learning

```
User: "Jarvis, review today's #engineering channel and store any important decisions"

Jarvis:
1. Fetches conversations_history for #engineering
2. Identifies key decisions (via LLM analysis)
3. Stores in hive-mind with branch_id="slack"
4. Returns summary of stored learnings
```

### Pattern 2: Hive-Mind → Slack Sharing

```
User: "Jarvis, find our terraform validation pattern and share it in #devops"

Jarvis:
1. Searches hive-mind for terraform patterns
2. Formats for Slack
3. Posts to #devops channel (as you)
```

### Pattern 3: Parallel Context Gathering

```
User: "Jarvis, gather context on the API refactor from both Slack and our memories"

Jarvis:
1. Spawns parallel tasks:
   - Search Slack for "API refactor" discussions
   - Search hive-mind for stored API knowledge
2. Aggregates findings
3. Stores new learnings from Slack
4. Returns comprehensive context
```

## Security Considerations

### Token Lifespan

- Browser tokens (`xoxc`/`xoxd`) expire when you log out
- If tokens stop working, re-extract from browser
- Consider automation with token refresh scripts

### What Jarvis Can See

- **Everything YOU can see** in Slack
- Public channels you're in
- Private channels you're in
- DMs you have access to

### Message Posting Safety

**Recommended settings**:
```bash
# Disable posting by default (read-only)
SLACK_MCP_ADD_MESSAGE_TOOL=false

# Or whitelist specific channels
SLACK_MCP_ADD_MESSAGE_TOOL=true
SLACK_MCP_ALLOWED_CHANNELS="#sandbox,#test-channel"
```

**Always verify** before letting Jarvis post. Remember: it posts as YOU!

## Troubleshooting

### "Authentication failed" error

- Re-extract tokens (they may have expired)
- Make sure you copied the FULL token (xoxc tokens are long!)
- Check you're logged into the correct workspace

### "Cannot find channel" error

- Verify you're a member of the channel
- Try using channel ID instead of name
- List channels with `channels_list` to see available options

### "Rate limited" error

- Slack limits API calls
- Jarvis will automatically retry
- Consider adding delays between bulk operations

### Tokens stopped working after logout

- Browser tokens are session-based
- Re-extract tokens after logging back in
- Consider using xoxp OAuth token instead (doesn't expire on logout)

## Alternative: OAuth Mode (More Stable)

If browser tokens are too fragile, use OAuth instead:

1. Create Slack app at https://api.slack.com/apps
2. Add OAuth scopes (user scopes, not bot scopes):
   - `channels:history`, `channels:read`
   - `groups:history`, `groups:read`
   - `im:history`, `im:read`
   - `mpim:history`, `mpim:read`
   - `chat:write`, `search:read`
   - `users:read`
3. Install to workspace (may need approval)
4. Copy **User OAuth Token** (starts with `xoxp-`)
5. Use in config:
   ```json
   "env": {
     "SLACK_MCP_XOXP_TOKEN": "xoxp-your-token-here"
   }
   ```

**Trade-off**: OAuth is more stable but may require approval.

## Next Steps

Once Slack MCP is working:

1. **Test basic queries**: List channels, search messages
2. **Integrate with Jarvis memory**: Store Slack learnings in hive-mind
3. **Create skills**: Common Slack operations as reusable skills
4. **Automate monitoring**: Regular channel checks for keywords
5. **Build workflows**: Slack → Analysis → Hive-Mind → Action

---

**You're now a stealth operator!** Jarvis can tap into Slack under your credentials. 🕵️

Questions? Check the upstream repo: https://github.com/korotovsky/slack-mcp-server
