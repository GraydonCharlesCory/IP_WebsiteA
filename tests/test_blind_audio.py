"""Real decoding and fail-closed byte-level privacy, not just an audio HTML tag."""
import io
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from server.blind_audio import audio_only
from server.config import ROOT, Settings
from server.errors import ApiError
from server.pcm_wave import clean_pcm, PCM_GUID
from tests.support import ServerTestCase


class AudioConversionTests(unittest.TestCase):
    def test_pcm_copy_drops_metadata_and_rejects_unexpected_format(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / "decoded.wav", Path(folder) / "clean.wav"
            fmt = struct.pack("<HHIIHHHHI", 65534, 2, 44100, 176400, 4, 16, 22, 16, 3) + PCM_GUID
            def write_format(format_bytes):
                chunks = b""
                for tag, value in ((b"fmt ", format_bytes), (b"LIST", b"Leo Marquez identity"), (b"data", b"\0" * 16)):
                    chunks += tag + struct.pack("<I", len(value)) + value + b"\0" * (len(value) % 2)
                source.write_bytes(b"RIFF" + struct.pack("<I", len(chunks) + 4) + b"WAVE" + chunks)
            write_format(fmt)
            clean_pcm(source, target)
            self.assertNotIn(b"Leo", target.read_bytes())
            with wave.open(str(target)) as wav:
                self.assertEqual((wav.getnchannels(), wav.getnframes()), (2, 4))
            for invalid in (fmt[:-1] + b"X", struct.pack("<HHIIHH", 3, 2, 44100, 176400, 4, 16)):
                write_format(invalid)
                with self.assertRaises(ValueError):
                    clean_pcm(source, target)
            source.write_bytes(b"RIFF\0\0\0\0WAVEdata\xff\xff\xff\xff")
            with self.assertRaises(ValueError):
                clean_pcm(source, target)

    def test_real_mp4_becomes_metadata_free_pcm_and_is_cached(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = Settings(data_dir=Path(folder))
            source = ROOT / "my-clips" / "aiko-nakamura-1.mp4"
            target = audio_only(source, settings)
            body = target.read_bytes()
            self.assertEqual(body[:4], b"RIFF")
            self.assertEqual(body[8:12], b"WAVE")
            with wave.open(io.BytesIO(body)) as wav:
                self.assertGreater(wav.getnframes(), 0)
                self.assertEqual(wav.getcomptype(), "NONE")
            chunks, offset = [], 12
            while offset + 8 <= len(body):
                chunks.append(body[offset:offset+4])
                size = int.from_bytes(body[offset+4:offset+8], "little")
                offset += 8 + size + size % 2
            self.assertEqual(chunks, [b"fmt ", b"data"])
            self.assertNotIn("aiko", target.name)
            with patch("server.blind_audio.subprocess.run", side_effect=AssertionError("must reuse cache")):
                self.assertEqual(audio_only(source, settings), target)

    def test_failure_and_timeout_never_fall_back_to_original(self):
        for failure in (subprocess.CompletedProcess([], 1), subprocess.TimeoutExpired("decoder", 45)):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / "identifying-name.mp4"
                source.write_bytes(b"private video")
                kwargs = {"side_effect": failure} if isinstance(failure, Exception) else {"return_value": failure}
                with patch("server.blind_audio.subprocess.run", **kwargs), self.assertLogs("tutti", "ERROR"):
                    with self.assertRaises(ApiError) as error:
                        audio_only(source, Settings(data_dir=Path(folder)))
                self.assertIn("withheld", str(error.exception))
                self.assertEqual(list((Path(folder) / "blind-audio").glob("*.wav")), [])


class BlindRouteTests(ServerTestCase):
    def test_owner_and_guest_receive_only_sanitized_wav_including_ranges(self):
        shutil.copyfile(ROOT / "my-clips" / "aiko-nakamura-1.mp4", self.settings.clips_dir / "leo-marquez-2.mp4")
        owner = self.client("rhonda-holloway")
        aid = owner.json("GET", "/api/auditions?mine=1")[1]["auditions"][0]["id"]
        sid = self.submission_id_of("leo-marquez", aid)
        status, body, response = owner.request("GET", f"/api/submissions/{sid}/audio")
        self.assertEqual(status, 200)
        self.assertEqual(body[:4], b"RIFF")
        self.assertIn("audio/wav", response.getheader("Content-Type"))
        self.assertIn("no-store", response.getheader("Cache-Control"))
        self.assertIsNone(response.getheader("Content-Disposition"))
        link = owner.json("POST", f"/api/auditions/{aid}/guests", {"label": "Panel"})[1]
        headers = {"X-Review-Key": link["url"].split("#")[1], "Range": "bytes=0-11"}
        code, partial, _ = self.client().request("GET", f"/api/guest/submissions/{sid}/audio", headers=headers)
        self.assertEqual((code, partial), (206, body[:12]))
        for who, code in ((None, 401), ("leo-marquez", 403), ("elena-voss", 403)):
            self.assertEqual(self.client(who).request("GET", f"/api/submissions/{sid}/audio")[0], code)
