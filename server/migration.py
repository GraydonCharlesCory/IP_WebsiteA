"""Additive v3 migration. Backup first; retain every user, upload, message and application."""
import sqlite3

from .config import log


def add_columns(conn):
    additions = {
        "users": {"education": "TEXT NOT NULL DEFAULT '[]'", "certifications": "TEXT NOT NULL DEFAULT '[]'"},
        "auditions": {"blind_review": "INTEGER NOT NULL DEFAULT 1", "rubric": "TEXT NOT NULL DEFAULT '[\"tone\",\"rhythm\",\"technique\",\"musicality\",\"preparation\"]'", "school_id": "INTEGER REFERENCES schools(id)"},
        "reviews": {"rubric_scores": "TEXT NOT NULL DEFAULT '{}'"},
    }
    for table, fields in additions.items():
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
        for name, definition in fields.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
    conn.execute("CREATE TRIGGER IF NOT EXISTS immutable_blind BEFORE UPDATE OF blind_review ON auditions "
                 "WHEN NEW.blind_review != OLD.blind_review BEGIN SELECT RAISE(ABORT, 'Review mode is immutable'); END")


def migrate(conn, path):
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version == 3:
        return
    if version != 2:
        from .db import SchemaOutOfDate
        raise SchemaOutOfDate(f"Unsupported schema {version}. Preserve {path}; migrate a copy to version 2 first. Do not reset existing data.")
    backup = path.with_suffix(".pre-v3.sqlite")
    if not backup.exists():
        with sqlite3.connect(str(backup)) as target:
            conn.backup(target)
    conn.execute("PRAGMA foreign_keys=OFF")
    try:
        conn.execute("BEGIN")
        for table, old, new in (
            ("users", "'musician','director'", "'musician','director','school'"),
            ("auditions", "'audition','gig'", "'audition','gig','grant','residency','college_audition','summer_camp'"),
        ):
            sql = conn.execute("SELECT sql FROM sqlite_master WHERE name=?", (table,)).fetchone()[0]
            sql = sql.replace(f"CREATE TABLE {table}", f"CREATE TABLE {table}_v3", 1).replace(old, new)
            conn.execute(sql)
            conn.execute(f"INSERT INTO {table}_v3 SELECT * FROM {table}")
            conn.execute(f"DROP TABLE {table}")
            conn.execute(f"ALTER TABLE {table}_v3 RENAME TO {table}")
        if conn.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("Migration found invalid references; restore the pre-v3 backup and inspect the database.")
        conn.commit()
        log.info("Migrated v2 data without reset; backup at %s", backup)
    except Exception:
        conn.rollback()
        log.exception("Migration failed; existing data retained. Inspect pre-v3 backup at %s", backup)
        raise
    finally:
        conn.execute("PRAGMA foreign_keys=ON")
