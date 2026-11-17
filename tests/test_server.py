import asyncio
import unittest
from unittest.mock import patch

from simplelogin_mcp.client import SimpleLoginError
from simplelogin_mcp.server import server, sl_create_alias, sl_whoami


class ToolRegistrationTests(unittest.TestCase):
    def test_all_tools_are_registered(self):
        tools = asyncio.run(server.list_tools())
        names = {tool.name for tool in tools}
        self.assertEqual(
            names,
            {
                "sl_whoami",
                "sl_list_aliases",
                "sl_get_alias",
                "sl_alias_options",
                "sl_create_alias",
                "sl_create_custom_alias",
                "sl_update_alias",
                "sl_toggle_alias",
                "sl_delete_alias",
                "sl_list_mailboxes",
            },
        )

    def test_create_alias_tool_calls_client(self):
        with patch("simplelogin_mcp.server._client") as mocked:
            mocked.return_value.create_alias.return_value = {"id": 3}
            result = sl_create_alias(note="forum")
        self.assertEqual(result, {"id": 3})
        mocked.return_value.create_alias.assert_called_once_with(
            note="forum", mode=None
        )

    def test_api_error_becomes_tool_error(self):
        with patch("simplelogin_mcp.server._client") as mocked:
            mocked.return_value.whoami.side_effect = SimpleLoginError("bad key")
            with self.assertRaises(Exception) as ctx:
                sl_whoami()
        self.assertIn("bad key", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
