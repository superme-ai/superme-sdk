#!/usr/bin/env python3
"""Simple example showing basic usage of SuperMe SDK"""

import os

from dotenv import load_dotenv

from superme_sdk import SuperMeClient

load_dotenv()


def main():
    api_key = os.environ["SUPERME_API_KEY"]
    client = SuperMeClient(api_key=api_key)

    print("SuperMe SDK Simple Example")
    print("=" * 50)

    # 1. Simple question
    print("\n1. Simple question:")
    answer = client.ask(
        "What are the key principles of growth marketing?", username="ludo"
    )
    print(f"Answer: {answer[:200]}...")

    # 2. Anonymous question (incognito mode)
    print("\n2. Anonymous question (incognito mode):")
    anonymous_answer = client.ask(
        "What are the key principles of growth marketing?",
        username="ludo",
        incognito=True,
    )
    print(f"Anonymous Answer: {anonymous_answer[:200]}...")

    # 3. OpenAI-style interface
    print("\n3. OpenAI-style chat.completions.create:")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "What is product-market fit?"}],
        username="ludo",
    )
    print(f"Response: {response.choices[0].message.content[:200]}...")
    print(f"Conversation ID: {response.metadata['conversation_id']}")

    # 4. Multi-turn conversation
    print("\n4. Multi-turn conversation:")
    messages = [{"role": "user", "content": "What is growth hacking?"}]

    response1, conv_id = client.ask_with_history(messages, username="ludo")
    print(f"First response: {response1[:150]}...")

    messages.append({"role": "assistant", "content": response1})
    messages.append({"role": "user", "content": "Give me 3 examples"})

    response2, conv_id = client.ask_with_history(
        messages, username="ludo", conversation_id=conv_id
    )
    print(f"Second response: {response2[:150]}...")

    print("\nExample completed!")


if __name__ == "__main__":
    main()
