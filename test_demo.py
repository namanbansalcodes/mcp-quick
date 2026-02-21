"""
MCP Gatekeeper - Demo script using mcp-use (Manufact).

Connects to the Gatekeeper MCP server using mcp-use's MCPClient
and walks through the full approval workflow programmatically.

No LLM/API key needed - this calls tools directly.

Usage:
    pip install fastmcp mcp-use
    python test_demo.py
"""

import asyncio
import json
import os
from mcp_use import MCPClient

# Suppress telemetry noise
os.environ.setdefault("MCP_USE_ANONYMIZED_TELEMETRY", "false")


async def main():
    # Connect to the Gatekeeper server via stdio using mcp-use
    config = {
        "mcpServers": {
            "gatekeeper": {
                "command": "python",
                "args": [os.path.join(os.path.dirname(__file__) or ".", "server.py")],
            }
        }
    }

    print("=" * 60)
    print("  MCP Gatekeeper - Demo (mcp-use MCPClient)")
    print("=" * 60)

    client = MCPClient.from_dict(config)

    try:
        # Create a session to the gatekeeper server
        session = await client.create_session("gatekeeper")

        # Helper to call a tool and print the result
        async def call(tool_name: str, args: dict | None = None) -> str:
            if args is None:
                args = {}
            print(f"\n>>> {tool_name}({json.dumps(args)})")
            result = await session.call_tool(tool_name, args)
            text = ""
            for block in result.content:
                if hasattr(block, "text"):
                    text += block.text
            print(text[:600])
            return text

        # ── Step 1: View policy ──
        print("\n" + "-" * 40)
        print("STEP 1: View policy")
        await call("get_policy")

        # ── Step 2: SAFE - read_file (auto-executes) ──
        print("\n" + "-" * 40)
        print("STEP 2: SAFE action - read_file (file doesn't exist yet)")
        await call("read_file", {"path": "nonexistent.txt"})

        # ── Step 3: SENSITIVE - write_file (needs approval) ──
        print("\n" + "-" * 40)
        print("STEP 3: SENSITIVE action - write_file (needs approval)")
        result = await call("write_file", {
            "path": "hello.txt",
            "content": "Hello from MCP Gatekeeper demo!"
        })

        # Extract action_id
        action_id = None
        try:
            data = json.loads(result)
            action_id = data.get("action_id")
        except json.JSONDecodeError:
            pass

        # ── Step 4: List pending ──
        print("\n" + "-" * 40)
        print("STEP 4: List pending actions")
        await call("list_pending")

        # ── Step 5: Approve the write ──
        if action_id:
            print("\n" + "-" * 40)
            print(f"STEP 5: Approve action {action_id}")
            await call("approve", {"action_id": action_id})

        # ── Step 6: Verify file was written ──
        print("\n" + "-" * 40)
        print("STEP 6: Read the file we just approved")
        await call("read_file", {"path": "hello.txt"})

        # ── Step 7: DANGEROUS - delete_file ──
        print("\n" + "-" * 40)
        print("STEP 7: DANGEROUS - delete_file (blocked, but approvable)")
        result = await call("delete_file", {"path": "hello.txt"})

        delete_id = None
        try:
            data = json.loads(result)
            delete_id = data.get("action_id")
        except json.JSONDecodeError:
            pass

        # ── Step 8: Deny the delete ──
        if delete_id:
            print("\n" + "-" * 40)
            print(f"STEP 8: Deny the delete ({delete_id})")
            await call("deny", {"action_id": delete_id})

        # ── Step 9: run_shell (always blocked) ──
        print("\n" + "-" * 40)
        print("STEP 9: DANGEROUS - run_shell (ALWAYS blocked)")
        await call("run_shell", {"command": "rm -rf /"})

        # ── Step 10: Path traversal ──
        print("\n" + "-" * 40)
        print("STEP 10: Security - path traversal attempt")
        await call("read_file", {"path": "../../etc/passwd"})

        # ── Step 11: Audit log ──
        print("\n" + "-" * 40)
        print("STEP 11: Audit log")
        await call("audit_log", {"limit": 15})

        # ── Step 12: Dashboard ──
        print("\n" + "-" * 40)
        print("STEP 12: Dashboard")
        await call("get_dashboard")

    finally:
        await client.close_all_sessions()

    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
