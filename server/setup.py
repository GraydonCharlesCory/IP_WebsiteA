"""Prepare the data directory and database (optionally wiping it first)."""
import shutil

from . import db
from .config import Settings, log
from .seed import seed


def prepare_data(settings: Settings, reset: bool = False) -> None:
    if reset and settings.data_dir.exists():
        shutil.rmtree(settings.data_dir)
        log.info("Wiped %s", settings.data_dir)
    settings.profile_uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.submission_uploads_dir.mkdir(parents=True, exist_ok=True)
    db.init_schema(settings.db_path)
    conn = db.connect(settings.db_path)
    try:
        fresh_demo = db.is_empty(conn)
        if fresh_demo:
            seed(conn, settings.clips_dir)
        from .seed_v3 import seed_v3
        seed_v3(conn)
        from .seed_discovery import seed_discovery
        seed_discovery(conn, fresh_demo)
    finally:
        conn.close()
