"""Return types an API handler may use besides a plain dict (200 JSON)."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileResponse:
    path: Path
    content_type: str = "video/mp4"
    cache: str = "no-cache"


@dataclass
class JsonResponse:
    body: dict
    status: int = 200
