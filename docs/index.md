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

# OpenAI-style chat completions
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What is PMF?"}],
    username="ludo",
)
print(response.choices[0].message.content)

# Convenience helper
answer = client.ask("What is PMF?", username="ludo")

# Profile lookup
profile = client.get_profile("ludo")
```

## API Reference

- [Client](api/client.md) — main `SuperMeClient` class
- [Models](api/models.md) — response data models
- [Auth](api/auth.md) — token helpers
- [Chat](api/chat.md) — OpenAI-compatible chat interface
- **Services** — [Profiles](api/services/profiles.md), [Conversations](api/services/conversations.md), [Groups](api/services/groups.md), [Companies](api/services/companies.md), [Interviews](api/services/interviews.md), [Content](api/services/content.md), [Social](api/services/social.md)
