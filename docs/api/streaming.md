# Streaming events

`ask(stream=True)` yields partner chunks over SSE. At runtime each chunk is a
plain `dict` — discriminate on `["type"]`. The stream stops after `done` or
`error`.

| `type` | fields | meaning |
|--------|--------|---------|
| `content` | `text: str` | a piece of the answer text |
| `tool` | `label: str` | a tool the agent is calling (e.g. `"Searching the web"`) |
| `done` | `conversation_id: str` | finished — pass `conversation_id` back to continue the thread |
| `error` | `message: str` | the turn failed |

```python
for chunk in client.ask("What is PMF?", username="ludo", stream=True):
    if chunk["type"] == "content":
        print(chunk["text"], end="", flush=True)
    elif chunk["type"] == "done":
        conversation_id = chunk["conversation_id"]
```

For static typing, import `PartnerStreamChunk` (a union of `TypedDict`s) and its
members from `superme_sdk`:

```python
from superme_sdk import PartnerStreamChunk, ContentChunk, ToolChunk, DoneChunk, ErrorChunk
```
