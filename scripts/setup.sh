#!/usr/bin/env bash
# Setup script for Jarvis LMAO

set -e

echo "🤖 Jarvis LMAO Setup"
echo "==================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Setup environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✓ .env created from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and configure your settings!"
    echo "   Required: EMBEDDING_PROVIDER (ollama or openai)"
    echo "   If using OpenAI: Add your OPENAI_API_KEY"
else
    echo "✓ .env file exists"
fi

# Check Qdrant
echo ""
echo "🔍 Checking Qdrant..."
if podman ps | grep -q qdrant; then
    echo "✓ Qdrant container running"
else
    echo "⚠️  Qdrant not running in Podman"
    echo "   Start it with: podman start qdrant"
fi

# Initialize schema
echo ""
echo "🗄️  Initialize Qdrant schema? (y/N)"
read -r response
if [ "$response" = "y" ]; then
    python scripts/init_schema.py
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Run: python scripts/init_schema.py (if not done)"
echo "3. Test: python src/server.py"
echo "4. Configure Claude Code MCP"
echo ""
echo "Documentation: README.md"
