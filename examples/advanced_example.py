#!/usr/bin/env python3
"""Advanced example showing more SDK features"""

import os

from dotenv import load_dotenv

from superme_sdk import SuperMeClient

load_dotenv()


def main():
    api_key = os.environ["SUPERME_API_KEY"]
    client = SuperMeClient(api_key=api_key)

    print("SuperMe SDK Advanced Example")
    print("=" * 50)

    # 1. Multi-turn conversation with OpenAI interface
    print("\n1. Multi-turn conversation (OpenAI-style):")
    messages = [{"role": "user", "content": "What is content marketing?"}]

    r1 = client.chat.completions.create(
        model="gpt-4", messages=messages, username="ludo"
    )
    conv_id = r1.metadata["conversation_id"]
    print(f"Turn 1: {r1.choices[0].message.content[:150]}...")

    messages.append({"role": "assistant", "content": r1.choices[0].message.content})
    messages.append(
        {"role": "user", "content": "How does it differ from social media marketing?"}
    )

    r2 = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        username="ludo",
        conversation_id=conv_id,
    )
    print(f"Turn 2: {r2.choices[0].message.content[:150]}...")

    # 2. MCP tools - list available tools
    print("\n2. List MCP tools:")
    tools = client.mcp_list_tools()
    for tool in tools:
        print(f"  - {tool['name']}: {tool.get('description', '')[:60]}")

    # 3. MCP tool call - find a user
    print("\n3. Find user by name:")
    result = client.mcp_tool_call("find_user_by_name", {"name": "ludo"})
    print(f"  Result: {result[:200]}")

    # 4. MCP tool call - get profile
    print("\n4. Get profile:")
    profile = client.mcp_tool_call("get_profile", {"username": "ludo"})
    print(f"  Profile: {profile[:200]}")

    # 5. List conversations
    print("\n5. List conversations:")
    conversations = client.mcp_tool_call("list_conversations", {"username": "ludo"})
    print(f"  Conversations: {conversations[:200]}")

    print("\nAdvanced example completed!")


if __name__ == "__main__":
    main()
