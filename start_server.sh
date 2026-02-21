#!/bin/bash

cd /Users/namanbansal/Desktop/mcp-quick/polymarket-mcp

# New tunnel URL
export MCP_PUBLIC_URL="https://bugs-introducing-eagles-romance.trycloudflare.com"
export CSP_URLS="https://bugs-introducing-eagles-romance.trycloudflare.com,https://claude.ai,https://*.claude.ai"

# Start server
node dist/index.js
