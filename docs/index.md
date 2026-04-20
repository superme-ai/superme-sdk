# SuperMe SDK

Python client for the [SuperMe AI](https://www.superme.ai) API with an OpenAI-compatible interface.

## Installation

```bash
pip install superme-sdk
```

## Quick start

```python
from superme_sdk import SuperMeClient

client = SuperMeClient(api_key="your-superme-api-key")

# ask a question to a user's AI
answer = client.ask("What is your take on product-market fit?", username="ludo")
print(answer)

# look up a profile
profile = client.get_profile("ludo")

# get perspectives from multiple people at once
result = client.perspective_search("What is the best growth channel for B2B?")
print(result["answer"])

# multi-turn conversation
answer1, conv_id = client.ask_with_history(
    [{"role": "user", "content": "What is content marketing?"}],
    username="ludo",
)
answer2, _ = client.ask_with_history(
    [
        {"role": "user", "content": "What is content marketing?"},
        {"role": "assistant", "content": answer1},
        {"role": "user", "content": "How does it differ from SEO?"},
    ],
    username="ludo",
    conversation_id=conv_id,
)
```

## API Reference

- [Client](api/client.md) — main `SuperMeClient` class
- [Models](api/models.md) — response data models
- [Auth](api/auth.md) — token helpers
- [Chat](api/chat.md) — OpenAI-compatible chat interface
- **Services** — [Profiles](api/services/profiles.md), [Conversations](api/services/conversations.md), [Groups](api/services/groups.md), [Companies](api/services/companies.md), [Interviews](api/services/interviews.md), [Content](api/services/content.md), [Social](api/services/social.md)
