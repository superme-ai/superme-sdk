# SuperMe SDK

Python SDK for the SuperMe API. Ask questions to professionals, search expert perspectives, manage your knowledge library, and interact via MCP.

## Installation

```bash
pip install superme-sdk
```

From source:

```bash
git clone https://github.com/superme-ai/superme-sdk.git
cd superme-sdk
pip install -e .
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

## Dev Setup

```bash
git clone https://github.com/superme-ai/superme-sdk.git
cd superme-sdk
pip install -e ".[dev]"
```

Run tests:
```bash
pytest                  # all tests
pytest --cov=superme_sdk
```

## Running Examples

```bash
# Option 1 — env var
export SUPERME_API_KEY=your_api_key_here

# Option 2 — .env file (python-dotenv is included by default)
cp .env.example .env   # fill in your key

python examples/simple_example.py
python examples/advanced_example.py
python examples/mcp_example.py
```

## API Reference

### `SuperMeClient(api_key, base_url="https://mcp.superme.ai", timeout=120.0)`

| Method | Returns | Description |
|--------|---------|-------------|
| `ask(question, username, ...)` | `str` | Ask a question about a user |
| `ask_with_history(messages, username, ...)` | `(str, str\|None)` | Ask with conversation history |
| `ask_my_agent(question, *, conversation_id)` | `dict` | Talk to your own SuperMe AI |
| `list_conversations(*, limit)` | `list[dict]` | List recent conversations |
| `get_conversation(conversation_id)` | `dict` | Get conversation with messages |
| `get_profile(identifier)` | `dict` | Get user profile |
| `find_user_by_name(name, *, limit)` | `dict` | Search users by name |
| `find_users_by_names(names, *, limit_per_name)` | `dict` | Batch resolve names to users |
| `perspective_search(question)` | `dict` | Get multi-expert perspectives |
| `add_internal_content(input, ...)` | `dict` | Add notes to your library |
| `update_internal_content(learning_id, ...)` | `dict` | Update a library note |
| `add_external_content(urls, ...)` | `dict` | Add URLs to knowledge base |
| `check_uncrawled_urls(urls)` | `dict` | Check which URLs are unindexed |
| `chat.completions.create(messages, model, ...)` | `ChatCompletion` | OpenAI-compatible interface |
| `mcp_tool_call(tool_name, arguments)` | `dict` | Call any MCP tool by name |
| `mcp_list_tools()` | `list[dict]` | List all available MCP tools |
| `raw_request(method, params)` | `dict` | Raw MCP JSON-RPC request |

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

### MCP tools via SDK

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
