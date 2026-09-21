"""Viseme timeline generation: ElevenLabs alignment, Rhubarb JSON, energy fallback."""

from __future__ import annotations

import io
import math
import struct
import wave
from pathlib import Path

from services.viseme_service import (
    get_viseme_timeline,
    visemes_from_elevenlabs_alignment,
    visemes_from_pcm_energy,
    visemes_from_rhubarb_json,
)


def _tone_wav_bytes(duration_s: float = 0.6, sample_rate: int = 22050) -> bytes:
    frames = bytearray()
    for i in range(int(sample_rate * duration_s)):
        t = i / sample_rate
        envelope = 0.2 + 0.8 * abs(math.sin(t * 12.0))
        sample = int(14000 * envelope * math.sin(2 * math.pi * 180 * t))
        frames += struct.pack("<h", max(-32767, min(32767, sample)))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(frames))
    return buf.getvalue()


def test_elevenlabs_alignment_maps_characters_to_rhubarb_visemes():
    alignment = {
        "characters": ["P", "a", " ", "w"],
        "character_start_times_seconds": [0.0, 0.08, 0.16, 0.28],
        "character_end_times_seconds": [0.08, 0.16, 0.28, 0.36],
    }
    cues = visemes_from_elevenlabs_alignment(alignment)
    visemes = [c["viseme"] for c in cues]
    assert "A" in visemes  # p
    assert "D" in visemes  # a
    assert "X" in visemes  # held space
    assert "F" in visemes  # w
    assert all(c["duration"] > 0 for c in cues)
    assert cues[0]["time"] == 0.0


def test_short_letter_gaps_do_not_fully_close():
    alignment = {
        "characters": ["a", " ", "w"],
        "character_start_times_seconds": [0.0, 0.08, 0.12],
        "character_end_times_seconds": [0.08, 0.12, 0.2],
    }
    visemes = [c["viseme"] for c in visemes_from_elevenlabs_alignment(alignment)]
    assert "X" not in visemes


def test_rhubarb_json_normalizes_mouth_cues():
    payload = {
        "mouthCues": [
            {"start": 0.0, "end": 0.12, "value": "X"},
            {"start": 0.12, "end": 0.28, "value": "D"},
            {"start": 0.28, "end": 0.4, "value": "D"},
        ]
    }
    cues = visemes_from_rhubarb_json(payload)
    assert cues[0]["viseme"] == "X"
    assert cues[1]["viseme"] == "D"
    assert cues[1]["duration"] == 0.28  # consecutive D merged
    assert abs(cues[1]["time"] - 0.12) < 1e-6


def test_get_viseme_timeline_from_sample_wav(tmp_path: Path):
    wav_bytes = _tone_wav_bytes()
    sample = tmp_path / "sample.wav"
    sample.write_bytes(wav_bytes)

    from_path = get_viseme_timeline(sample)
    from_buffer = get_viseme_timeline(wav_bytes)

    assert from_path, "energy fallback should produce cues from a modulated tone"
    assert from_buffer
    assert from_path[0]["time"] == 0.0
    assert {c["viseme"] for c in from_path} <= {"A", "B", "C", "D", "E", "F", "G", "H", "X"}
    assert sum(c["duration"] for c in from_path) > 0.3


def test_pcm_energy_silence_is_rest():
    silence = b"\x00\x00" * 22050
    cues = visemes_from_pcm_energy(silence, sample_rate=22050, sample_width=2)
    assert cues
    assert all(c["viseme"] == "X" for c in cues)
