"""Paths and limits. Tests build their own Settings pointing at a temp directory."""
import logging
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_UPLOAD_BYTES = 500 * 1024 * 1024
SESSION_COOKIE = "tutti_session"
SESSION_DAYS = 30

log = logging.getLogger("tutti")


@dataclass(frozen=True)
class Settings:
    data_dir: Path = ROOT / "data"
    static_dir: Path = ROOT / "static"
    clips_dir: Path = ROOT / "my-clips"
    max_upload_bytes: int = MAX_UPLOAD_BYTES

    @property
    def db_path(self) -> Path:
        return self.data_dir / "tutti.db"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def profile_uploads_dir(self) -> Path:
        return self.uploads_dir / "clips"

    @property
    def submission_uploads_dir(self) -> Path:
        return self.uploads_dir / "submissions"
