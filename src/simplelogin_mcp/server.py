"""MCP tool surface for SimpleLogin alias management."""

from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .client import SimpleLoginClient, SimpleLoginError

server = MCPServer(
    "simplelogin",
    instructions="Manage email aliases through the SimpleLogin API.",
)


def _client() -> SimpleLoginClient:
    return SimpleLoginClient(api_key=os.environ.get("SIMPLELOGIN_API_KEY"))


def tool(name: str, description: str) -> Callable[[Callable], Callable]:
    """Register a tool and turn API failures into clean MCP tool errors."""

    def register(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            except SimpleLoginError as exc:
                raise ToolError(str(exc)) from None

        return server.tool(name=name, description=description)(wrapped)

    return register


@tool(
    name="sl_whoami",
    description="Check the configured API key and return the SimpleLogin account email.",
)
def sl_whoami() -> Any:
    return _client().whoami()


@tool(
    name="sl_list_aliases",
    description="List aliases (newest first), optionally filtered by a search query.",
)
def sl_list_aliases(query: str | None = None, page_id: int = 0) -> Any:
    return _client().list_aliases(query=query, page_id=page_id)


@tool(name="sl_get_alias", description="Get one SimpleLogin alias by numeric ID.")
def sl_get_alias(alias_id: int) -> Any:
    return _client().get_alias(alias_id)


@tool(
    name="sl_alias_options",
    description=(
        "Get the signed suffixes and mailboxes available for creating a custom "
        "alias. Pass hostname (e.g. 'example.com') for a site-specific suffix."
    ),
)
def sl_alias_options(hostname: str | None = None) -> Any:
    return _client().alias_options(hostname=hostname)


@tool(
    name="sl_create_alias",
    description="Create a new random alias. note is a label for your own use.",
)
def sl_create_alias(note: str | None = None, mode: str | None = None) -> Any:
    return _client().create_alias(note=note, mode=mode)


@tool(
    name="sl_create_custom_alias",
    description=(
        "Create a custom alias with a chosen prefix. Get signed_suffix and "
        "mailbox_ids from sl_alias_options first."
    ),
)
def sl_create_custom_alias(
    alias_prefix: str,
    signed_suffix: str,
    mailbox_ids: list[int],
    note: str | None = None,
    name: str | None = None,
    hostname: str | None = None,
) -> Any:
    return _client().create_custom_alias(
        alias_prefix=alias_prefix,
        signed_suffix=signed_suffix,
        mailbox_ids=mailbox_ids,
        note=note,
        name=name,
        hostname=hostname,
    )


@tool(
    name="sl_update_alias",
    description="Update the note and/or name of an existing SimpleLogin alias.",
)
def sl_update_alias(
    alias_id: int,
    note: str | None = None,
    name: str | None = None,
) -> Any:
    return _client().update_alias(alias_id, note=note, name=name)


@tool(
    name="sl_toggle_alias",
    description="Flip a SimpleLogin alias between enabled and disabled by ID.",
)
def sl_toggle_alias(alias_id: int) -> Any:
    return _client().toggle_alias(alias_id)


@tool(
    name="sl_delete_alias",
    description="Delete a SimpleLogin alias by ID. This cannot be undone.",
)
def sl_delete_alias(alias_id: int) -> Any:
    return _client().delete_alias(alias_id)


@tool(
    name="sl_list_mailboxes",
    description="List the mailboxes available for SimpleLogin aliases.",
)
def sl_list_mailboxes() -> Any:
    return _client().list_mailboxes()


def main() -> None:
    if not os.environ.get("SIMPLELOGIN_API_KEY"):
        raise SimpleLoginError(
            "SIMPLELOGIN_API_KEY is not set; launch via bin/simplelogin-mcp "
            "to read it from 1Password"
        )
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
