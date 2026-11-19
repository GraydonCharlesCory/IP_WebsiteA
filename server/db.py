"""SQLite access: one short-lived connection per request."""
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA_DIR = Path(__file__).with_name("schema")
SCHEMA_VERSION = 3


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def days_ago(days: float) -> str:
    """Timestamp a given number of days (an hour more) in the past, for seed data."""
    return (datetime.now(timezone.utc) - timedelta(days=days, hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class SchemaOutOfDate(Exception):
    """The data/ folder was created by an older version of Tutti."""


def init_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    try:
        has_tables = conn.execute("SELECT 1 FROM sqlite_master WHERE name='users'").fetchone()
        if has_tables:
            from .migration import migrate
            migrate(conn, db_path)
        for schema_file in sorted(SCHEMA_DIR.glob("*.sql")):
            conn.executescript(schema_file.read_text())
        from .migration import add_columns
        add_columns(conn)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.commit()
    finally:
        conn.close()


def is_empty(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def load_list(text: str) -> list:
    return json.loads(text) if text else []
