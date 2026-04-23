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

### `SuperMeClient(api_key, base_url="https://mcp.superme.ai", rest_base_url="https://www.superme.ai", timeout=120.0)`

#### Conversations & agent

| Method | Returns | Description |
|--------|---------|-------------|
| `ask(question, username, *, conversation_id, max_tokens, incognito)` | `str` | Ask a question to a user's SuperMe agent. Returns the answer text. |
| ~~`ask_with_history(messages, username, *, conversation_id, max_tokens, incognito)`~~ | `(str, str\|None)` | **Deprecated** — kept for backward compatibility. Use `ask` with `conversation_id` instead. Only the last user message is sent; the rest of the list is ignored. |
| `ask_my_agent(question, *, conversation_id)` | `dict` | Talk to your own SuperMe AI agent. Returns `{"response": ..., "conversation_id": ...}`. |
| `ask_my_agent_stream(question, *, conversation_id)` | `generator` | Stream your own agent's response. Yields string chunks; final item is `{"conversation_id": ..., "_done": True}`. |
| `list_conversations(*, limit)` | `list[dict]` | List your most recent conversations. |
| `get_conversation(conversation_id)` | `dict` | Fetch a single conversation with all its messages. |

#### Profiles & search

| Method | Returns | Description |
|--------|---------|-------------|
| `get_profile(identifier)` | `dict` | Get a user's public profile. Omit `identifier` for your own profile. |
| `find_user_by_name(name, *, limit)` | `dict` | Search for users by name. |
| `find_users_by_names(names, *, limit_per_name)` | `dict` | Resolve multiple names to SuperMe users in one call. |
| `perspective_search(question)` | `dict` | Get perspectives from multiple experts on a topic. |

#### Group conversations

| Method | Returns | Description |
|--------|---------|-------------|
| `group_converse(participants, topic, *, max_turns, conversation_id)` | `dict` | Start or continue a multi-turn group conversation between multiple users. |
| `group_converse_stream(participants, topic, *, max_turns, conversation_id)` | `generator` | Stream a group conversation. Yields per-perspective dicts; final item has `"_done": True`. |

#### Content

| Method | Returns | Description |
|--------|---------|-------------|
| `add_internal_content(input, *, extended_content, past_instructions)` | `dict` | Save notes or knowledge to your personal library. |
| `update_internal_content(learning_id, *, user_input, extended_content, past_instructions)` | `dict` | Update an existing note. |
| `add_external_content(urls, *, reference, instant_recrawl)` | `dict` | Submit URLs to be crawled and added to your knowledge base. |
| `check_uncrawled_urls(urls)` | `dict` | Check which URLs are not yet in your knowledge base. |

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
| `list_active_roles(*, limit)` | `list[dict]` | List active job roles across all companies. |
| `start_interview(role_id)` | `dict` | Start a background agent interview. Returns `{"interview_id": ..., "status": "preparing"}`. |
| `stream_interview(interview_id)` | `generator` | Stream interview events via SSE. Yields dicts with `event` key; stops at terminal status. |
| `list_my_interviews()` | `list[dict]` | List your interviews. |
| `get_interview_status(interview_id)` | `dict` | Poll interview status and stages. |
| `get_interview_transcript(interview_id)` | `dict` | Get the full transcript for a completed interview. |

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

### Low-level MCP access

```python
# List available tools
tools = client.mcp_list_tools()

# Call a tool directly
profile = client.mcp_tool_call("get_profile", {"username": "ludo"})

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
