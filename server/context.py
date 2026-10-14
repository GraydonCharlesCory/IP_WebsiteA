"""What an API handler gets: the request, the database, the signed-in user."""
import json
from urllib.parse import parse_qs

from .config import SESSION_COOKIE
from .errors import bad_request

MAX_JSON_BYTES = 1024 * 1024


class Context:
    def __init__(self, handler, settings, conn, params, query_string):
        self.handler = handler
        self.settings = settings
        self.db = conn
        self.params = params
        self.query = {k: v[-1] for k, v in parse_qs(query_string).items()}
        self.user = None
        self.cookie_header = None  # Set-Cookie value, filled by sign-in/out handlers

    @property
    def session_token(self):
        for piece in (self.headers.get("Cookie") or "").split(";"):
            name, _, value = piece.strip().partition("=")
            if name == SESSION_COOKIE:
                return value
        return None

    @property
    def headers(self):
        return self.handler.headers

    @property
    def rfile(self):
        return self.handler.rfile

    @property
    def content_length(self) -> int:
        try:
            return int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise bad_request("The request had an invalid Content-Length header.")

    def json(self) -> dict:
        length = self.content_length
        if length > MAX_JSON_BYTES:
            raise bad_request("That request is too large.")
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw or b"{}")
        except ValueError:
            raise bad_request("The request body must be valid JSON.")
        if not isinstance(data, dict):
            raise bad_request("The request body must be a JSON object.")
        return data

    def query_int(self, name: str, default=None):
        value = self.query.get(name)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            raise bad_request(f"The '{name}' option must be a whole number.")
