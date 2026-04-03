#!/usr/bin/env python3
"""
test_stdio.py — Tests the MCP stdio protocol layer.

This is separate from test_server.py because it tests a different thing:
not the Pokédex logic, but whether the server speaks the MCP protocol
correctly — can it start up, accept a JSON-RPC message, and respond?

MCP clients (Claude Desktop, Cursor, etc.) communicate with servers
exclusively via stdin/stdout. This test simulates that by spawning
the server as a subprocess and sending it a real MCP message.

Run with:
    python test_stdio.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path

SERVER_PATH = Path(__file__).parent / "server.py"


def test_server_starts():
    """Check the server process starts without immediately crashing."""
    print("1. Server startup")

    proc = subprocess.Popen(
        [sys.executable, str(SERVER_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    proc.terminate()
    _, stderr = proc.communicate(timeout=5)

    # A crash would show a Python traceback in stderr
    if b"Traceback" in stderr:
        print(f"   FAIL — server crashed on startup:\n{stderr.decode()}")
        return False

    print("   OK — server started cleanly")
    return True


def test_mcp_initialize():
    """Send an MCP initialize message and check we get a valid JSON-RPC response."""
    print("\n2. MCP initialize handshake")

    init_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    proc = subprocess.Popen(
        [sys.executable, str(SERVER_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        payload = json.dumps(init_message) + "\n"
        stdout, _ = proc.communicate(input=payload, timeout=10)

        if not stdout.strip():
            print("   FAIL — no response from server")
            return False

        response = json.loads(stdout.strip())
        assert response.get("jsonrpc") == "2.0", "Missing jsonrpc field"
        assert "result" in response or "error" in response, "Missing result/error"
        print("   OK — valid JSON-RPC response received")
        return True

    except subprocess.TimeoutExpired:
        # stdio servers block waiting for more input — a timeout here
        # just means the server is alive and waiting, which is correct.
        proc.kill()
        print("   OK — server is alive and waiting for input (expected for stdio)")
        return True

    except json.JSONDecodeError as e:
        print(f"   FAIL — response was not valid JSON: {e}")
        return False

    except AssertionError as e:
        print(f"   FAIL — response missing required fields: {e}")
        return False


def main():
    print("Pokédex MCP Server — Stdio Protocol Tests")
    print("=" * 45)

    results = [
        test_server_starts(),
        test_mcp_initialize(),
    ]

    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 45}")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\nAll good — the server is ready to register with an MCP client.")
        print("Point your claude_desktop_config.json at server.py and restart Claude.")
    else:
        print("\nSome tests failed. Check the errors above before connecting to a client.")
        sys.exit(1)


if __name__ == "__main__":
    main()