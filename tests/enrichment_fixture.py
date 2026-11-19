"""Populated round-four database assembled without the enrichment read paths."""
import json

from server import db
from server.seed import seed
from server.seed_v3 import seed_v3
from server.seed_discovery import seed_discovery
from server.setup import prepare_data


def snapshot(conn):
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    return {table: [tuple(r) for r in conn.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
            for table in tables}


def populated_fixture(settings):
    settings.data_dir.mkdir(parents=True)
    db.init_schema(settings.db_path)
    with db.connect(settings.db_path) as conn:
        seed(conn, settings.clips_dir)
        seed_v3(conn)
        seed_discovery(conn, True)
        school_id = conn.execute("SELECT id FROM schools WHERE name='Lakefront Conservatory'").fetchone()[0]
        education = [{"school_id": school_id, "school": "Lakefront Conservatory", "degree": "Authored <degree> & study"}]
        conn.execute("UPDATE users SET education=?,certifications=? WHERE handle='leo-marquez'",
                     (json.dumps(education), json.dumps(["Authored <certificate> & practice"])))
        conn.execute("UPDATE schools SET about='Authored <school> & story' WHERE id=?", (school_id,))
        conn.execute("INSERT INTO alumni SELECT ?,id FROM users WHERE handle='leo-marquez'", (school_id,))
        conn.execute("UPDATE auditions SET requirements='[\"Authored requirement\"]' WHERE type='grant'")
        conn.commit()
        before = snapshot(conn)
    settings.submission_uploads_dir.mkdir(parents=True)
    upload = settings.submission_uploads_dir / 'preserved.mp4'
    upload.write_bytes(b'authored upload fixture')
    for _ in range(2):
        prepare_data(settings)
        with db.connect(settings.db_path) as conn:
            assert snapshot(conn) == before, 'Startup changed populated authored rows'
        assert upload.read_bytes() == b'authored upload fixture'
