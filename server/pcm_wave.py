"""Copy only validated 16-bit PCM from afconvert WAV, including extensible headers.

Python 3.9's wave reader rejects extensible WAV. Parse the decoder's RIFF chunks,
but rebuild a plain WAV with wave so no metadata or extra tracks survive.
"""
import struct
import wave

PCM_GUID = bytes.fromhex("0100000000001000800000aa00389b71")


def clean_pcm(source, destination):
    with open(source, "rb") as reader:
        header = reader.read(12)
        if header[:4] != b"RIFF" or header[8:] != b"WAVE":
            raise ValueError("Decoder did not produce RIFF WAVE")
        fmt, audio = None, None
        length = source.stat().st_size
        while reader.tell() + 8 <= length:
            kind, size = struct.unpack("<4sI", reader.read(8))
            start = reader.tell()
            if start + size > length:
                raise ValueError("Truncated decoder output")
            if kind == b"fmt ":
                fmt = reader.read(min(size, 40))
            elif kind == b"data":
                audio = (start, size)
            reader.seek(start + size + size % 2)
        if fmt is None or len(fmt) < 16 or audio is None:
            raise ValueError("Decoder output lacks audio format or samples")
        tag, channels, rate, _, alignment, bits = struct.unpack("<HHIIHH", fmt[:16])
        if (tag not in (1, 65534) or channels not in (1, 2) or rate != 44100 or
                bits != 16 or alignment != channels * 2 or not audio[1] or audio[1] % alignment or
                (tag == 65534 and (len(fmt) < 40 or fmt[24:40] != PCM_GUID))):
            raise ValueError("Decoder output is not the requested 16-bit PCM")
        reader.seek(audio[0])
        with wave.open(str(destination), "wb") as writer:
            writer.setparams((channels, 2, rate, 0, "NONE", "not compressed"))
            remaining = audio[1]
            while remaining:
                samples = reader.read(min(remaining, 262144))
                if not samples:
                    raise ValueError("Truncated PCM samples")
                writer.writeframesraw(samples)
                remaining -= len(samples)
