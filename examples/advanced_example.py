#!/usr/bin/env python3
"""Advanced example showing features of SuperMe SDK"""

from typing import Dict, Any, Union
from pydantic import BaseModel
from superme_sdk import SuperMeClient


class UserProfile(BaseModel):
    """Example Pydantic model for structured responses"""
    name: str
    age: int
    expertise: list[str]
    location: str


class GrowthStrategy(BaseModel):
    """Example model for growth marketing strategies"""
    strategy_name: str
    description: str
    target_audience: str
    expected_outcome: str
    implementation_difficulty: int  # 1-5 scale


def ask_with_schema(
    client: SuperMeClient,
    messages: list[dict],
    response_format: Union[BaseModel, dict],
    name: str = "response",
    username: str = "ludo",
    **kwargs
):
    """
    Ask a question with structured response format using Pydantic models.
    
    Args:
        client: SuperMe client instance
        messages: List of messages in OpenAI format
        response_format: Pydantic BaseModel class or dict schema
        name: Name for the JSON schema
        username: SuperMe username to query
        **kwargs: Additional arguments to pass to OpenAI client
        
    Returns:
        OpenAI response object
    """
    if isinstance(response_format, BaseModel):
        response_format_dict = response_format.model_json_schema()
    else:
        response_format_dict = response_format

    parse_kwargs: Dict[str, Any] = {
        "model": "gpt-4",
        "messages": messages,
        "extra_body": {
            "username": username,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": name,
                    "schema": response_format_dict,
                    "strict": True,
                },
            },
        },
        **kwargs
    }
    
    return client.chat.completions.create(**parse_kwargs)


def main():
    client = SuperMeClient(
        api_key="YOUR_API_KEY_HERE",
        base_url="https://api.superme.ai",
    )

    print("🚀 SuperMe SDK Advanced Example")
    print("=" * 50)

    # 1. Structured conversation with context
    print("\n1️⃣ Building a conversation with context:")

    conversation = []

    # First question
    q1 = "Who is the founder of Y Combinator?"
    conversation.append({"role": "user", "content": q1})
    response1 = client.chat.completions.create(
        model="gpt-4", messages=conversation, extra_body={"username": "ludo"}, max_tokens=100
    )
    a1 = response1.choices[0].message.content
    conversation.append({"role": "assistant", "content": a1})
    print(f"Q: {q1}")
    print(f"A: {a1}")

    # Follow-up question using context
    q2 = "What companies did he help start?"
    conversation.append({"role": "user", "content": q2})
    response2 = client.chat.completions.create(
        model="gpt-4", messages=conversation, extra_body={"username": "ludo"}, max_tokens=150
    )
    a2 = response2.choices[0].message.content
    conversation.append({"role": "assistant", "content": a2})
    print(f"\nQ: {q2}")
    print(f"A: {a2}")

    # 2. Using raw API access
    print("\n2️⃣ Raw API access:")
    try:
        raw_response = client.raw_request(
            "/mcp", json={"method": "initialize", "params": {}}
        )
        print(f"Response status: {raw_response.status_code}")
        print(f"Response headers: {dict(raw_response.headers)}")
        
        if raw_response.status_code == 200:
            if raw_response.text.strip():
                print(f"MCP initialize response: {raw_response.json()}")
            else:
                print("MCP endpoint returned empty response")
        else:
            print(f"Request failed with status {raw_response.status_code}")
            print(f"Response text: {raw_response.text}")
    except Exception as e:
        print(f"Error making raw request: {e}")

    # 3. Different user profiles
    print("\n3️⃣ Querying different user profiles:")
    usernames = ["ludo", "casey"]
    question = "What are your areas of expertise?"

    for username in usernames:
        answer = client.ask(question, username=username, max_tokens=100)
        print(f"\nUser {username}: {answer[:150]}...")

    # 4. Structured responses with Pydantic models
    print("\n4️⃣ Structured responses with Pydantic models:")
    
    # Example 1: User profile extraction
    print("\n📋 User Profile Extraction:")
    profile_response = ask_with_schema(
        client=client,
        messages=[
            {
                "role": "user",
                "content": "Create a user profile for a 28-year-old marketing expert named Sarah from San Francisco with expertise in growth hacking, content marketing, and social media"
            }
        ],
        response_format=UserProfile,
        name="user_profile",
        username="ludo",
        max_tokens=200
    )
    print(f"Structured profile:\n{profile_response.choices[0].message.content}")
    
    # Example 2: Growth strategy with custom schema
    print("\n🚀 Growth Strategy Analysis:")
    strategy_response = ask_with_schema(
        client=client,
        messages=[
            {
                "role": "user",
                "content": "Provide a growth marketing strategy for a B2B SaaS startup targeting small businesses"
            }
        ],
        response_format=GrowthStrategy,
        name="growth_strategy",
        username="ludo",
        max_tokens=300
    )
    print(f"Structured strategy:\n{strategy_response.choices[0].message.content}")
    
    # Example 3: Using dict schema (backward compatibility)
    print("\n📊 Custom Dict Schema:")
    custom_schema = {
        "type": "object",
        "properties": {
            "tactics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 5}
                    },
                    "required": ["name", "description", "priority"]
                }
            }
        },
        "required": ["tactics"]
    }
    
    tactics_response = ask_with_schema(
        client=client,
        messages=[
            {
                "role": "user",
                "content": "List 3 growth marketing tactics with descriptions and priority levels"
            }
        ],
        response_format=custom_schema,
        name="marketing_tactics",
        username="ludo",
        max_tokens=400
    )
    print(f"Custom schema response:\n{tactics_response.choices[0].message.content}")

    print("\n✅ Advanced example completed!")


if __name__ == "__main__":
    main()
