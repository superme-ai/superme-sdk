# SuperMe SDK

Python SDK for the SuperMe API. Ask questions to professionals, search expert perspectives, manage your knowledge library, and interact via MCP.

## Documentation

See our latest documentation here for usage: [SuperMe SDK documentation](https://sdkdocs.superme.ai/)


## Installation

```bash
pip install superme-sdk
```

Or with uv:

```bash
uv pip install superme-sdk
```

From source:

```bash
git clone https://github.com/superme-ai/superme-sdk.git
cd superme-sdk
uv sync
source .venv/bin/activate
```

## Authentication

Get your API key at [superme.ai/settings](https://superme.ai/settings) → API Keys.

**Option 1 — environment variable (recommended)**
```bash
export SUPERME_API_KEY=your_api_key_here
```

**Option 2 — `.env` file**
```bash
cp .env.example .env
# edit .env and fill in your key
```
Then load it before running:
```python
from dotenv import load_dotenv
load_dotenv()
```
Or source it in your shell:
```bash
set -a && source .env && set +a
```

Pass the key to the client:
```python
import os
from superme_sdk import SuperMeClient

client = SuperMeClient(api_key=os.environ["SUPERME_API_KEY"])
```

## Quick Start

```python
import os
from superme_sdk import SuperMeClient

client = SuperMeClient(api_key=os.environ["SUPERME_API_KEY"])

# Ask a question
answer = client.ask("What are the key principles of growth marketing?", username="ludo")
print(answer)

# Multi-turn conversation
messages = [{"role": "user", "content": "What is product-market fit?"}]
response, conv_id = client.ask_with_history(messages, username="ludo")
messages.append({"role": "assistant", "content": response})
messages.append({"role": "user", "content": "How do you measure it?"})
response2, _ = client.ask_with_history(messages, username="ludo", conversation_id=conv_id)
```

## Running Examples

```bash
export SUPERME_API_KEY=your_api_key_here

python examples/simple_example.py
python examples/advanced_example.py
python examples/mcp_example.py
```

Or with dotenv:
```bash
cp .env.example .env   # fill in your key
set -a && source .env && set +a
python examples/simple_example.py
```

## Development

```bash
make install       # set up virtualenv with dev deps (run once)

make test          # unit tests — mocked, no network, always fast
make test-live     # e2e tests — hit real endpoints (requires SUPERME_API_KEY)
make test-cov      # unit tests with coverage report
make check         # lint + typecheck + unit tests
make fmt           # auto-format with ruff
```

**Unit tests** run on every commit via CI and need no credentials.

**Live / e2e tests** hit the real production API — use them to verify integration changes end-to-end:

```bash
cp .env.example .env   # fill in SUPERME_API_KEY
make test-live
```

## API Reference

### `SuperMeClient(api_key, base_url="https://mcp.superme.ai", rest_base_url="https://www.superme.ai", partner_base_url="https://api.superme.ai", timeout=120.0)`

#### Conversations & agent

| Method | Returns | Description |
|--------|---------|-------------|
| `ask(question, username, *, conversation_id, max_tokens, incognito)` | `str` | Ask a question to a user's SuperMe agent. Returns the answer text. |
| `ask_stream(question, username, *, conversation_id)` | `generator` | Stream a user's agent answer via SSE (`POST /partner/ask`). Yields chunk dicts (`content` / `tool` / `done` / `error`); stops after `done`/`error`. |
| ~~`ask_with_history(messages, username, *, conversation_id, max_tokens, incognito)`~~ | `(str, str\|None)` | **Deprecated** — kept for backward compatibility. Use `ask` with `conversation_id` instead. Only the last user message is sent; the rest of the list is ignored. |
| `ask_my_agent(question, *, conversation_id)` | `dict` | Talk to your own SuperMe AI agent. Returns `{"response": ..., "conversation_id": ...}`. |
| `ask_my_agent_stream(question, *, conversation_id)` | `generator` | Stream your own agent's turn via SSE (`POST /partner/agent`). Yields typed turn-event dicts (`turn_started`, `content`, `tool_call`, `turn_completed`, ...); stops at a terminal event. |

`AsyncSuperMeClient` mirrors these: `ask_stream` / `ask_my_agent_stream` are async generators (`async for`), and `ask_my_agent`, `get_profile`, `get_user_details`, `find_user_by_name`, `find_users_by_names`, and `find_users_on_topic` are awaitable.

#### Profiles & search

| Method | Returns | Description |
|--------|---------|-------------|
| `get_profile(identifier=None)` | `dict` | Get a user's public profile card by user ID, username, or name. Omit `identifier` for your own profile. |
| `get_user_details(identifier)` | `dict` | Read a user's **full** profile — un-truncated summary plus structured work experience, education, and skills (deeper than `get_profile`'s search card). |
| `find_user_by_name(name, *, limit)` | `dict` | Search for users by name. |
| `find_users_by_names(names, *, limit_per_name)` | `dict` | Resolve multiple names to SuperMe users in one call. |
| `find_users_on_topic(question, *, max_results, excluded_user_ids)` | `dict` | Find SuperMe users who are experts on a topic. |

#### Social accounts

| Method | Returns | Description |
|--------|---------|-------------|
| `get_connected_accounts()` | `dict` | List connected social accounts and blogs. |
| `connect_social(platform, handle, *, token)` | `dict` | Connect a social platform account (medium, substack, x, instagram, youtube, beehiiv, google_drive, linkedin, github, notion). |
| `disconnect_social(platform)` | `dict` | Disconnect a social platform account. |
| `connect_blog(url)` | `dict` | Connect a custom blog or website. |
| `disconnect_blog(url)` | `dict` | Disconnect a custom blog. |

#### Interviews

| Method | Returns | Description |
|--------|---------|-------------|
| `start_interview(role_id)` | `dict` | Start a background agent interview. Returns `{"interview_id": ..., "status": "preparing"}`. |
| `stream_interview(interview_id)` | `generator` | Stream interview events via SSE. Yields dicts with `event` key; stops at terminal status. |
| `list_my_interviews()` | `list[dict]` | List your interviews. |
| `get_interview_status(interview_id)` | `dict` | Poll interview status and stages. |
| `get_interview_transcript(interview_id)` | `dict` | Get the full transcript for a completed interview. |

#### Provisioning

| Method | Returns | Description |
|--------|---------|-------------|
| `provision_create(community_id, *, name, linkedin_url, contact_email, notes, socials, external_urls)` | `ProvisionCreateResponse` | Provision a single community member. Returns a `provision` record with `user_id`, `token`, `claim_url`, and `status`. |
| `provision_create_batch(community_id, profiles)` | `list[dict]` | Provision multiple members concurrently (up to 10 in flight). Results match the order of `profiles`; failed items have an `"error"` key instead of `"provision"`. |
| `provision_send_invites(community_id, user_ids)` | `ProvisionInviteResponse` | Send invite emails to provisioned members. Returns `sent`, `skipped`, and `failed` lists. |
| `provision_list(community_id)` | `ProvisionListResponse` | List all provisions for a community. Returns `provisions` and `count`. |
| `provision_get(community_id, user_id)` | `ProvisionRecord` | Fetch a single provisioned member by user ID. |

#### OpenAI-compatible interface

| Method | Returns | Description |
|--------|---------|-------------|
| `chat.completions.create(messages, model, *, username, conversation_id, ...)` | `ChatCompletion` | OpenAI-compatible chat completion backed by the SuperMe MCP server. |

#### Low-level

| Method | Returns | Description |
|--------|---------|-------------|
| `mcp_tool_call(tool_name, arguments)` | `dict` | Call any MCP tool by name. |
| `mcp_list_tools()` | `list[dict]` | List all available MCP tools. |
| `raw_request(method, params)` | `dict` | Raw MCP JSON-RPC request. |

### OpenAI-compatible interface

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What is PLG?"}],
    username="ludo",
)
print(response.choices[0].message.content)
print(response.metadata["conversation_id"])
```

### Streaming

Stream tokens as they're generated over SSE. `ask_stream` targets another
user's agent; `ask_my_agent_stream` targets your own.

```python
# Stream a question to a user's agent
conversation_id = None
for chunk in client.ask_stream("What is PMF?", username="ludo"):
    if chunk["type"] == "content":
        print(chunk["text"], end="", flush=True)
    elif chunk["type"] == "done":
        conversation_id = chunk["conversation_id"]

