# Jarvis Slack Integration

Get Jarvis talking in Slack with a simple slash command!

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name it `Jarvis LMAO` and select your workspace

### 3. Configure Slack App

#### Add Slash Command
1. In your app settings, go to **"Slash Commands"**
2. Click **"Create New Command"**
3. Configure:
   - **Command**: `/jarvis`
   - **Request URL**: `https://your-domain.com/slack/command`
     - For local testing with ngrok: `https://abc123.ngrok.io/slack/command`
   - **Short Description**: `Talk to Jarvis hive-mind`
   - **Usage Hint**: `search <query> | store <text> | stats | help`
4. Save

#### Get Bot Token
1. Go to **"OAuth & Permissions"**
2. Add these scopes under **"Bot Token Scopes"**:
   - `chat:write` - Send messages
   - `commands` - Receive slash commands
3. Click **"Install to Workspace"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

#### Get Signing Secret
1. Go to **"Basic Information"**
2. Copy **"Signing Secret"**

### 4. Configure Environment

Add to your `.env` file:

```bash
# Slack credentials
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# Bridge server port
SLACK_BRIDGE_PORT=3000

# Default branch for Slack memories
DEFAULT_SLACK_BRANCH=slack
```

### 5. Run the Bridge

```bash
# Start Jarvis Slack bridge
python3 src/slack_bridge.py
```

The bridge will run on `http://localhost:3000`

### 6. Expose to Internet (for Slack)

**For local development, use ngrok:**

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 3000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and update your Slack app's slash command **Request URL** to:

```
https://abc123.ngrok.io/slack/command
```

**For production, deploy to:**
- Heroku
- Railway
- Render
- Your own server with HTTPS

## Usage

Once configured, use Jarvis in any Slack channel:

### Search Hive-Mind

```
/jarvis search terraform patterns
/jarvis authentication logic
/jarvis deployment scripts
```

Quick search (no keyword needed):
```
/jarvis how do we handle errors?
```

### Store Knowledge

```
/jarvis store Always validate Terraform before apply
/jarvis remember We use JWT for authentication
```

### System Info

```
/jarvis stats          # Hive-mind statistics
/jarvis resources      # System resource usage
/jarvis help          # Show all commands
```

## Architecture

```
Slack User
    ↓
/jarvis <command>
    ↓
Slack API → POST to Bridge Server
    ↓
FastAPI Bridge (slack_bridge.py)
    ↓
Jarvis MCP Functions (server.py)
    ↓
Qdrant Vector DB
    ↓
Response → Slack User
```

## Features

✅ **Search memories** - Query shared hive-mind knowledge
✅ **Store memories** - Save learnings from Slack
✅ **View stats** - See branch statistics
✅ **Resource monitoring** - Check system capacity
✅ **Silent Overseer** - Blocks dangerous patterns
✅ **Branch isolation** - Slack gets its own branch (default: `slack`)

## Security

- **Ephemeral responses** - Only visible to command user
- **Overseer protection** - Blocks dangerous patterns before storing
- **Signing verification** - Validates Slack requests (TODO)
- **Branch isolation** - Slack memories separate from main

## Troubleshooting

### "This didn't work" error in Slack

- Check bridge is running: `curl http://localhost:3000/health`
- Check ngrok is forwarding: Visit ngrok URL in browser
- Verify Request URL in Slack app settings matches ngrok URL

### "Connection refused"

- Ensure Jarvis is running: `podman ps | grep jarvis`
- Ensure Qdrant is running: `podman ps | grep qdrant`
- Check bridge logs for errors

### Responses not appearing

- Check SLACK_BOT_TOKEN is set correctly
- Verify bot scopes include `chat:write`
- Check Slack app is installed to workspace

## Future Enhancements

- [ ] Interactive buttons for memory actions
- [ ] Threaded conversations with Jarvis
- [ ] Parallel task spawning from Slack
- [ ] Skill execution via Slack
- [ ] Request verification with signing secret
- [ ] Rate limiting per user
- [ ] Rich formatting with Slack blocks

## Containerization

To run in Docker/Podman alongside Jarvis:

```dockerfile
# Add to Containerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
CMD ["python3", "src/slack_bridge.py"]
```

Build and run:
```bash
podman build -t jarvis-slack-bridge .
podman run -p 3000:3000 --env-file .env jarvis-slack-bridge
```

---

**Now your whole team can tap into the hive-mind!** 🧠⚡
