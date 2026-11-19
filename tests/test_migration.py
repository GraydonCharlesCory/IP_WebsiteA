"""A populated v2 database upgrades without resetting records or uploads."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from server import db
from server.config import Settings
from server.seed import seed
from server.setup import prepare_data


class MigrationTests(unittest.TestCase):
    def test_populated_v2_backup_rows_files_and_idempotence(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = Settings(data_dir=Path(folder) / "data", clips_dir=Path(folder) / "clips")
            settings.data_dir.mkdir()
            settings.clips_dir.mkdir()
            with db.connect(settings.db_path) as conn:
                for file in sorted(db.SCHEMA_DIR.glob("0[1-4]*.sql")):
                    sql = file.read_text().replace("'musician','director','school'", "'musician','director'")
                    sql = sql.replace("'audition','gig','grant','residency','college_audition','summer_camp'", "'audition','gig'")
                    conn.executescript(sql)
                seed(conn, settings.clips_dir)
                conn.execute("UPDATE users SET bio='Keep this custom biography' WHERE id=1")
                conn.execute("PRAGMA user_version=2")
                conn.commit()
                tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                before = {t: [tuple(r) for r in conn.execute(f'SELECT * FROM "{t}" ORDER BY rowid')] for t in tables}
            settings.submission_uploads_dir.mkdir(parents=True)
            upload = settings.submission_uploads_dir / "keep.mp4"
            upload.write_bytes(b"existing uploaded bytes")
            prepare_data(settings)
            self.assertEqual(upload.read_bytes(), b"existing uploaded bytes")
            backup = settings.db_path.with_suffix(".pre-v3.sqlite")
            self.assertTrue(backup.is_file())
            with db.connect(backup) as copy:
                self.assertEqual(copy.execute("PRAGMA user_version").fetchone()[0], 2)
                self.assertEqual(copy.execute("SELECT bio FROM users WHERE id=1").fetchone()[0], "Keep this custom biography")
            with db.connect(settings.db_path) as conn:
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 3)
                self.assertEqual(list(conn.execute("PRAGMA foreign_key_check")), [])
                for table, rows in before.items():
                    columns = len(rows[0]) if rows else 0
                    after = [tuple(r)[:columns] for r in conn.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
                    self.assertEqual(after[:len(rows)], rows, table)
                counts = {t: conn.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables}
            prepare_data(settings)
            with db.connect(settings.db_path) as conn:
                self.assertEqual({t: conn.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables}, counts)

    def test_future_schema_is_preserved_not_downgraded(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = Settings(data_dir=Path(folder))
            with sqlite3.connect(str(settings.db_path)) as conn:
                conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
                conn.execute("INSERT INTO users VALUES (99)")
                conn.execute("PRAGMA user_version=99")
            with self.assertRaises(db.SchemaOutOfDate):
                prepare_data(settings)
            with sqlite3.connect(str(settings.db_path)) as conn:
                self.assertEqual(conn.execute("SELECT id FROM users").fetchone()[0], 99)
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 99)

    def test_existing_v3_additive_metadata_preserves_rows_schema_and_constraints(self):
        from server.migration import add_columns
        from server.seed_v3 import seed_v3
        from server.discovery import metadata
        with tempfile.TemporaryDirectory() as folder:
            settings = Settings(data_dir=Path(folder) / 'data', clips_dir=Path(folder) / 'clips')
            settings.data_dir.mkdir()
            settings.clips_dir.mkdir()
            with db.connect(settings.db_path) as conn:
                for file in sorted(db.SCHEMA_DIR.glob('0[1-5]*.sql')):
                    conn.executescript(file.read_text())
                add_columns(conn)
                seed(conn, settings.clips_dir)
                seed_v3(conn)
                conn.execute("UPDATE auditions SET description='Custom Jazz high school description',level='student' WHERE id=1")
                conn.execute('PRAGMA user_version=3')
                conn.commit()
                tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name!='demo_upgrades'")]
                before = {t: [tuple(r) for r in conn.execute(f'SELECT * FROM "{t}" ORDER BY rowid')] for t in tables}
                schema = [tuple(r) for r in conn.execute("SELECT type,name,sql FROM sqlite_master WHERE type IN ('table','trigger','index') ORDER BY name")]
            prepare_data(settings)
            prepare_data(settings)
            with db.connect(settings.db_path) as conn:
                for table, rows in before.items():
                    self.assertEqual([tuple(r) for r in conn.execute(f'SELECT * FROM "{table}" ORDER BY rowid')], rows, table)
                for kind, name, sql in schema:
                    self.assertEqual(conn.execute('SELECT sql FROM sqlite_master WHERE type=? AND name=?', (kind, name)).fetchone()[0], sql, name)
                self.assertEqual(metadata(conn, 1), {'genre': '', 'eligibility': [], 'student_hub': False})
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM opportunity_discovery').fetchone()[0], 0)
                self.assertEqual(list(conn.execute('PRAGMA foreign_key_check')), [])
                with self.assertRaises(sqlite3.IntegrityError):
                    conn.execute("INSERT INTO opportunity_discovery VALUES(999999,'Jazz','[]',1)")
                with self.assertRaises(sqlite3.IntegrityError):
                    conn.execute('UPDATE auditions SET blind_review=1-blind_review WHERE id=1')
                with self.assertRaises(sqlite3.IntegrityError):
                    conn.execute("UPDATE auditions SET type='teaching' WHERE id=1")
