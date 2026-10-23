"""Real clip lengths, read from the MP4 header (stdlib only), and the rule that times stay inside a clip."""
import struct
from pathlib import Path

from .config import log
from .errors import bad_request


def _boxes(data: bytes, start: int, end: int):
    """Yield (type, payload_start, payload_end) for each box between start and end."""
    pos = start
    while pos + 8 <= end:
        size, kind = struct.unpack(">I4s", data[pos:pos + 8])
        header = 8
        if size == 1:
            size, header = struct.unpack(">Q", data[pos + 8:pos + 16])[0], 16
        elif size == 0:
            size = end - pos
        if size < header:
            return
        yield kind, pos + header, min(pos + size, end)
        pos += size


def mp4_duration(path: Path):
    """The clip length in seconds from the moov/mvhd header, or None when it cannot be read (the reason is logged)."""
    try:
        data = Path(path).read_bytes()
        for kind, start, end in _boxes(data, 0, len(data)):
            if kind != b"moov":
                continue
            for inner, inner_start, _ in _boxes(data, start, end):
                if inner == b"mvhd":
                    version = data[inner_start]
                    fmt, offset = (">II", inner_start + 12) if version == 0 else (">IQ", inner_start + 20)
                    timescale, units = struct.unpack(fmt, data[offset:offset + struct.calcsize(fmt)])
                    return units / timescale if timescale else None
        log.warning("No duration found in %s (no moov/mvhd box)", path)
    except (OSError, struct.error, IndexError) as error:
        log.warning("Could not read the duration of %s (missing or truncated MP4 header): %s. Its length is treated as unknown.", path, error)
    return None


def require_within(time_seconds, duration, what: str) -> int:
    """The time as whole seconds, only if it lies between 0 and the clip's length (when the length is known)."""
    if time_seconds < 0:
        raise bad_request(f"{what} cannot be before the start of the clip (0:00).")
    if duration is not None and time_seconds > duration:
        raise bad_request(f"{what} is at {time_seconds}s but the clip is only {duration:.0f}s long. Pick a time inside the clip.")
    return time_seconds
