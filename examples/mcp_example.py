#!/usr/bin/env python3
"""Example showing direct MCP JSON-RPC usage"""

import os

from dotenv import load_dotenv

from superme_sdk import SuperMeClient

load_dotenv()


def main():
    api_key = os.environ["SUPERME_API_KEY"]
    client = SuperMeClient(api_key=api_key)

    print("SuperMe SDK MCP Example")
    print("=" * 50)

    # 1. List all available MCP tools
    print("\n1. Available MCP tools:")
    tools = client.mcp_list_tools()
    for tool in tools:
        print(f"  - {tool['name']}: {tool.get('description', '')[:80]}")

    # 2. Call the ask tool directly
    print("\n2. Ask via MCP tool call:")
    answer = client.mcp_tool_call(
        "ask",
        {"question": "What is growth marketing?", "username": "ludo"},
    )
    print(f"  Answer: {answer[:200]}")

    # 3. Raw JSON-RPC request (tools/list)
    print("\n3. Raw JSON-RPC request (tools/list):")
    raw = client.raw_request("tools/list", {})
    tool_names = [t["name"] for t in raw.get("tools", [])]
    print(f"  Tools: {tool_names}")

    # 4. Raw JSON-RPC request (tools/call)
    print("\n4. Raw JSON-RPC request (tools/call):")
    raw2 = client.raw_request(
        "tools/call",
        {"name": "get_profile", "arguments": {"username": "ludo"}},
    )
    print(f"  Raw result: {str(raw2)[:200]}")

    print("\nMCP example completed!")


if __name__ == "__main__":
    main()
