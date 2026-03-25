#!/usr/bin/env python3
"""MCP example showing how to use SuperMe API with MCP protocol"""

import json
import os

from superme_sdk import SuperMeClient


def main():
    # Get your API key from superme.ai/settings
    api_key = os.environ["SUPERME_API_KEY"]
    client = SuperMeClient(api_key=api_key, base_url="https://api.superme.ai")

    print("SuperMe MCP Example")
    print("=" * 50)

    # 1. Initialize MCP connection
    print("\n1. Initialize MCP connection:")
    init_response = client.raw_request(
        "/mcp",
        json={"method": "initialize", "params": {}},
    )
    init_data = init_response.json()
    print(f"Server info: {init_data.get('serverInfo')}")
    print(f"Capabilities: {init_data.get('capabilities')}")

    # 2. List available tools
    print("\n2. List available tools:")
    tools_response = client.raw_request(
        "/mcp",
        json={"method": "tools/list", "params": {}},
    )
    tools = tools_response.json()["tools"]
    print(f"Available tools: {[tool['name'] for tool in tools]}")

    # 3. Ask a question using MCP ask tool
    print("\n3. Ask a question using MCP ask tool:")
    ask_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "ask",
                "arguments": {
                    "username": "ludo",
                    "question": "What is product-market fit?",
                },
            },
        },
    )
    ask_result = json.loads(ask_response.json()["content"][0]["text"])
    print(f"Question: {ask_result['question']}")
    print(f"Response: {ask_result['response'][:200]}...")
    print(f"Conversation ID: {ask_result['conversation_id']}")

    # 4. Ask an anonymous question
    print("\n4. Ask an anonymous question using MCP ask tool:")
    anon_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "ask",
                "arguments": {
                    "username": "ludo",
                    "question": "What is product-market fit?",
                    "incognito": True,
                },
            },
        },
    )
    anon_result = json.loads(anon_response.json()["content"][0]["text"])
    print(f"Anonymous Response: {anon_result['response'][:200]}...")

    # 5. List conversations
    print("\n5. List conversations:")
    conv_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "list_conversations",
                "arguments": {"limit": 5},
            },
        },
    )
    conversations = json.loads(conv_response.json()["content"][0]["text"])
    print(f"Found {len(conversations)} conversations")
    if conversations:
        print(f"Latest conversation: {conversations[0]}")

    # 6. Get conversation details
    if conversations:
        print("\n6. Get conversation details:")
        conv_id = conversations[0]["id"]
        details_response = client.raw_request(
            "/mcp",
            json={
                "method": "tools/call",
                "params": {
                    "name": "get_conversation",
                    "arguments": {"conversation_id": conv_id},
                },
            },
        )
        details = json.loads(details_response.json()["content"][0]["text"])
        print(f"Conversation details: {details}")

    # 7. Get user profile
    print("\n7. Get user profile:")
    profile_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "get_profile",
                "arguments": {"username": "ludo"},
            },
        },
    )
    profile = json.loads(profile_response.json()["content"][0]["text"])
    print(f"Profile: {json.dumps(profile, indent=2)}")

    # 8. Get own profile
    print("\n8. Get authenticated user's profile:")
    my_profile_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "get_profile",
                "arguments": {},
            },
        },
    )
    my_profile = json.loads(my_profile_response.json()["content"][0]["text"])
    print(f"My profile: {json.dumps(my_profile, indent=2)}")

    # 9. SDK high-level methods
    print("\n9. SDK high-level methods:")
    answer = client.ask("What are the key principles of startup success?", username="ludo")
    print(f"Answer: {answer[:100]}...")

    anon_answer = client.ask(
        "What are the key principles of startup success?", username="ludo", incognito=True
    )
    print(f"Anonymous answer: {anon_answer[:100]}...")

    print("\nMCP Example completed!")


if __name__ == "__main__":
    main()
