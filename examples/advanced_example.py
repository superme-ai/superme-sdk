#!/usr/bin/env python3
"""Advanced example showing features of SuperMe SDK"""

import os

from superme_sdk import SuperMeClient


def main():
    # Get your API key from superme.ai/settings
    api_key = os.environ["SUPERME_API_KEY"]
    client = SuperMeClient(api_key=api_key, base_url="https://api.superme.ai")

    print("SuperMe SDK Advanced Example")
    print("=" * 50)

    # 1. Structured conversation with context
    print("\n1. Building a conversation with context:")

    conversation = []

    q1 = "Who is the founder of Y Combinator?"
    conversation.append({"role": "user", "content": q1})
    response1 = client.chat_completions(
        messages=conversation, username="ludo", max_tokens=100
    )
    a1 = response1["choices"][0]["message"]["content"]
    conversation.append({"role": "assistant", "content": a1})
    print(f"Q: {q1}")
    print(f"A: {a1}")

    q2 = "What companies did he help start?"
    conversation.append({"role": "user", "content": q2})
    response2 = client.chat_completions(
        messages=conversation, username="ludo", max_tokens=150
    )
    a2 = response2["choices"][0]["message"]["content"]
    conversation.append({"role": "assistant", "content": a2})
    print(f"\nQ: {q2}")
    print(f"A: {a2}")

    # 2. Using raw API access
    print("\n2. Raw API access:")
    try:
        raw_response = client.raw_request(
            "/mcp", json={"method": "initialize", "params": {}}
        )
        print(f"Response status: {raw_response.status_code}")

        if raw_response.status_code == 200:
            if raw_response.text.strip():
                print(f"MCP initialize response: {raw_response.json()}")
            else:
                print("MCP endpoint returned empty response")
        else:
            print(f"Request failed with status {raw_response.status_code}")
    except Exception as e:
        print(f"Error making raw request: {e}")

    # 3. Different user profiles
    print("\n3. Querying different user profiles:")
    usernames = ["ludo", "casey"]
    question = "What are your areas of expertise?"

    for username in usernames:
        answer = client.ask(question, username=username, max_tokens=100)
        print(f"\nUser {username}: {answer[:150]}...")

    # 4. Structured responses with JSON schema
    print("\n4. Structured responses with JSON schema:")

    user_profile_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "user_profile",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "expertise": {"type": "array", "items": {"type": "string"}},
                    "location": {"type": "string"},
                },
                "required": ["name", "expertise", "location"],
            },
            "strict": True,
        },
    }

    profile_response = client.chat_completions(
        messages=[
            {
                "role": "user",
                "content": "Create a user profile for a 28-year-old marketing expert named Sarah from San Francisco with expertise in growth hacking, content marketing, and social media",
            }
        ],
        username="ludo",
        max_tokens=200,
        response_format=user_profile_schema,
    )
    print(f"Structured profile:\n{profile_response['choices'][0]['message']['content']}")

    # 5. Custom dict schema
    print("\n5. Custom dict schema:")
    tactics_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "marketing_tactics",
            "schema": {
                "type": "object",
                "properties": {
                    "tactics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "priority": {"type": "integer"},
                            },
                            "required": ["name", "description", "priority"],
                        },
                    }
                },
                "required": ["tactics"],
            },
        },
    }

    tactics_response = client.chat_completions(
        messages=[
            {
                "role": "user",
                "content": "List 3 growth marketing tactics with descriptions and priority levels",
            }
        ],
        username="ludo",
        max_tokens=400,
        response_format=tactics_schema,
    )
    print(f"Custom schema response:\n{tactics_response['choices'][0]['message']['content']}")

    print("\nAdvanced example completed!")


if __name__ == "__main__":
    main()
