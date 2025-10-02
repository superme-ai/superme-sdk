# SuperMe SDK

Python SDK for SuperMe AI API with OpenAI-compatible interface.

## Features

✅ **OpenAI-Compatible Interface** - Drop-in replacement for OpenAI Python client
✅ **Simple Authentication** - Username/password login with automatic JWT handling
✅ **Conversation Management** - Multi-turn conversations with automatic tracking
✅ **Personalized AI** - Access to SuperMe's personalized AI responses
✅ **Type Hints** - Full type annotations for better IDE support

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

# Initialize client (automatically logs in)
client = SuperMeClient(
    username="your-username",
    password="your-password"
)

# Simple question
answer = client.ask("What are the key principles of growth marketing?")
print(answer)
```

## Usage Examples

### Basic Chat Completion

```python
from superme_sdk import SuperMeClient

client = SuperMeClient(
    username="your-username",
    password="your-password"
)

# Use OpenAI-compatible interface
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "What is product-market fit?"}
    ],
    extra_body={"user": "1"}  # SuperMe user ID for personalization
)

print(response.choices[0].message.content)
```

### Simplified Ask Method

```python
# Simpler interface for single questions
answer = client.ask(
    question="What are growth strategies?",
    user_id="1",
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
    user_id="1"
)
print(response1)

# Continue conversation
messages.append({"role": "assistant", "content": response1})
messages.append({"role": "user", "content": "How do you measure it?"})

response2, conv_id = client.ask_with_history(
    messages=messages,
    user_id="1",
    conversation_id=conv_id
)
print(response2)
```

### Custom Base URL (Self-Hosted)

```python
client = SuperMeClient(
    username="your-username",
    password="your-password",
    base_url="http://localhost:5000"
)
```

### Manual Login

```python
client = SuperMeClient(
    username="your-username",
    password="your-password",
    auto_login=False
)

# Login when needed
token = client.login()
print(f"JWT Token: {token}")
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
    username: str,
    password: str,
    base_url: str = "https://api.superme.ai",
    auto_login: bool = True
)
```

**Parameters:**
- `username` - SuperMe username
- `password` - SuperMe password
- `base_url` - Base URL for SuperMe API (default: `https://api.superme.ai`)
- `auto_login` - Automatically login on initialization (default: `True`)

#### Methods

##### `login() -> str`

Login to SuperMe and get JWT token.

**Returns:** JWT token string

**Raises:** Exception if login fails

##### `ask(question, user_id="1", conversation_id=None, max_tokens=1000, **kwargs) -> str`

Simplified method to ask a question.

**Parameters:**
- `question` - The question to ask
- `user_id` - SuperMe user ID to query (default: `"1"`)
- `conversation_id` - Continue existing conversation (optional)
- `max_tokens` - Maximum tokens in response (default: `1000`)
- `**kwargs` - Additional arguments to pass to OpenAI client

**Returns:** AI response as string

##### `ask_with_history(messages, user_id="1", conversation_id=None, max_tokens=1000, **kwargs) -> tuple[str, str]`

Ask a question with conversation history.

**Parameters:**
- `messages` - List of messages in OpenAI format
- `user_id` - SuperMe user ID to query (default: `"1"`)
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
    extra_body={"user": "1"}
)
```

##### `token`

Get the current JWT token.

**Returns:** JWT token string or `None` if not logged in

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
