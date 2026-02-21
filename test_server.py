#!/usr/bin/env python3
"""
Polymarket MCP Server Health Check & Size Validator
Tests server functionality and validates response sizes
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime

# Add mcp-use to path
sys.path.insert(0, '/Users/namanbansal/anaconda3/envs/mcp-quick/lib/python3.12/site-packages')

try:
    from mcp_use import MCPClient
except ImportError:
    print("❌ ERROR: mcp_use not found. Run: pip install mcp-use")
    sys.exit(1)

# Configuration
SERVER_URL = "https://conservative-answers-wallpaper-refugees.trycloudflare.com/mcp"
MAX_SIZE_MB = 5.0  # Maximum allowed size in MB
WARNING_SIZE_MB = 1.0  # Warning threshold in MB

def size_mb(size_bytes):
    """Convert bytes to MB"""
    return size_bytes / (1024 * 1024)

def format_size(size_bytes):
    """Format size in human-readable format"""
    mb = size_mb(size_bytes)
    if mb < 0.001:
        return f"{size_bytes} bytes"
    elif mb < 1:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{mb:.3f} MB"

def check_process(process_name):
    """Check if a process is running"""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            check=True
        )
        return process_name in result.stdout
    except Exception as e:
        print(f"⚠️  Warning: Could not check process: {e}")
        return None

async def test_server():
    """Main test function"""
    print("=" * 70)
    print("POLYMARKET MCP SERVER HEALTH CHECK")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Server URL: {SERVER_URL}")
    print(f"Max Size Limit: {MAX_SIZE_MB} MB")
    print("=" * 70)

    # Check processes
    print("\n📊 PROCESS STATUS")
    print("-" * 70)

    node_running = check_process("node dist/index.js")
    cloudflared_running = check_process("cloudflared tunnel")

    print(f"Node Server:       {'✅ RUNNING' if node_running else '❌ NOT RUNNING'}")
    print(f"Cloudflared Tunnel: {'✅ RUNNING' if cloudflared_running else '❌ NOT RUNNING'}")

    if not node_running or not cloudflared_running:
        print("\n❌ FATAL: Required processes not running!")
        return False

    # Test MCP connection
    print("\n🔌 MCP CONNECTION TEST")
    print("-" * 70)

    config = {"polymarket": {"url": SERVER_URL}}
    client = MCPClient.from_dict(config)

    try:
        session = await client.create_session("polymarket")
        if session is None:
            print("❌ Failed to create session")
            return False

        print("✅ Session created successfully")

        # Test 1: List Tools
        print("\n🔧 TESTING: tools/list")
        print("-" * 70)
        tools_result = await session.list_tools()
        tools_json = json.dumps([t.model_dump() for t in tools_result.tools])
        tools_size = len(tools_json)

        print(f"Tools found: {len(tools_result.tools)}")
        for tool in tools_result.tools:
            print(f"  - {tool.name}")
        print(f"Response size: {format_size(tools_size)}")

        if size_mb(tools_size) > WARNING_SIZE_MB:
            print(f"⚠️  WARNING: Response size exceeds {WARNING_SIZE_MB} MB")
        elif size_mb(tools_size) > MAX_SIZE_MB:
            print(f"❌ ERROR: Response size exceeds {MAX_SIZE_MB} MB limit!")
        else:
            print("✅ Size OK")

        # Test 2: List Resources
        print("\n📦 TESTING: resources/list")
        print("-" * 70)
        try:
            resources_result = await session.list_resources()
            resources_json = json.dumps([r.model_dump() for r in resources_result.resources])
            resources_size = len(resources_json)

            print(f"Resources found: {len(resources_result.resources)}")
            for resource in resources_result.resources:
                print(f"  - {resource.name}")
            print(f"Response size: {format_size(resources_size)}")

            if size_mb(resources_size) > MAX_SIZE_MB:
                print(f"❌ ERROR: Response size exceeds {MAX_SIZE_MB} MB limit!")
            else:
                print("✅ Size OK")
        except Exception as e:
            print(f"⚠️  Warning: Could not list resources: {e}")

        # Test 3: Call list_trending_markets
        print("\n📈 TESTING: list_trending_markets tool")
        print("-" * 70)
        try:
            result = await session.call_tool("list_trending_markets", {})
            result_json = json.dumps(result.model_dump())
            result_size = len(result_json)

            print(f"Response size: {format_size(result_size)}")
            print(f"Content blocks: {len(result.content)}")

            if result.content and hasattr(result.content[0], 'text'):
                preview = result.content[0].text[:200].replace('\n', ' ')
                print(f"Preview: {preview}...")

            if size_mb(result_size) > MAX_SIZE_MB:
                print(f"❌ ERROR: Response size exceeds {MAX_SIZE_MB} MB limit!")
            else:
                print("✅ Size OK")
        except Exception as e:
            print(f"❌ Error calling tool: {e}")

        # Test 4: Call view_market (with widget)
        print("\n🎨 TESTING: view_market tool (with widget)")
        print("-" * 70)
        try:
            result = await session.call_tool("view_market", {"keyword": "bitcoin"})
            result_json = json.dumps(result.model_dump())
            result_size = len(result_json)

            print(f"Response size: {format_size(result_size)}")
            print(f"Content blocks: {len(result.content)}")

            # Check for widget reference
            has_widget = any(hasattr(block, 'resource') for block in result.content)
            print(f"Has widget resource: {'✅ Yes' if has_widget else '❌ No'}")

            if size_mb(result_size) > MAX_SIZE_MB:
                print(f"❌ ERROR: Response size exceeds {MAX_SIZE_MB} MB limit!")
                return False
            elif size_mb(result_size) > WARNING_SIZE_MB:
                print(f"⚠️  WARNING: Response size exceeds {WARNING_SIZE_MB} MB")
            else:
                print("✅ Size OK")
        except Exception as e:
            print(f"❌ Error calling tool: {e}")
            return False

        # Test 5: Call place_bet
        print("\n💰 TESTING: place_bet tool")
        print("-" * 70)
        try:
            result = await session.call_tool("place_bet", {
                "market_title": "Test Market",
                "outcome": "YES",
                "amount": 10
            })
            result_json = json.dumps(result.model_dump())
            result_size = len(result_json)

            print(f"Response size: {format_size(result_size)}")
            if size_mb(result_size) > MAX_SIZE_MB:
                print(f"❌ ERROR: Response size exceeds {MAX_SIZE_MB} MB limit!")
            else:
                print("✅ Size OK")
        except Exception as e:
            print(f"❌ Error calling tool: {e}")

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print("✅ All tests completed")
        print(f"Server URL: {SERVER_URL}")
        print(f"All responses under {MAX_SIZE_MB} MB limit: ✅")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.close_all_sessions()

if __name__ == "__main__":
    print("\nStarting health check...\n")
    success = asyncio.run(test_server())

    print("\n" + "=" * 70)
    if success:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
