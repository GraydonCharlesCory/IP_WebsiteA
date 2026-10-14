"""Serving video files with HTTP Range support, and saving uploads to disk."""
import os
import re
import uuid
from pathlib import Path

from .config import log
from .errors import ApiError, bad_request

CHUNK = 256 * 1024
_RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


def parse_range(header: str, size: int):
    """Returns (start, end) inclusive for a single byte range, None when absent; raises ApiError 416."""
    if not header:
        return None
    match = _RANGE.match(header.strip())
    if not match or (not match.group(1) and not match.group(2)):
        return None
    if match.group(1):
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else size - 1
    else:
        start, end = max(size - int(match.group(2)), 0), size - 1
    end = min(end, size - 1)
    if start >= size or start > end:
        raise ApiError(416, "That part of the video is past the end of the file.")
    return start, end


def send_file(handler, path: Path, content_type: str = "video/mp4", cache: str = "no-cache"):
    """Write a file response (200 or 206) on a BaseHTTPRequestHandler."""
    size = path.stat().st_size
    byte_range = parse_range(handler.headers.get("Range"), size)
    start, end = byte_range if byte_range else (0, size - 1)
    handler.send_response(206 if byte_range else 200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Cache-Control", cache)
    handler.send_header("Content-Length", str(max(end - start + 1, 0)))
    if byte_range:
        handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
    handler.end_headers()
    if handler.command == "HEAD":
        return
    try:
        with open(path, "rb") as source:
            source.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = source.read(min(CHUNK, remaining))
                if not chunk:
                    break
                handler.wfile.write(chunk)
                remaining -= len(chunk)
    except (BrokenPipeError, ConnectionResetError):
        log.info("Client closed the connection while streaming %s (normal when seeking)", path.name)


def safe_child(directory: Path, name: str):
    """directory/name if it is a plain file directly inside directory, else None."""
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return None
    path = directory / name
    return path if path.is_file() else None


def save_upload(ctx, directory: Path) -> str:
    """Stream the raw request body to a new file in `directory` and return its file name.

    Requires an mp4 content type and an 'ftyp' box; enforces the size cap. The partial file is
    removed on any failure.
    """
    content_type = (ctx.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if content_type != "video/mp4":
        raise bad_request("Please upload an MP4 video (Content-Type must be video/mp4).")
    length = ctx.content_length
    if length <= 0:
        raise bad_request("The upload was empty. Choose an MP4 file and try again.")
    if length > ctx.settings.max_upload_bytes:
        raise ApiError(413, f"That file is too large. The limit is {ctx.settings.max_upload_bytes // (1024 * 1024)} MB.")
    directory.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.mp4"
    path = directory / name
    try:
        _stream_to(ctx.rfile, path, length)
        _require_ftyp(path)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return name


def _stream_to(rfile, path: Path, length: int) -> None:
    remaining = length
    try:
        with open(path, "wb") as target:
            while remaining > 0:
                chunk = rfile.read(min(CHUNK, remaining))
                if not chunk:
                    raise bad_request("The upload was interrupted before it finished. Please try again.")
                target.write(chunk)
                remaining -= len(chunk)
    except OSError as error:
        log.error("Could not write upload to %s: %s", path, error)
        raise ApiError(500, "The server could not save the upload (disk problem). Check free space and try again.")


def _require_ftyp(path: Path) -> None:
    with open(path, "rb") as source:
        header = source.read(12)
    if header[4:8] != b"ftyp":
        raise bad_request("That file is not a valid MP4 video. Export it as .mp4 and try again.")
