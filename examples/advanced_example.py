#!/usr/bin/env python3
"""Advanced example showing features of SuperMe SDK"""

from superme_sdk import SuperMeClient


def main():
    client = SuperMeClient(
        username="your-username",
        key="your-api-key",
        base_url="http://localhost:5000",
    )

    print("🚀 SuperMe SDK Advanced Example")
    print("=" * 50)

    # 1. Structured conversation with context
    print("\n1️⃣ Building a conversation with context:")

    conversation = []

    # First question
    q1 = "Who is the founder of Y Combinator?"
    conversation.append({"role": "user", "content": q1})
    response1 = client.chat.completions.create(
        model="gpt-4", messages=conversation, extra_body={"user": "1"}, max_tokens=100
    )
    a1 = response1.choices[0].message.content
    conversation.append({"role": "assistant", "content": a1})
    print(f"Q: {q1}")
    print(f"A: {a1}")

    # Follow-up question using context
    q2 = "What companies did he help start?"
    conversation.append({"role": "user", "content": q2})
    response2 = client.chat.completions.create(
        model="gpt-4", messages=conversation, extra_body={"user": "1"}, max_tokens=150
    )
    a2 = response2.choices[0].message.content
    conversation.append({"role": "assistant", "content": a2})
    print(f"\nQ: {q2}")
    print(f"A: {a2}")

    # 2. Using raw API access
    print("\n2️⃣ Raw API access:")
    raw_response = client.raw_request(
        "/mcp", json={"method": "initialize", "params": {}}
    )
    print(f"MCP initialize response: {raw_response.json()}")

    # 3. Different user profiles
    print("\n3️⃣ Querying different user profiles:")
    users = ["1", "2"]
    question = "What are your areas of expertise?"

    for user_id in users:
        answer = client.ask(question, user_id=user_id, max_tokens=100)
        print(f"\nUser {user_id}: {answer[:150]}...")

    # 4. Custom parameters
    print("\n4️⃣ Using custom parameters:")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": "List 3 growth marketing tactics in a structured way",
            }
        ],
        extra_body={"user": "1", "response_format": {"type": "json_object"}},
        max_tokens=300,
    )
    print(f"Structured response:\n{response.choices[0].message.content}")

    print("\n✅ Advanced example completed!")


if __name__ == "__main__":
    main()
