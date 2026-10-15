"""Test helpers: a throwaway seeded server on a free port and a cookie-keeping client."""
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from server.app import make_server
from server.config import Settings
from server.setup import prepare_data

FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + bytes(range(256)) * 8


class Client:
    def __init__(self, port):
        self.port, self.cookie = port, None

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = dict(headers or {})
        if self.cookie:
            headers["Cookie"] = self.cookie
        if isinstance(body, (dict, list)):
            body, headers["Content-Type"] = json.dumps(body), "application/json"
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        set_cookie = response.getheader("Set-Cookie")
        if set_cookie:
            pair = set_cookie.split(";")[0]
            self.cookie = pair if pair.split("=", 1)[1] else None
        conn.close()
        return response.status, data, response

    def json(self, method, path, body=None, headers=None):
        status, data, _ = self.request(method, path, body, headers)
        return status, json.loads(data)

    def sign_in(self, handle):
        status, data = self.json("POST", "/api/sign-in", {"email": f"{handle.replace('-', '.')}@tutti.demo", "password": "demo"})
        assert status == 200, data
        return data["user"]

    def upload(self, path, payload=FAKE_MP4, content_type="video/mp4"):
        return self.json("POST", path, payload, {"Content-Type": content_type})


class ServerTestCase(unittest.TestCase):
    """Starts one seeded server per test class."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        clips = root / "my-clips"
        clips.mkdir()
        (clips / "leo-marquez-2.mp4").write_bytes(FAKE_MP4)
        cls.settings = Settings(data_dir=root / "data", clips_dir=clips, max_upload_bytes=1024 * 1024)
        prepare_data(cls.settings)
        cls.server = make_server(cls.settings, 0)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls._tmp.cleanup()

    def client(self, handle=None):
        client = Client(self.port)
        if handle:
            client.sign_in(handle)
        return client


def find_opportunity(client, title_part, **query):
    """The first opportunity whose title contains `title_part`, found through the search API."""
    from urllib.parse import urlencode
    status, data = client.json("GET", "/api/opportunities?" + urlencode(query))
    assert status == 200, data
    matches = [o for o in data["opportunities"] if title_part in o["title"]]
    assert matches, f"no opportunity titled like {title_part!r}"
    return matches[0]
