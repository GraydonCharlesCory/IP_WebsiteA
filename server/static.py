"""Serves the front-end files from static/ (pages at the site root, assets under /static/)."""
import mimetypes
from pathlib import Path

from .media import send_file, safe_child

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("text/javascript", ".js")

PAGES = {"/": "index.html"}


def resolve_static(static_dir: Path, url_path: str):
    """Maps a URL path to a file inside static_dir, or None."""
    if url_path in PAGES:
        candidate = static_dir / PAGES[url_path]
        return candidate if candidate.is_file() else None
    parts = [p for p in url_path.split("/") if p]
    if not parts or any(p in ("..", ".") or p.startswith(".") for p in parts):
        return None
    if parts[0] == "static":
        candidate = static_dir.joinpath(*parts[1:])
    elif len(parts) == 1 and parts[0].endswith(".html"):
        candidate = static_dir / parts[0]
    else:
        return None
    return candidate if candidate.is_file() and static_dir.resolve() in candidate.resolve().parents else None


def serve_static(handler, static_dir: Path, url_path: str) -> bool:
    path = resolve_static(static_dir, url_path)
    if path is None:
        return False
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if content_type.startswith(("text/", "application/json")):
        content_type += "; charset=utf-8"
    send_file(handler, path, content_type, cache="no-cache")
    return True
