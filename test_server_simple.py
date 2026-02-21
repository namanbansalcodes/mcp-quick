#!/usr/bin/env python3
"""
Polymarket MCP Server Health Check (HTTP-based)
Tests server functionality and validates response sizes
"""

import json
import requests
import subprocess
import sys
from datetime import datetime

# Configuration
SERVER_URL = "https://files-subscribers-deborah-mere.trycloudflare.com/mcp"
MAX_SIZE_MB = 5.0
WARNING_SIZE_MB = 1.0

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
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, check=True)
        return process_name in result.stdout
    except:
        return None

def mcp_request(method, params=None, session_id="test-session"):
    """Make an MCP JSON-RPC request"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    headers = {
        "Content-Type": "application/json",
        "mcp-session-id": session_id
    }

    try:
        response = requests.post(SERVER_URL, json=payload, headers=headers, timeout=10)
        return response.text, len(response.text), response.status_code
    except Exception as e:
        return None, 0, 0

def test_server():
    """Main test function"""
    print("=" * 70)
    print("POLYMARKET MCP SERVER HEALTH CHECK")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Server URL: {SERVER_URL}")
    print(f"Max Size Limit: {MAX_SIZE_MB} MB")
    print("=" * 70)

    all_passed = True

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

    # Test 1: Initialize
    print("\n🔌 TESTING: initialize")
    print("-" * 70)
    response, size, status = mcp_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0.0"}
    })

    if status == 200:
        print(f"✅ Status: {status}")
        print(f"Response size: {format_size(size)}")
        if size_mb(size) > MAX_SIZE_MB:
            print(f"❌ ERROR: Response exceeds {MAX_SIZE_MB} MB!")
            all_passed = False
    else:
        print(f"❌ Failed with status: {status}")
        all_passed = False

    # Test 2: List Tools
    print("\n🔧 TESTING: tools/list")
    print("-" * 70)
    response, size, status = mcp_request("tools/list")

    if status == 200:
        print(f"✅ Status: {status}")
        print(f"Response size: {format_size(size)}")
        try:
            data = json.loads(response)
            tools = data.get('result', {}).get('tools', [])
            print(f"Tools found: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.get('name')}")
        except:
            pass

        if size_mb(size) > MAX_SIZE_MB:
            print(f"❌ ERROR: Response exceeds {MAX_SIZE_MB} MB!")
            all_passed = False
        else:
            print("✅ Size OK")
    else:
        print(f"❌ Failed with status: {status}")
        all_passed = False

    # Test 3: List Resources
    print("\n📦 TESTING: resources/list")
    print("-" * 70)
    response, size, status = mcp_request("resources/list")

    if status == 200:
        print(f"✅ Status: {status}")
        print(f"Response size: {format_size(size)}")
        try:
            data = json.loads(response)
            resources = data.get('result', {}).get('resources', [])
            print(f"Resources found: {len(resources)}")
            for resource in resources:
                print(f"  - {resource.get('name')}")
        except:
            pass

        if size_mb(size) > MAX_SIZE_MB:
            print(f"❌ ERROR: Response exceeds {MAX_SIZE_MB} MB!")
            all_passed = False
        else:
            print("✅ Size OK")
    else:
        print(f"❌ Failed with status: {status}")

    # Test 4: Call list_trending_markets
    print("\n📈 TESTING: list_trending_markets")
    print("-" * 70)
    response, size, status = mcp_request("tools/call", {
        "name": "list_trending_markets",
        "arguments": {}
    })

    if status == 200:
        print(f"✅ Status: {status}")
        print(f"Response size: {format_size(size)}")
        try:
            data = json.loads(response)
            content = data.get('result', {}).get('content', [])
            if content and 'text' in content[0]:
                preview = content[0]['text'][:150].replace('\n', ' ')
                print(f"Preview: {preview}...")
        except:
            pass

        if size_mb(size) > MAX_SIZE_MB:
            print(f"❌ ERROR: Response exceeds {MAX_SIZE_MB} MB!")
            all_passed = False
        elif size_mb(size) > WARNING_SIZE_MB:
            print(f"⚠️  WARNING: Response exceeds {WARNING_SIZE_MB} MB")
        else:
            print("✅ Size OK")
    else:
        print(f"❌ Failed with status: {status}")
        all_passed = False

    # Test 5: Call view_market (THE CRITICAL TEST)
    print("\n🎨 TESTING: view_market (WITH WIDGET)")
    print("-" * 70)
    response, size, status = mcp_request("tools/call", {
        "name": "view_market",
        "arguments": {"keyword": "bitcoin"}
    })

    if status == 200:
        print(f"✅ Status: {status}")
        print(f"Response size: {format_size(size)}")
        try:
            data = json.loads(response)
            content = data.get('result', {}).get('content', [])
            print(f"Content blocks: {len(content)}")

            # Check for widget resource reference
            has_resource = any('resource' in block for block in content)
            print(f"Has widget resource: {'✅ Yes' if has_resource else 'ℹ️  No'}")
        except:
            pass

        if size_mb(size) > MAX_SIZE_MB:
            print(f"❌ CRITICAL ERROR: Response exceeds {MAX_SIZE_MB} MB limit!")
            print(f"   This is likely causing the '5MB limit' error in Claude web!")
            all_passed = False
        elif size_mb(size) > WARNING_SIZE_MB:
            print(f"⚠️  WARNING: Response size {format_size(size)} exceeds {WARNING_SIZE_MB} MB")
            print(f"   Getting close to limit - consider optimizing")
        else:
            print("✅ Size OK - Well under 5MB limit")
    else:
        print(f"❌ Failed with status: {status}")
        all_passed = False

    # Test 6: Call place_bet
    print("\n💰 TESTING: place_bet")
    print("-" * 70)
    response, size, status = mcp_request("tools/call", {
        "name": "place_bet",
        "arguments": {
            "market_title": "Test Market",
            "outcome": "YES",
            "amount": 10
        }
    })

    if status == 200:
        print(f"✅ Status: {status}")
        print(f"Response size: {format_size(size)}")
        if size_mb(size) > MAX_SIZE_MB:
            print(f"❌ ERROR: Response exceeds {MAX_SIZE_MB} MB!")
            all_passed = False
        else:
            print("✅ Size OK")
    else:
        print(f"❌ Failed with status: {status}")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if all_passed:
        print("✅ ALL TESTS PASSED")
        print(f"✅ All responses are under {MAX_SIZE_MB} MB limit")
        print("✅ Server is healthy and ready for use")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️  Check errors above for details")

    return all_passed

if __name__ == "__main__":
    print("\nStarting health check...\n")
    success = test_server()
    print()
    sys.exit(0 if success else 1)
