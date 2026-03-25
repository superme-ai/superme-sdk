#!/usr/bin/env python3
"""Simple example showing basic usage of SuperMe SDK"""

import os

from superme_sdk import SuperMeClient


def main():
    # Get your API key from superme.ai/settings
    api_key = os.environ["SUPERME_API_KEY"]
    client = SuperMeClient(api_key=api_key, base_url="https://api.superme.ai")

    print("SuperMe SDK Simple Example")
    print("=" * 50)

    # Simple question
    print("\n1. Simple question:")
    answer = client.ask("What are the key principles of growth marketing?", username="ludo")
    print(f"Answer: {answer[:200]}...")

    # Anonymous question (incognito mode)
    print("\n2. Anonymous question (incognito mode):")
    anonymous_answer = client.ask("What are the key principles of growth marketing?", username="ludo", incognito=True)
    print(f"Anonymous Answer: {anonymous_answer[:200]}...")

    # Using chat_completions (returns full response dict)
    print("\n3. Using chat_completions (full response):")
    response = client.chat_completions(
        messages=[{"role": "user", "content": "What is product-market fit?"}],
        username="ludo",
        max_tokens=150,
    )
    print(f"Response: {response['choices'][0]['message']['content'][:200]}...")

    # Multi-turn conversation
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

    # Anonymous multi-turn conversation
    print("\n5. Anonymous multi-turn conversation:")
    anonymous_messages = [{"role": "user", "content": "What is growth hacking?"}]

    anonymous_response1, anonymous_conv_id = client.ask_with_history(anonymous_messages, username="ludo", incognito=True)
    print(f"Anonymous first response: {anonymous_response1[:150]}...")

    anonymous_messages.append({"role": "assistant", "content": anonymous_response1})
    anonymous_messages.append({"role": "user", "content": "Give me 3 examples"})

    anonymous_response2, anonymous_conv_id = client.ask_with_history(
        anonymous_messages, username="ludo", conversation_id=anonymous_conv_id, incognito=True
    )
    print(f"Anonymous second response: {anonymous_response2[:150]}...")

    print("\nExample completed!")


if __name__ == "__main__":
    main()
