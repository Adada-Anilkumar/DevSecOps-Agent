#!/bin/bash
set -e

echo "🚀 DevSecOps Agent - Local Testing Setup"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY=sk-..."
    echo "   - GITHUB_TOKEN=ghp_..."
    echo "   - GITHUB_WEBHOOK_SECRET=your-secret"
    echo ""
    read -p "Press Enter after you've edited .env..."
else
    echo "✅ .env file exists"
fi

# Check if API keys are set
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-..." ]; then
    echo "❌ OPENAI_API_KEY not set in .env"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN not set - webhook won't be able to post comments"
fi

echo ""
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
pip install -q -e .
echo "✅ Dependencies installed"

echo ""
echo "🔧 Testing configuration..."
python -c "from devsecops_agent.settings import get_settings; get_settings()" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Configuration valid"
else
    echo "❌ Configuration error - check your .env file"
    exit 1
fi

echo ""
echo "🏥 Starting health check..."
python -m devsecops_agent.webhook.serve &
SERVER_PID=$!
sleep 3

if curl -s http://localhost:8080/health | grep -q "ok"; then
    echo "✅ Server is healthy"
    kill $SERVER_PID
else
    echo "❌ Server health check failed"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Start the agent:"
echo "   python -m devsecops_agent.webhook.serve"
echo ""
echo "2. In another terminal, expose with ngrok:"
echo "   ngrok http 8080"
echo ""
echo "3. Configure GitHub webhook:"
echo "   - URL: https://YOUR-NGROK-URL.ngrok.io/webhook"
echo "   - Secret: (value from GITHUB_WEBHOOK_SECRET in .env)"
echo "   - Events: Pull requests"
echo ""
echo "4. Create a test PR and watch it work!"
echo ""
echo "📖 Full guide: docs/LOCAL_TESTING.md"
