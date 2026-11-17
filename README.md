# simplelogin-mcp

A stdio MCP server that exposes SimpleLogin alias management as tools for
Hermes (or any MCP client). It is a thin wrapper around SimpleLogin's public
REST API; the API key stays in the server subprocess environment and is never
written to a config file, chat, or the repository.

API endpoints follow the upstream docs:
<https://github.com/simple-login/app/blob/master/docs/api.md>

## Tools

| Tool | Arguments | Description |
| --- | --- | --- |
| `sl_whoami` | — | Validate the API key and return account info (`GET /user_info`). |
| `sl_list_aliases` | `query?`, `page_id=0` | List aliases, newest first (`GET /v2/aliases`). |
| `sl_get_alias` | `alias_id` | Fetch a single alias by numeric ID. |
| `sl_alias_options` | `hostname?` | Get signed suffixes and mailbox IDs needed for a custom alias (`GET /v5/alias/options`). Pass a site hostname for site-specific suffixes. |
| `sl_create_alias` | `note?`, `mode?` | Create a random alias (`POST /alias/random/new`). `mode` may be `uuid`, `word`, or omitted for the default. |
| `sl_create_custom_alias` | `alias_prefix`, `signed_suffix`, `mailbox_ids`, `note?`, `name?`, `hostname?` | Create a chosen-prefix alias (`POST /v3/alias/custom/new`). Get `signed_suffix` and `mailbox_ids` from `sl_alias_options` first. |
| `sl_update_alias` | `alias_id`, `note?`, `name?` | Change an alias's note and/or name. |
| `sl_toggle_alias` | `alias_id` | Flip an alias between enabled and disabled. |
| `sl_delete_alias` | `alias_id` | Delete an alias. This cannot be undone. |
| `sl_list_mailboxes` | — | List available mailboxes (`GET /v2/mailboxes`). |

Errors from the API are returned as clean MCP tool errors (no raw stack traces
or echoed credentials). Every ID used in a URL path is URL-escaped.

## Install

Requires Python 3.11+ and the MCP SDK.

```bash
cd /path/to/simplelogin-mcp
uv venv
uv pip install -e .
```

## Credentials

The client reads `SIMPLELOGIN_API_KEY` at request time. The recommended
launcher is `bin/simplelogin-mcp`, which fetches the key from 1Password with
`op` at startup and exports it only into the child process:

1. Create a 1Password item holding the SimpleLogin API key.
2. Set `SIMPLELOGIN_OP_ITEM` to its item ID and, optionally,
   `SIMPLELOGIN_OP_VAULT` to its vault name (default: `Hermes Agent`).
   `~/.hermes/.env` is sourced so non-interactive MCP processes see these.
3. Launch through the wrapper: `bin/simplelogin-mcp`.

The wrapper probes common field labels (`password`, `credential`, `api key`,
`token`) and falls back to a JSON field scan, so the exact label does not
matter. If you rotate the key in 1Password, restart the MCP server process to
pick it up — no file edits needed.

You can also bypass 1Password by exporting `SIMPLELOGIN_API_KEY` yourself, but
never place it in a committed file or paste it into chat.

`SIMPLELOGIN_API_BASE` optionally overrides the default
`https://api.simplelogin.io/api` (useful for a local mock).

## Hermes registration

```bash
hermes mcp add simplelogin --command /absolute/path/to/simplelogin-mcp/bin/simplelogin-mcp
hermes mcp test simplelogin
```

Restart Hermes after adding or changing the server so the tools load into your
session. Other MCP clients can use the same command over stdio.

## Development

```bash
uv pip install -e . pytest
.venv/bin/python -m pytest -q
```

Unit tests mock HTTP and never require a live key. They cover auth headers,
endpoint paths, request bodies, error detail scrubbing, and tool registration.

## Security notes

- The API key is sent only in the `Authentication` header to the configured
  API base; it never appears in a URL or log message.
- No credential, item ID, or vault name is baked into the source; all are
  supplied via environment variables at runtime.
- `sl_delete_alias` and `sl_toggle_alias` change live state — check the target
  alias before calling them.

## Licence

MIT — see [LICENSE](LICENSE).
