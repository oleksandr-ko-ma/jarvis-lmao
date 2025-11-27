#!/bin/bash
# Setup Slack MCP Server for Claude Code
# This script helps configure the slack-mcp-server for stealth mode access

set -e

echo "🕵️  Jarvis Slack Stealth Mode Setup"
echo "===================================="
echo ""

# Check if Claude Code config exists
CLAUDE_CONFIG_DIR="$HOME/.config/ClaudeCode"
MCP_CONFIG="$CLAUDE_CONFIG_DIR/mcp_config.json"

if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    echo "Creating Claude Code config directory..."
    mkdir -p "$CLAUDE_CONFIG_DIR"
fi

# Check for tokens
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "Please create .env file with your Slack tokens:"
    echo ""
    cat .env.slack.example
    echo ""
    echo "To extract tokens, follow: docs/SLACK_STEALTH_MODE.md"
    echo "Or use quick guide: scripts/extract_slack_tokens.md"
    exit 1
fi

# Load environment variables
source .env

# Verify tokens are set
if [ -z "$SLACK_MCP_XOXC_TOKEN" ] || [ -z "$SLACK_MCP_XOXD_TOKEN" ]; then
    if [ -z "$SLACK_MCP_XOXP_TOKEN" ]; then
        echo "❌ No Slack tokens found in .env!"
        echo ""
        echo "You need either:"
        echo "  - SLACK_MCP_XOXC_TOKEN + SLACK_MCP_XOXD_TOKEN (stealth mode)"
        echo "  - SLACK_MCP_XOXP_TOKEN (OAuth mode)"
        echo ""
        echo "See: docs/SLACK_STEALTH_MODE.md"
        exit 1
    fi
fi

echo "✓ Tokens found in .env"
echo ""

# Generate MCP config
echo "Generating MCP configuration..."

# Check if mcp_config.json exists
if [ -f "$MCP_CONFIG" ]; then
    echo "⚠️  $MCP_CONFIG already exists"
    echo ""
    read -p "Do you want to merge Slack config? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping MCP config update"
        echo "Manually add Slack server to: $MCP_CONFIG"
        exit 0
    fi
fi

# Build the Slack MCP server config
SLACK_CONFIG=$(cat <<EOF
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": [
        "-y",
        "slack-mcp-server"
      ],
      "env": {
EOF
)

# Add tokens based on what's available
if [ -n "$SLACK_MCP_XOXP_TOKEN" ]; then
    SLACK_CONFIG+=$(cat <<EOF

        "SLACK_MCP_XOXP_TOKEN": "$SLACK_MCP_XOXP_TOKEN",
EOF
)
else
    SLACK_CONFIG+=$(cat <<EOF

        "SLACK_MCP_XOXC_TOKEN": "$SLACK_MCP_XOXC_TOKEN",
        "SLACK_MCP_XOXD_TOKEN": "$SLACK_MCP_XOXD_TOKEN",
EOF
)
fi

# Add optional config
ADD_MESSAGE_TOOL="${SLACK_MCP_ADD_MESSAGE_TOOL:-false}"
SLACK_CONFIG+=$(cat <<EOF

        "SLACK_MCP_ADD_MESSAGE_TOOL": "$ADD_MESSAGE_TOOL"
      }
    }
  }
}
EOF
)

# Write config
echo "$SLACK_CONFIG" > "$MCP_CONFIG"

echo "✓ MCP config written to: $MCP_CONFIG"
echo ""

# Test npx installation
echo "Testing slack-mcp-server installation..."
if command -v npx &> /dev/null; then
    echo "✓ npx is available"
    echo ""
    echo "The MCP server will be auto-installed on first run via npx"
else
    echo "❌ npx not found!"
    echo ""
    echo "Please install Node.js: https://nodejs.org/"
    exit 1
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Restart Claude Code to load the new MCP server"
echo "2. Try: 'Jarvis, list my Slack channels'"
echo "3. Check docs/SLACK_STEALTH_MODE.md for usage examples"
echo ""
echo "Tools available:"
echo "  - mcp__slack__conversations_history"
echo "  - mcp__slack__conversations_replies"
echo "  - mcp__slack__conversations_search_messages"
echo "  - mcp__slack__channels_list"
if [ "$ADD_MESSAGE_TOOL" = "true" ]; then
    echo "  - mcp__slack__conversations_add_message (ENABLED - posts as YOU!)"
fi
echo ""
