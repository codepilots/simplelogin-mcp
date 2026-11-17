import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from simplelogin_mcp.client import SimpleLoginClient, SimpleLoginError


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.client = SimpleLoginClient(
            api_key="test-key", base_url="https://example.test/api"
        )

    def test_create_random_alias_sends_auth_header_and_note(self):
        response = io.BytesIO(json.dumps({"alias": {"id": 7}}).encode())
        with patch("simplelogin_mcp.client.urlopen", return_value=response) as mocked:
            result = self.client.create_alias(note="Flickr")
        req = mocked.call_args.args[0]
        self.assertEqual(req.get_header("Authentication"), "test-key")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.full_url, "https://example.test/api/alias/random/new")
        self.assertEqual(json.loads(req.data), {"note": "Flickr"})
        self.assertEqual(result, {"alias": {"id": 7}})

    def test_list_aliases_uses_v2_endpoint_and_query_body(self):
        seen = {}

        def fake_request(method, path, **kwargs):
            seen.update(method=method, path=path, **kwargs)
            return {"aliases": [{"id": 1}], "total": 1}

        self.client.request = fake_request
        result = self.client.list_aliases(query="flickr", page_id=2)
        self.assertEqual(result, [{"id": 1}])
        self.assertEqual(seen["method"], "GET")
        self.assertEqual(seen["path"], "/v2/aliases")
        self.assertEqual(seen["params"], {"page_id": 2})
        self.assertEqual(seen["body"], {"query": "flickr"})

    def test_whoami_uses_user_info_endpoint(self):
        seen = {}
        self.client.request = lambda method, path, **kw: seen.update(
            method=method, path=path
        ) or {"email": "me@example.com"}
        self.assertEqual(self.client.whoami()["email"], "me@example.com")
        self.assertEqual((seen["method"], seen["path"]), ("GET", "/user_info"))

    def test_paths_escape_ids_and_omit_empty_fields(self):
        seen = {}

        def fake_request(method, path, **kwargs):
            seen.update(method=method, path=path, **kwargs)
            return {}

        self.client.request = fake_request
        self.client.update_alias("a/b", note="renamed")
        self.assertEqual(seen["body"], {"note": "renamed"})
        self.assertEqual(seen["path"], "/aliases/a%2Fb")
        seen.clear()
        self.client.toggle_alias(3)
        self.assertEqual(seen["path"], "/aliases/3/toggle")
        self.assertNotIn("body", seen)

    def test_missing_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(SimpleLoginError):
                SimpleLoginClient(api_key=None)

    def test_http_error_detail_does_not_include_key(self):
        error = HTTPError(
            "https://example.test/api/user_info",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"error": "bad api key"}'),
        )
        with patch("simplelogin_mcp.client.urlopen", side_effect=error):
            with self.assertRaises(SimpleLoginError) as ctx:
                self.client.whoami()
        self.assertIn("bad api key", str(ctx.exception))
        self.assertNotIn("test-key", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