# Stream your own agent (richer turn events: tool calls, messages, ...)
for evt in client.ask_my_agent_stream("Summarise my last 3 posts"):
    if evt["type"] == "content":
        print(evt["content"], end="", flush=True)
```

Async (`AsyncSuperMeClient`):

```python
async with AsyncSuperMeClient(api_key=API_KEY) as client:
    async for chunk in client.ask_stream("What is PMF?", username="ludo"):
        if chunk["type"] == "content":
            print(chunk["text"], end="", flush=True)
```

### Low-level MCP access

```python
# List available tools
tools = client.mcp_list_tools()

# Call a tool directly
profiles = client.mcp_tool_call("user_profile_search", {"identifier": "ludo"})

# Raw JSON-RPC
result = client.raw_request("tools/list")
```

## MCP Setup

Connect the SuperMe MCP server (`https://mcp.superme.ai`) to your AI client.

### Claude Desktop

`~/.config/Claude/claude_desktop_config.json` (Linux) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "superme": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.superme.ai", "--header", "Authorization: Bearer YOUR_TOKEN"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add --transport http --scope user superme https://mcp.superme.ai \
  --header "Authorization: Bearer YOUR_TOKEN"
```

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "superme": {
      "url": "https://mcp.superme.ai",
      "headers": { "Authorization": "Bearer YOUR_TOKEN" }
    }
  }
}
```

### VS Code (Copilot)

`.vscode/mcp.json` in your workspace:

```json
{
  "inputs": [
    { "id": "superme-token", "type": "promptString", "description": "SuperMe API Token" }
  ],
  "servers": {
    "superme": {
      "type": "http",
      "url": "https://mcp.superme.ai",
      "headers": { "Authorization": "Bearer ${input:superme-token}" }
    }
  }
}
```

VS Code will prompt once for the token and cache it.

### Quick install (Claude Desktop + Cursor)

```bash
curl -fsSL https://superme.ai/mcp-install.sh | SUPERME_TOKEN="your-token" bash
```

## Network Guidelines

See [network_guidelines/](network_guidelines/) for content evaluation and moderation rules used by the SuperMe network.

## License

MIT
