"""Command handler functions for the SuperMe CLI.

Each handler corresponds to one subcommand and follows the signature::

    def _cmd_<name>(args: argparse.Namespace, token_file: Path) -> int

Return value is the shell exit code (0 = success).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..auth import load_token, save_token, remove_token, resolve_token
from ..client import SuperMeClient
from .utils import read_token_input, mask_token


def cmd_login(args: argparse.Namespace, token_file: Path) -> int:
    """Save an API token to *token_file*.

    If ``--token`` was not provided on the command line, the user is
    prompted interactively (input is hidden).

    Args:
        args: Parsed CLI arguments.  ``args.token`` may be ``None``.
        token_file: Path where the token will be written.

    Returns:
        0 on success, 1 if the token is empty.
    """
    token = args.token
    if token is None:
        token = read_token_input()

    if not token or not token.strip():
        print("Error: API key is required and cannot be empty.")
        return 1

    save_token(token.strip(), token_file)
    print(f"Logged in. Token saved to {token_file}")
    return 0


def cmd_logout(args: argparse.Namespace, token_file: Path) -> int:
    """Remove the saved API token from *token_file*.

    Args:
        args: Parsed CLI arguments (unused).
        token_file: Path from which the token will be deleted.

    Returns:
        Always 0.
    """
    removed = remove_token(token_file)
    if removed:
        print("Logged out. Token removed.")
    else:
        print("Not logged in (no token found).")
    return 0


def cmd_status(args: argparse.Namespace, token_file: Path) -> int:
    """Print the current authentication status.

    Displays a masked version of the token when one is found.

    Args:
        args: Parsed CLI arguments (unused).
        token_file: Path from which the token is read.

    Returns:
        Always 0.
    """
    token = load_token(token_file)
    if token:
        print(f"Logged in. Token: {mask_token(token)}")
    else:
        print("Not logged in. Run `superme login` to authenticate.")
    return 0


def cmd_ask(args: argparse.Namespace, token_file: Path) -> int:
    """Send a question to SuperMe and print the answer."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        answer = client.ask(
            args.question,
            username=args.username,
            conversation_id=args.conversation_id,
        )
        print(answer)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


def cmd_chat(args: argparse.Namespace, token_file: Path) -> int:
    """Send a chat message, optionally with history or conversation ID."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        messages: list[dict] = []
        if args.history:
            try:
                messages = json.loads(args.history)
            except json.JSONDecodeError as exc:
                print(f"Error: --history is not valid JSON: {exc}")
                return 1
        messages.append({"role": "user", "content": args.message})

        answer, conversation_id = client.ask_with_history(
            messages,
            username=args.username,
            conversation_id=args.conversation_id,
        )
        print(answer)
        if conversation_id:
            print(f"\nconversation_id: {conversation_id}")
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


def cmd_interactive_chat(args: argparse.Namespace, token_file: Path) -> int:
    """Interactive multi-turn conversation loop (REPL)."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    messages: list[dict] = []
    conversation_id: str | None = None
    print(f"Chatting with {args.username}. Type 'quit' or Ctrl-C to exit.\n")
    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                break
            messages.append({"role": "user", "content": user_input})
            try:
                answer, conversation_id = client.ask_with_history(
                    messages,
                    username=args.username,
                    conversation_id=conversation_id,
                )
            except Exception as exc:
                print(f"Error: {exc}")
                messages.pop()  # remove the failed message
                continue
            print(f"SuperMe: {answer}\n")
            messages.append({"role": "assistant", "content": answer})
    finally:
        client.close()
    return 0


def cmd_mcp_tools(args: argparse.Namespace, token_file: Path) -> int:
    """List all available MCP tools."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        tools = client.mcp_list_tools()
        if not tools:
            print("No tools available.")
            return 0
        for tool in tools:
            name = tool.get("name", "?")
            desc = tool.get("description", "")
            print(f"{name}: {desc}")
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


def cmd_mcp_call(args: argparse.Namespace, token_file: Path) -> int:
    """Call an MCP tool by name with JSON arguments."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    try:
        arguments = json.loads(args.args) if args.args else {}
    except json.JSONDecodeError as exc:
        print(f"Error: --args is not valid JSON: {exc}")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        result = client.mcp_tool_call(args.tool_name, arguments)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


# ------------------------------------------------------------------
# Conversations
# ------------------------------------------------------------------


def cmd_conversations(args: argparse.Namespace, token_file: Path) -> int:
    """List recent conversations."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        result = client.list_conversations(limit=args.limit)
        if not result:
            print("No conversations found.")
            return 0
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


def cmd_conversation(args: argparse.Namespace, token_file: Path) -> int:
    """Get a single conversation with all messages."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        result = client.get_conversation(args.conversation_id)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


def cmd_ask_agent(args: argparse.Namespace, token_file: Path) -> int:
    """Ask your own SuperMe AI agent."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        result = client.ask_my_agent(
            args.question, conversation_id=args.conversation_id
        )
        print(result.get("response", ""))
        conv_id = result.get("conversation_id")
        if conv_id:
            print(f"\nconversation_id: {conv_id}")
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


# ------------------------------------------------------------------
# Users
# ------------------------------------------------------------------


def cmd_profile(args: argparse.Namespace, token_file: Path) -> int:
    """Get a user profile."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        result = client.get_profile(args.identifier)
        if not result:
            print("No profile found.")
            return 1
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


def cmd_find_user(args: argparse.Namespace, token_file: Path) -> int:
    """Find users by name."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        result = client.find_user_by_name(args.name, limit=args.limit)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


# ------------------------------------------------------------------
# Search
# ------------------------------------------------------------------


def cmd_search(args: argparse.Namespace, token_file: Path) -> int:
    """Search expert perspectives on a topic."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        result = client.perspective_search(args.question)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


# ------------------------------------------------------------------
# Content
# ------------------------------------------------------------------


def cmd_add_content(args: argparse.Namespace, token_file: Path) -> int:
    """Add notes to your library."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        result = client.add_internal_content(
            args.notes,
            extended_content=args.extended_content,
            past_instructions=args.instructions,
        )
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


def cmd_add_urls(args: argparse.Namespace, token_file: Path) -> int:
    """Add URLs to your knowledge base."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    url_objects = [{"url": u} for u in args.urls]
    client = SuperMeClient(api_key=token)
    try:
        result = client.add_external_content(url_objects)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


def cmd_check_urls(args: argparse.Namespace, token_file: Path) -> int:
    """Check which URLs are not yet indexed."""
    token = resolve_token(token_file=token_file)
    if not token:
        print("Error: No API token found. Run `superme login` first.")
        return 1

    client = SuperMeClient(api_key=token)
    try:
        result = client.check_uncrawled_urls(args.urls)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        client.close()
    return 0


#: Maps subcommand names to their handler functions.
COMMANDS = {
    "login": cmd_login,
    "logout": cmd_logout,
    "status": cmd_status,
    "ask": cmd_ask,
    "chat": cmd_chat,
    "interactive-chat": cmd_interactive_chat,
    "ask-agent": cmd_ask_agent,
    "conversations": cmd_conversations,
    "conversation": cmd_conversation,
    "profile": cmd_profile,
    "find-user": cmd_find_user,
    "search": cmd_search,
    "add-content": cmd_add_content,
    "add-urls": cmd_add_urls,
    "check-urls": cmd_check_urls,
    "mcp-tools": cmd_mcp_tools,
    "mcp-call": cmd_mcp_call,
}
