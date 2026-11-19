"""`--reset` wipes only data/ (database and uploads); my-clips/ and demo-uploads/ are never touched."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from server.config import Settings
from server.db import SchemaOutOfDate
from server.setup import prepare_data


class ResetKeepsSampleFoldersTest(unittest.TestCase):
    def test_reset_wipes_data_but_keeps_sample_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clips, demo_uploads = root / "my-clips", root / "demo-uploads"
            clips.mkdir()
            demo_uploads.mkdir()
            (clips / "leo-marquez-1.mp4").write_bytes(b"seed clip")
            (demo_uploads / "sample-performance.mp4").write_bytes(b"sample performance")
            settings = Settings(data_dir=root / "data", clips_dir=clips)
            prepare_data(settings)
            stale_upload = settings.profile_uploads_dir / "stale.mp4"
            stale_upload.write_bytes(b"old upload")

            prepare_data(settings, reset=True)

            self.assertFalse(stale_upload.exists())
            self.assertTrue(settings.db_path.exists())
            self.assertEqual((clips / "leo-marquez-1.mp4").read_bytes(), b"seed clip")
            self.assertEqual((demo_uploads / "sample-performance.mp4").read_bytes(), b"sample performance")

    def test_a_v1_database_is_refused_with_a_helpful_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(data_dir=Path(tmp) / "data")
            settings.data_dir.mkdir()
            conn = sqlite3.connect(str(settings.db_path))
            conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
            conn.commit()
            conn.close()
            with self.assertRaises(SchemaOutOfDate) as raised:
                prepare_data(settings)
            self.assertIn("Do not reset", str(raised.exception))
            with sqlite3.connect(str(settings.db_path)) as check:
                self.assertEqual(check.execute("PRAGMA table_info(users)").fetchone()[1], "id")


if __name__ == "__main__":
    unittest.main()
