"""Stdlib-only client for the SimpleLogin API.

Endpoints follow https://github.com/simple-login/app/blob/master/docs/api.md.
The API key is sent only in the ``Authentication`` header, never in a URL.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://api.simplelogin.io/api"
TIMEOUT = 20


class SimpleLoginError(RuntimeError):
    """Raised for API or configuration failures."""


class SimpleLoginClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = (
            api_key if api_key is not None else os.environ.get("SIMPLELOGIN_API_KEY", "")
        )
        self.base_url = (
            base_url or os.environ.get("SIMPLELOGIN_API_BASE", DEFAULT_BASE_URL)
        ).rstrip("/")
        if not self.api_key:
            raise SimpleLoginError("SIMPLELOGIN_API_KEY is not set")

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        if clean_params:
            url = f"{url}?{urlencode(clean_params)}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Authentication": self.api_key, "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=TIMEOUT) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            detail = _error_detail(exc.read().decode("utf-8", errors="replace"))
            raise SimpleLoginError(
                f"SimpleLogin {method} {path} failed ({exc.code}): {detail}"
            ) from None
        except URLError as exc:
            raise SimpleLoginError(
                f"SimpleLogin {method} {path} failed: {exc.reason}"
            ) from None
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise SimpleLoginError(
                f"SimpleLogin {method} {path} returned non-JSON data"
            ) from None

    # Account ---------------------------------------------------------------

    def whoami(self) -> Any:
        """GET /api/user_info — validates the API key and returns account info."""
        return self.request("GET", "/user_info")

    # Aliases ---------------------------------------------------------------

    def list_aliases(self, query: str | None = None, page_id: int = 0) -> Any:
        """GET /api/v2/aliases. Query is sent in the JSON body (as the API requires)."""
        payload = self.request(
            "GET",
            "/v2/aliases",
            params={"page_id": page_id},
            body={"query": query} if query else None,
        )
        return _unwrap(payload, "aliases")

    def get_alias(self, alias_id: int | str) -> Any:
        return self.request("GET", f"/aliases/{quote(str(alias_id), safe='')}")

    def alias_options(self, hostname: str | None = None) -> Any:
        """GET /api/v5/alias/options — suffixes needed to create a custom alias."""
        return self.request("GET", "/v5/alias/options", params={"hostname": hostname})

    def create_alias(self, note: str | None = None, mode: str | None = None) -> Any:
        """POST /api/alias/random/new — create a random alias."""
        return self.request(
            "POST",
            "/alias/random/new",
            params={"mode": mode},
            body={"note": note} if note is not None else {},
        )

    def create_custom_alias(
        self,
        alias_prefix: str,
        signed_suffix: str,
        mailbox_ids: list[int],
        note: str | None = None,
        name: str | None = None,
        hostname: str | None = None,
    ) -> Any:
        """POST /api/v3/alias/custom/new — create an alias with a chosen prefix."""
        body: dict[str, Any] = {
            "alias_prefix": alias_prefix,
            "signed_suffix": signed_suffix,
            "mailbox_ids": mailbox_ids,
        }
        if note is not None:
            body["note"] = note
        if name is not None:
            body["name"] = name
        return self.request(
            "POST", "/v3/alias/custom/new", params={"hostname": hostname}, body=body
        )

    def update_alias(
        self,
        alias_id: int | str,
        note: str | None = None,
        name: str | None = None,
    ) -> Any:
        body = {k: v for k, v in {"note": note, "name": name}.items() if v is not None}
        return self.request(
            "PATCH", f"/aliases/{quote(str(alias_id), safe='')}", body=body
        )

    def toggle_alias(self, alias_id: int | str) -> Any:
        """POST /api/aliases/:id/toggle — flips the current state."""
        return self.request("POST", f"/aliases/{quote(str(alias_id), safe='')}/toggle")

    def delete_alias(self, alias_id: int | str) -> Any:
        return self.request("DELETE", f"/aliases/{quote(str(alias_id), safe='')}")

    # Mailboxes -------------------------------------------------------------

    def list_mailboxes(self) -> Any:
        payload = self.request("GET", "/v2/mailboxes")
        return _unwrap(payload, "mailboxes")


def _unwrap(payload: Any, key: str) -> Any:
    if isinstance(payload, dict) and key in payload:
        return payload[key]
    return payload


def _error_detail(raw: str, limit: int = 300) -> str:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:limit] or "no response body"
    if isinstance(data, dict):
        for key in ("error", "message", "detail"):
            if key in data:
                return str(data[key])[:limit]
    return json.dumps(data)[:limit]
