"""Fail-closed blind playback: OS decoder → PCM → metadata-free WAV, never MP4 bytes."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import wave

from .config import log
from .errors import ApiError
from .pcm_wave import clean_pcm


def audio_only(source, settings):
    cache = settings.data_dir / "blind-audio"
    cache.mkdir(exist_ok=True)
    stat = source.stat()
    key = hashlib.sha256(f"{source}:{stat.st_mtime_ns}:{stat.st_size}".encode()).hexdigest()
    target = cache / (key + ".wav")
    if target.is_file():
        return target
    decoder = Path("/usr/bin/afconvert")
    if not decoder.is_file():
        log.error("Blind audio unavailable: macOS afconvert is missing; original media withheld")
        raise ApiError(503, "Blind audio conversion is unavailable. Use this demo on macOS with afconvert; original video is never served.")
    try:
        with tempfile.TemporaryDirectory(dir=cache) as folder:
            decoded, clean = Path(folder) / "decoded.wav", Path(folder) / "clean.wav"
            result = subprocess.run([str(decoder), "-f", "WAVE", "-d", "LEI16@44100", "-c", "2", str(source), str(decoded)],
                                    capture_output=True, timeout=45)
            if result.returncode:
                raise ValueError(f"decoder exit {result.returncode}")
            clean_pcm(decoded, clean)
            os.replace(clean, target)
        return target
    except (OSError, ValueError, wave.Error, subprocess.TimeoutExpired):
        log.exception("Blind audio conversion failed; original recording withheld")
        raise ApiError(422, "This recording could not be converted to safe audio. Upload a playable MP4 with an audio track; video has been withheld.")
