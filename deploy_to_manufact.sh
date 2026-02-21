#!/bin/bash
set -e

echo "🚀 Deploying Polymarket MCP to Manufact..."
echo ""
echo "⚠️  PREREQUISITES:"
echo "   1. GitHub repo must be PUBLIC"
echo "   2. Go to: https://github.com/namanbansalcodes/mcp-quick/settings"
echo "   3. Change visibility to PUBLIC"
echo ""
read -p "Have you made the repo public? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Please make the repo public first, then run this script again."
    exit 1
fi

echo ""
echo "📦 Deploying from polymarket-mcp directory..."
cd "$(dirname "$0")/polymarket-mcp"

# Deploy with correct environment variables
npx @mcp-use/cli deploy \
  --name "polymarket-mcp-production" \
  --port 3000 \
  --runtime node \
  --env-file .env.deploy \
  --open

echo ""
echo "✅ Deployment command executed!"
echo "📊 Check status with: npx @mcp-use/cli deployments list"
