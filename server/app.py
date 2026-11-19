"""HTTP entry point: dispatches /api and /media routes, then falls back to static files."""
import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from . import auth, db
from .api import ROUTER
from .config import Settings, log
from .context import Context
from .errors import ApiError
from .responses import FileResponse, JsonResponse
from .media import send_file
from .static import serve_static

_NOT_FOUND_API = "That address does not exist. Check the API list in the README."


def make_handler(settings: Settings):
    class TuttiHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "Tutti"

        def log_message(self, fmt, *args):
            log.info("%s %s", self.address_string(), fmt % args)

        def do_GET(self): self._dispatch()
        def do_HEAD(self): self._dispatch()
        def do_POST(self): self._dispatch()
        def do_PUT(self): self._dispatch()
        def do_DELETE(self): self._dispatch()

        def _dispatch(self):
            parts = urlsplit(self.path)
            path = unquote(parts.path)
            conn = db.connect(settings.db_path)
            try:
                self._handle(conn, path, parts.query)
            except ApiError as error:
                self._send_error(error.status, error.message)
            except Exception:
                log.exception("Unhandled error on %s %s", self.command, self.path)
                self._send_error(500, "Something went wrong on the server. Check the server log for details.")
            finally:
                conn.close()

        def _handle(self, conn, path, query_string):
            method = "GET" if self.command == "HEAD" else self.command
            if not path.startswith(("/api/", "/media/")):
                if method == "GET" and serve_static(self, settings.static_dir, path):
                    return
                raise ApiError(404, "Page not found.")
            func, found = ROUTER.match(method, path)
            if func is None:
                if found:
                    raise ApiError(405, f"Use {' or '.join(found)} for this address.")
                raise ApiError(404, _NOT_FOUND_API)
            ctx = Context(self, settings, conn, found, query_string, path)
            ctx.user = auth.user_for_token(conn, ctx.session_token)
            self._send_result(func(ctx), ctx)

        def _send_result(self, result, ctx):
            if isinstance(result, FileResponse):
                send_file(self, result.path, result.content_type, result.cache)
                return
            if not isinstance(result, JsonResponse):
                result = JsonResponse(result)
            self._send_json(result.status, result.body, ctx.cookie_header)

        def _send_error(self, status, message):
            self.close_connection = True  # a request body may be unread
            self._send_json(status, {"error": message})

        def _send_json(self, status, body, cookie=None):
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            if self.close_connection:
                self.send_header("Connection", "close")
            if cookie:
                self.s end_header("Set-Cookie", cookie)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)

    return TuttiHandler


def make_server(settings: Settings, port: int, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(settings))
    server.daemon_threads = True
    return server
