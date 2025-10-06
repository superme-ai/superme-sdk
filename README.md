# SuperMe SDK

Python SDK for SuperMe AI. Supports chat completions and MCP protocol.

## Features

- Chat completion support for SuperMe using standard OpenAI format
- Model Context Protocol (MCP) for tool calling and structured interactions
- Simplified ask methods for quick questions
- Multi-turn conversation support with history
- Raw API access for advanced use cases

## Supported Operations

### Chat Completions
- Ask questions to user profiles
- Multi-turn conversations with history
- Structured JSON responses
- OpenAI-compatible interface

### MCP Protocol
- Initialize MCP connections
- List available tools
- Ask questions using MCP ask tool
- List conversations
- Get conversation details

## Installation

```bash
pip install superme-sdk
```

Or install from source:

```bash
git clone https://github.com/superme-ai/superme-sdk.git
cd superme-sdk
pip install -e .
```

## Quick Start

```python
from superme_sdk import SuperMeClient

# Initialize client with API key
client = SuperMeClient(
    api_key="your-api-key",
    base_url="https://api.superme.ai"  # or "http://localhost:8089" for local
)

# Simple question
answer = client.ask("What are the key principles of growth marketing?", username="ludo")
print(answer)
```

## Usage Examples

The SDK includes several example files to demonstrate different use cases:

- `examples/simple_example.py` - Basic usage with simple questions and OpenAI-compatible interface
- `examples/advanced_example.py` - Advanced features including structured conversations and raw API access
- `examples/mcp_example.py` - Complete MCP protocol usage with tool calling and conversation management

### Basic Chat Completion

```python
from openai import OpenAI

# One can use the OpenAI client directly with SuperMe endpoint
client = OpenAI(
    api_key="your-api-key",
    base_url="https://api.superme.ai/sdk" # use /sdk here in case you are directly using the OpenAI client
)

# Standard OpenAI completion
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "What is product-market fit?"}
    ],
    extra_body={"username": "ludo"},  # SuperMe username
    max_tokens=150
)

print(response.choices[0].message.content)
```

### Simplified Ask Method

```python
# Simpler interface for single questions
answer = client.ask(
    question="What are growth strategies?",
    username="ludo",
    max_tokens=500
)
print(answer)
```

### Multi-Turn Conversations

```python
# First message
messages = [
    {"role": "user", "content": "What is product-market fit?"}
]

response1, conv_id = client.ask_with_history(
    messages=messages,
    username="ludo"
)
print(response1)

# Continue conversation
messages.append({"role": "assistant", "content": response1})
messages.append({"role": "user", "content": "How do you measure it?"})

response2, conv_id = client.ask_with_history(
    messages=messages,
    username="ludo",
    conversation_id=conv_id
)
print(response2)
```

### Custom Base URL (Self-Hosted)

```python
client = SuperMeClient(
    api_key="your-api-key",
    base_url="http://localhost:8089"  # Local development server
)
```

### Getting Your API Key

To get your API key:
1. Log into your SuperMe account
2. Navigate to Settings → Account → Account Management → API Keys
3. Generate a new API key
4. Use it in your client initialization

### MCP Protocol Usage

```python
import json
from superme_sdk import SuperMeClient

client = SuperMeClient(
    api_key="your-api-key",
    base_url="https://api.superme.ai"
)

# 1. Initialize MCP connection
init_response = client.raw_request(
    "/mcp", 
    json={"method": "initialize", "params": {}}
)
print(f"Server info: {init_response.json()['serverInfo']}")

# 2. List available tools
tools_response = client.raw_request(
    "/mcp", 
    json={"method": "tools/list", "params": {}}
)
tools = tools_response.json()["tools"]
print(f"Available tools: {[tool['name'] for tool in tools]}")

# 3. Ask a question using MCP ask tool
ask_response = client.raw_request(
    "/mcp",
    json={
        "method": "tools/call",
        "params": {
            "name": "ask",
            "arguments": {
                "username": "ludo",
                "question": "Where do you live?"
            }
        }
    }
)

# Parse the response
ask_result = json.loads(ask_response.json()["content"][0]["text"])
print(f"Question: {ask_result['question']}")
print(f"Response: {ask_result['response']}")
print(f"Conversation ID: {ask_result['conversation_id']}")

# 4. List conversations
conv_response = client.raw_request(
    "/mcp",
    json={
        "method": "tools/call",
        "params": {
            "name": "list_conversations",
            "arguments": {"limit": 5}
        }
    }
)
conversations = json.loads(conv_response.json()["content"][0]["text"])
print(f"Found {len(conversations)} conversations")
```

### Raw API Requests

```python
# Make raw requests to SuperMe API
response = client.raw_request(
    "/mcp",
    json={
        "method": "tools/list"
    }
)
print(response.json())
```

## API Reference

### `SuperMeClient`

Main client class for interacting with SuperMe API.

#### Constructor

```python
SuperMeClient(
    api_key: str,
    base_url: str = "https://api.superme.ai"
)
```

**Parameters:**
- `api_key` - SuperMe API key (get from Settings → Account → Account Management → API Keys)
- `base_url` - Base URL for SuperMe API (default: `https://api.superme.ai`, use `http://localhost:8089` for local development)

#### Methods

##### `ask(question, username="ludo", conversation_id=None, max_tokens=1000, **kwargs) -> str`

Simplified method to ask a question.

**Parameters:**
- `question` - The question to ask
- `username` - SuperMe username to query (default: `"ludo"`)
- `conversation_id` - Continue existing conversation (optional)
- `max_tokens` - Maximum tokens in response (default: `1000`)
- `**kwargs` - Additional arguments to pass to OpenAI client

**Returns:** AI response as string

##### `ask_with_history(messages, username="ludo", conversation_id=None, max_tokens=1000, **kwargs) -> tuple[str, str]`

Ask a question with conversation history.

**Parameters:**
- `messages` - List of messages in OpenAI format
- `username` - SuperMe username to query (default: `"ludo"`)
- `conversation_id` - Continue existing conversation (optional)
- `max_tokens` - Maximum tokens in response (default: `1000`)
- `**kwargs` - Additional arguments to pass to OpenAI client

**Returns:** Tuple of `(response_text, conversation_id)`

##### `raw_request(endpoint, method="POST", **kwargs) -> requests.Response`

Make a raw HTTP request to SuperMe API.

**Parameters:**
- `endpoint` - API endpoint (e.g., `"/mcp/completion"`)
- `method` - HTTP method (default: `"POST"`)
- `**kwargs` - Additional arguments to pass to requests

**Returns:** `requests.Response` object

#### Properties

##### `chat`

Access to OpenAI-compatible chat completions interface.

**Example:**
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}],
    extra_body={"username": "ludo"}
)
```

##### `token`

Get the current API key.

**Returns:** API key string

## Development

### Setup

```bash
git clone https://github.com/superme-ai/superme-sdk.git
cd superme-sdk
pip install -e ".[dev]"
```

### Testing

```bash
pytest
```

### Code Formatting

```bash
black superme_sdk/
ruff check superme_sdk/
```

## Requirements

- Python 3.8+
- `openai>=1.0.0`
- `requests>=2.25.0`

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- GitHub Issues: https://github.com/superme-ai/superme-sdk/issues
- Email: support@superme.ai

## Links

- Homepage: https://superme.ai
- Documentation: https://github.com/superme-ai/superme-sdk
- PyPI: https://pypi.org/project/superme-sdk/
