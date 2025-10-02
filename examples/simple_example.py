#!/usr/bin/env python3
"""Simple example showing basic usage of SuperMe SDK"""

from superme_sdk import SuperMeClient


def main():
    # Initialize client
    client = SuperMeClient(
        username="your-username",
        key="your-api-key",
        base_url="http://localhost:5000",  # Change to https://api.superme.ai for production
    )

    print("🚀 SuperMe SDK Simple Example")
    print("=" * 50)

    # Simple question
    print("\n1️⃣ Simple question:")
    answer = client.ask("What are the key principles of growth marketing?", user_id="1")
    print(f"Answer: {answer[:200]}...")

    # Using OpenAI-compatible interface
    print("\n2️⃣ Using OpenAI-compatible interface:")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "What is product-market fit?"}],
        extra_body={"user": "1"},
        max_tokens=150,
    )
    print(f"Response: {response.choices[0].message.content[:200]}...")

    # Multi-turn conversation
    print("\n3️⃣ Multi-turn conversation:")
    messages = [{"role": "user", "content": "What is growth hacking?"}]

    response1, conv_id = client.ask_with_history(messages, user_id="1")
    print(f"First response: {response1[:150]}...")

    messages.append({"role": "assistant", "content": response1})
    messages.append({"role": "user", "content": "Give me 3 examples"})

    response2, conv_id = client.ask_with_history(
        messages, user_id="1", conversation_id=conv_id
    )
    print(f"Second response: {response2[:150]}...")

    print("\n✅ Example completed!")


if __name__ == "__main__":
    main()
