"""Every time-based value (chapters, notes) lies inside its clip, and out-of-range times are rejected."""
import json
import struct
from urllib.parse import quote
import tempfile
import unittest
from pathlib import Path

from server import db
from server.config import Settings
from server.durations import mp4_duration, require_within
from server.errors import ApiError
from server.setup import prepare_data
from tests.support import ServerTestCase, find_opportunity


def mp4_with_duration(seconds: int, timescale: int = 1000) -> bytes:
    """A minimal MP4 header (ftyp + moov/mvhd) that reports the given length; enough for the server's probe."""
    payload = struct.pack(">B3xIIII", 0, 0, 0, timescale, seconds * timescale) + b"\x00" * 80
    mvhd = struct.pack(">I", 8 + len(payload)) + b"mvhd" + payload
    moov = struct.pack(">I", 8 + len(mvhd)) + b"moov" + mvhd
    return struct.pack(">I", 16) + b"ftypmp42\x00\x00\x00\x00" + moov


class SeedDurationTests(unittest.TestCase):
    def test_every_seeded_time_is_inside_its_real_clip(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(data_dir=Path(tmp) / "data")  # the real my-clips/ folder
            prepare_data(settings)
            conn = db.connect(settings.db_path)
            try:
                rows = conn.execute("SELECT * FROM submissions").fetchall()
                self.assertTrue(rows)
                for row in rows:
                    self.assertIsNotNone(row["duration_sec"], f"submission {row['id']} has no known duration")
                    real = mp4_duration(settings.clips_dir / conn.execute("SELECT file FROM clips WHERE id=?", (row["clip_id"],)).fetchone()["file"])
                    self.assertAlmostEqual(row["duration_sec"], real, places=3)
                    notes = json.loads(conn.execute("SELECT notes FROM reviews WHERE submission_id=?", (row["id"],)).fetchone()["notes"]) \
                        if conn.execute("SELECT 1 FROM reviews WHERE submission_id=?", (row["id"],)).fetchone() else []
                    for item in json.loads(row["timestamps"]) + notes:
                        self.assertTrue(0 <= item["time"] <= row["duration_sec"], f"submission {row['id']}: {item} outside {row['duration_sec']}s")
            finally:
                conn.close()


class ProbeTests(unittest.TestCase):
    def test_reads_duration_and_reports_unreadable_files_as_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            good, bad = Path(tmp) / "good.mp4", Path(tmp) / "bad.mp4"
            good.write_bytes(mp4_with_duration(42))
            bad.write_bytes(b"not a video at all")
            self.assertEqual(mp4_duration(good), 42)
            self.assertIsNone(mp4_duration(bad))
            self.assertIsNone(mp4_duration(Path(tmp) / "missing.mp4"))

    def test_require_within(self):
        self.assertEqual(require_within(40, 40.05, "A note"), 40)
        self.assertEqual(require_within(500, None, "A note"), 500)  # length unknown: only the start is checked
        for bad in (-1, 41):
            with self.assertRaises(ApiError):
                require_within(bad, 40.0, "A note")


class OutOfRangeTimeTests(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.settings.clips_dir / "leo-marquez-2.mp4").write_bytes(mp4_with_duration(40))
        conn = db.connect(cls.settings.db_path)
        conn.execute("UPDATE clips SET duration_sec=40 WHERE file='leo-marquez-2.mp4'")
        conn.execute("UPDATE submissions SET duration_sec=40 WHERE clip_id IN (SELECT id FROM clips WHERE file='leo-marquez-2.mp4')")
        conn.commit()
        conn.close()

    def setUp(self):
        self.rhonda = self.client("rhonda-holloway")
        self.audition = find_opportunity(self.rhonda, "Lead Tenor")
        self.leo = self.submission_id_of("leo-marquez", self.audition["id"])

    def test_note_outside_the_clip_is_rejected_and_inside_is_saved(self):
        for bad in (41, 5000, -3):
            status, data = self.rhonda.json("PUT", f"/api/submissions/{self.leo}/review", {"notes": [{"time": bad, "text": "x"}]})
            self.assertEqual(status, 400, bad)
            self.assertIn("clip", data["error"])
        status, data = self.rhonda.json("PUT", f"/api/submissions/{self.leo}/review", {"notes": [{"time": 40, "text": "end"}]})
        self.assertEqual((status, data["review"]["notes"]), (200, [{"time": 40, "text": "end"}]))

    def test_submission_detail_exposes_the_clip_length(self):
        detail = self.rhonda.json("GET", f"/api/submissions/{self.leo}")[1]["submission"]
        self.assertEqual(detail["duration"], 40)

    def test_chapters_outside_the_clip_are_rejected_on_submit(self):
        priya, jordan = self.client("priya-raman"), self.client("jordan-wells")
        honors = find_opportunity(priya, "Honors Jazz Combo")
        # an upload whose header says 30 s: a chapter at 31 s is refused and the file is not kept
        body = mp4_with_duration(30)
        url = f"/api/auditions/{honors['id']}/submissions?timestamps={quote(json.dumps([{'time': 31, 'label': 'late'}]))}"
        status, data = jordan.upload(url, body)
        self.assertEqual(status, 400)
        self.assertIn("30s", data["error"])
        self.assertEqual(list(self.settings.submission_uploads_dir.glob("*.mp4")), [])
        ok_url = f"/api/auditions/{honors['id']}/submissions?timestamps={quote(json.dumps([{'time': 30, 'label': 'end'}]))}"
        self.assertEqual(jordan.upload(ok_url, body)[0], 201)
