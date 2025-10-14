#!/usr/bin/env python3
"""MCP example showing how to use SuperMe API with MCP protocol"""

import json
import requests
from superme_sdk import SuperMeClient


def main():
    client = SuperMeClient(
        api_key="YOUR_API_KEY_HERE",
        base_url="https://api.superme.ai",
    )

    print("🚀 SuperMe MCP Example")
    print("=" * 50)

    # 1. Initialize MCP connection
    print("\n1️⃣ Initialize MCP connection:")
    init_response = client.raw_request(
        "/mcp", 
        json={"method": "initialize", "params": {}}
    )
    print(f"Server info: {init_response.json()['serverInfo']}")
    print(f"Capabilities: {init_response.json()['capabilities']}")

    # 2. List available tools
    print("\n2️⃣ List available tools:")
    tools_response = client.raw_request(
        "/mcp", 
        json={"method": "tools/list", "params": {}}
    )
    tools = tools_response.json()["tools"]
    print(f"Available tools: {[tool['name'] for tool in tools]}")

    # 3. Ask a question using MCP ask tool
    print("\n3️⃣ Ask a question using MCP ask tool:")
    ask_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "ask",
                "arguments": {
                    "username": "ludo",
                    "question": "What is product-market fit?"
                }
            }
        }
    )
    
    # Parse the response
    ask_result = json.loads(ask_response.json()["content"][0]["text"])
    print(f"Question: {ask_result['question']}")
    print(f"Response: {ask_result['response'][:200]}...")
    print(f"Conversation ID: {ask_result['conversation_id']}")

    # 3.5. Ask an anonymous question using MCP ask tool
    print("\n3️⃣.5 Ask an anonymous question using MCP ask tool:")
    anonymous_ask_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "ask",
                "arguments": {
                    "username": "ludo",
                    "question": "What is product-market fit?",
                    "incognito": True
                }
            }
        }
    )
    
    # Parse the anonymous response
    anonymous_ask_result = json.loads(anonymous_ask_response.json()["content"][0]["text"])
    print(f"Anonymous Question: {anonymous_ask_result['question']}")
    print(f"Anonymous Response: {anonymous_ask_result['response'][:200]}...")
    print(f"Anonymous Conversation ID: {anonymous_ask_result['conversation_id']}")

    # 4. List conversations
    print("\n4️⃣ List conversations:")
    conv_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "list_conversations",
                "arguments": {
                    "limit": 5
                }
            }
        }
    )
    conversations = json.loads(conv_response.json()["content"][0]["text"])
    print(f"Found {len(conversations)} conversations")
    if conversations:
        print(f"Latest conversation: {conversations[0]}")

    # 5. Get conversation details
    if conversations:
        print("\n5️⃣ Get conversation details:")
        conv_id = conversations[0]["id"]
        conv_details_response = client.raw_request(
            "/mcp",
            json={
                "method": "tools/call",
                "params": {
                    "name": "get_conversation",
                    "arguments": {
                        "conversation_id": conv_id
                    }
                }
            }
        )
        conv_details = json.loads(conv_details_response.json()["content"][0]["text"])
        print(f"Conversation details: {conv_details}")

    # 6. Get user profile (specific user)
    print("\n6️⃣ Get user profile for specific user:")
    profile_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "get_profile",
                "arguments": {
                    "username": "ludo"
                }
            }
        }
    )
    profile = json.loads(profile_response.json()["content"][0]["text"])
    print(f"Profile for 'ludo': {json.dumps(profile, indent=2)}")

    # 7. Get authenticated user's profile (no username)
    print("\n7️⃣ Get authenticated user's profile:")
    my_profile_response = client.raw_request(
        "/mcp",
        json={
            "method": "tools/call",
            "params": {
                "name": "get_profile",
                "arguments": {}
            }
        }
    )
    my_profile = json.loads(my_profile_response.json()["content"][0]["text"])
    print(f"My profile: {json.dumps(my_profile, indent=2)}")

    # 8. Demonstrate SDK simplified methods with incognito
    print("\n8️⃣ Demonstrate SDK simplified methods with incognito:")
    
    # Regular question
    print("Regular question:")
    regular_answer = client.ask("What are the key principles of startup success?", username="ludo")
    print(f"Regular answer: {regular_answer[:100]}...")
    
    # Anonymous question
    print("\nAnonymous question:")
    anonymous_answer = client.ask("What are the key principles of startup success?", username="ludo", incognito=True)
    print(f"Anonymous answer: {anonymous_answer[:100]}...")

    print("\n✅ MCP Example completed!")


if __name__ == "__main__":
    main()
