# SuperMe SDK

Python client for the [SuperMe AI](https://www.superme.ai) API with an OpenAI-compatible interface.

## Installation

```bash
pip install superme-sdk
```

## Quick start

Get your API key at [superme.ai/settings](https://superme.ai/settings) → **API Keys**.

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

```

## API Reference

- [Client](api/client.md) — main `SuperMeClient` class
- [Models](api/models.md) — response data models (`StreamEvent`, `ChatCompletion`, …)
- [Auth](api/auth.md) — token helpers
- [Chat](api/chat.md) — OpenAI-compatible chat interface
- **Services** — [Profiles](api/services/profiles.md), [Conversations](api/services/conversations.md), [Groups](api/services/groups.md), [Companies & Roles](api/services/companies.md), [Interviews](api/services/interviews.md), [Content](api/services/content.md), [Social](api/services/social.md)
