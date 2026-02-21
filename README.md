# MCP Gatekeeper

**A policy-enforced MCP server with approval workflows, risk classification, and audit logging.**

Built for the [Manufact (mcp-use) Hackathon](https://manufact.com/hackathon) at Y Combinator, Feb 2026.

## What It Does

MCP Gatekeeper wraps "dangerous" tools (file read/write/delete, shell exec) with a **policy engine** that classifies every action by risk level and enforces approval workflows:

| Tool | Risk Level | Behavior |
|------|-----------|----------|
| `read_file` | SAFE | Executes immediately |
| `write_file` | SENSITIVE | Requires approval before execution |
| `delete_file` | DANGEROUS | Blocked by default, can be approved |
| `run_shell` | DANGEROUS | **Always** blocked, never approvable |

All file operations are **sandboxed** to `./sandbox/` with path traversal protection.

### Key Features
- **Policy engine** with configurable risk levels (edit `policy.json`)
- **Approval queue** - pending actions with approve/deny workflow
- **Audit log** - every action and decision is recorded
- **Sandbox** - filesystem operations restricted to `./sandbox/`
- **HTML Dashboard** - embedded MCP App UI with risk badges
- **12 MCP tools** exposed for full workflow control

## Quick Start

```bash
# Install dependencies
pip install fastmcp mcp-use

# Run the server
python server.py
```

## Git Safety (Recommended)

This repo includes a `.gitignore` and an optional pre-commit hook to prevent accidentally committing `node_modules/`, `__pycache__/`, `.env*`, and `*.log`.

```bash
./scripts/setup-githooks.sh
```

## How to Test

### Option 1: mcp-use Inspector (Recommended)

Go to the [Manufact Inspector](https://inspector.mcp-use.com) and connect with:

- **Transport:** stdio
- **Command:** `python`
- **Args:** `server.py`
- **Working directory:** path to this project

Or use the local inspector:
```bash
pip install fastmcp
fastmcp dev server.py
```

### Option 2: Automated Demo Script (mcp-use)

```bash
pip install mcp-use
python test_demo.py
```

This runs through the full workflow automatically using mcp-use's `MCPClient`.

### Option 3: Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gatekeeper": {
      "command": "python",
      "args": ["/full/path/to/server.py"]
    }
  }
}
```

## Demo Script (step by step)

Run these tool calls in order in the Inspector to see the full flow:

```
1. get_policy()
   → See risk levels for all tools

2. read_file(path="test.txt")
   → SAFE: auto-executes (file not found, that's OK)

3. write_file(path="hello.txt", content="Hello Hackathon!")
   → SENSITIVE: returns APPROVAL_REQUIRED + action_id

4. list_pending()
   → Shows the pending write action

5. approve(action_id="<id from step 3>")
   → Executes the write, file is created

6. read_file(path="hello.txt")
   → SAFE: reads "Hello Hackathon!"

7. delete_file(path="hello.txt")
   → DANGEROUS: returns APPROVAL_REQUIRED + action_id

8. deny(action_id="<id from step 7>")
   → Denies the delete, file is preserved

9. run_shell(command="ls -la")
   → DANGEROUS: BLOCKED permanently

10. read_file(path="../../etc/passwd")
    → BLOCKED: path traversal detected

11. audit_log()
    → Full history of all actions and decisions

12. get_dashboard()
    → Formatted overview of everything

13. get_dashboard_ui()
    → HTML widget with risk badges, pending queue, audit table
```

## Tools Reference

| Tool | Description |
|------|------------|
| `read_file(path)` | Read a file from sandbox |
| `write_file(path, content)` | Write a file (needs approval) |
| `delete_file(path)` | Delete a file (needs approval) |
| `run_shell(command)` | Shell exec (always blocked) |
| `list_pending()` | Show pending approval queue |
| `approve(action_id)` | Approve and execute a pending action |
| `deny(action_id)` | Deny a pending action |
| `audit_log(limit=25)` | View decision history |
| `get_policy()` | View current policy config |
| `get_dashboard()` | Text dashboard overview |
| `get_dashboard_ui()` | HTML dashboard (MCP App UI) |

## Project Structure

```
mcp-quick/
├── server.py          # MCP server (FastMCP) - all tools + policy engine
├── policy.json        # Configurable policy rules
├── mcp_config.json    # mcp-use client configuration
├── test_demo.py       # Automated demo using mcp-use MCPClient
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── sandbox/           # Sandboxed filesystem (all ops happen here)
```

## Customizing Policy

Edit `policy.json` to change behavior:

```json
{
  "write_file": {
    "risk_level": "SAFE",
    "default_action": "allow",
    "allow_approval": false
  }
}
```

- `risk_level`: `SAFE` | `SENSITIVE` | `DANGEROUS`
- `default_action`: `allow` | `require_approval` | `block`
- `allow_approval`: `true` | `false` (can users approve blocked actions?)

## Tech Stack

- **Server:** [FastMCP](https://gofastmcp.com) (official MCP Python SDK)
- **Client/Testing:** [mcp-use](https://mcp-use.com) (Manufact SDK)
- **Transport:** stdio (local, no network)
- **State:** In-memory (dicts/lists)
- **UI:** Self-contained HTML (MCP App compatible)
