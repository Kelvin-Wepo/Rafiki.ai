"""
Viseme timeline generation for real-time canvas lip-sync.

Preferred source: ElevenLabs character alignment from
POST /v1/text-to-speech/{voice_id}/with-timestamps.

Fallback: Rhubarb Lip Sync CLI (https://github.com/DanielSWolf/rhubarb-lip-sync).
Last resort: amplitude envelopes from the audio itself so playback never blocks.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from utils.logger import get_logger

logger = get_logger(__name__)

AudioSource = Union[str, Path, bytes]

# Rhubarb mouth cue values. Mapped independently of the canvas renderer.
RHUBARB_VISEMES = ("A", "B", "C", "D", "E", "F", "G", "H", "X")

# Normalized 0–1 box on rafiki_avatar.png. Override via AVATAR_MOUTH_REGION JSON env.
# Calibrated on the native 501×667 PNG (cover crop). The 274×328 display
# measurement (x:92–160, y:152–191) is the same lips in a different frame;
# using those pixels as source fractions placed the box on the chin.
DEFAULT_MOUTH_REGION = {
    "x": 0.388,
    "y": 0.43,
    "width": 0.222,
    "height": 0.092,
}

# Character → Rhubarb viseme. Easy to retune without touching callers.
CHAR_TO_VISEME: Dict[str, str] = {
    "a": "D",
    "á": "D",
    "à": "D",
    "â": "D",
    "e": "C",
    "é": "C",
    "è": "C",
    "i": "C",
    "í": "C",
    "y": "C",
    "o": "E",
    "ó": "E",
    "u": "F",
    "ú": "F",
    "w": "F",
    "p": "A",
    "b": "A",
    "m": "A",
    "f": "G",
    "v": "G",
    "l": "H",
    "t": "B",
    "d": "B",
    "s": "B",
    "z": "B",
    "n": "B",
    "k": "B",
    "g": "B",
    "r": "B",
    "h": "B",
    "j": "B",
    "c": "B",
    "q": "B",
    "x": "B",
    " ": "X",
    "\n": "X",
    "\t": "X",
    ".": "X",
    ",": "X",
    "!": "X",
    "?": "X",
    ";": "X",
    ":": "X",
    "-": "X",
    "'": "X",
}


def mouth_region_config() -> Dict[str, float]:
    raw = (os.environ.get("AVATAR_MOUTH_REGION") or "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            return {
                "x": float(parsed["x"]),
                "y": float(parsed["y"]),
                "width": float(parsed["width"]),
                "height": float(parsed["height"]),
            }
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            logger.warning("Invalid AVATAR_MOUTH_REGION; using defaults")
    return dict(DEFAULT_MOUTH_REGION)


def _cue(time: float, viseme: str, duration: float) -> Dict[str, Any]:
    return {
        "time": round(max(0.0, float(time)), 4),
        "viseme": viseme if viseme in RHUBARB_VISEMES else "X",
        "duration": round(max(0.0, float(duration)), 4),
    }


def _coalesce(cues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge consecutive identical visemes so the frontend lerps fewer jumps."""
    merged: List[Dict[str, Any]] = []
    for cue in cues:
        if cue["duration"] <= 0:
            continue
        if merged and merged[-1]["viseme"] == cue["viseme"]:
            merged[-1]["duration"] = round(merged[-1]["duration"] + cue["duration"], 4)
        else:
            merged.append(dict(cue))
    return merged


def visemes_from_elevenlabs_alignment(alignment: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Turn ElevenLabs character timestamps into a Rhubarb-style viseme timeline."""
    if not alignment:
        return []
    characters = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    if not characters or len(characters) != len(starts) or len(characters) != len(ends):
        return []

    cues: List[Dict[str, Any]] = []
    for char, start, end in zip(characters, starts, ends):
        viseme = CHAR_TO_VISEME.get(str(char).lower(), "B")
        duration = float(end) - float(start)
        if duration < 0:
            duration = 0.04
        # Tiny rest cues (letter gaps) slam the mouth shut and look unsynced.
        if viseme == "X" and duration < 0.07:
            viseme = "B"
        cues.append(_cue(float(start), viseme, duration or 0.04))
    return _coalesce(cues)


def visemes_from_rhubarb_json(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize Rhubarb JSON (`mouthCues`) to {time, viseme, duration}."""
    mouth_cues = payload.get("mouthCues") or payload.get("mouth_cues") or []
    cues: List[Dict[str, Any]] = []
    for item in mouth_cues:
        start = float(item.get("start") or item.get("time") or 0.0)
        end = item.get("end")
        duration = float(end) - start if end is not None else float(item.get("duration") or 0.08)
        viseme = str(item.get("value") or item.get("viseme") or "X")
        cues.append(_cue(start, viseme, duration))
    return _coalesce(cues)


def visemes_from_pcm_energy(
    pcm: bytes,
    sample_rate: int = 22050,
    sample_width: int = 2,
    frame_ms: int = 40,
) -> List[Dict[str, Any]]:
    """Amplitude envelope fallback when neither ElevenLabs nor Rhubarb is available."""
    if not pcm or sample_width <= 0:
        return []
    frame_samples = max(1, int(sample_rate * (frame_ms / 1000.0)))
    frame_bytes = frame_samples * sample_width
    cues: List[Dict[str, Any]] = []
    time = 0.0
    duration = frame_ms / 1000.0
    fmt = "<" + ("h" if sample_width == 2 else "b") * frame_samples

    for offset in range(0, len(pcm) - frame_bytes + 1, frame_bytes):
        chunk = pcm[offset : offset + frame_bytes]
        try:
            samples = struct.unpack(fmt, chunk)
        except struct.error:
            break
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        peak = 32768.0 if sample_width == 2 else 128.0
        energy = min(1.0, rms / (peak * 0.35))
        if energy < 0.08:
            viseme = "X"
        elif energy < 0.22:
            viseme = "B"
        elif energy < 0.55:
            viseme = "C"
        else:
            viseme = "D"
        cues.append(_cue(time, viseme, duration))
        time += duration
    return _coalesce(cues)


def _read_wav_pcm(path: Path) -> Optional[tuple[bytes, int, int]]:
    try:
        with wave.open(str(path), "rb") as wav:
            return wav.readframes(wav.getnframes()), wav.getframerate(), wav.getsampwidth()
    except Exception as exc:
        logger.warning(f"Could not read wav {path}: {exc}")
        return None


def _write_temp_audio(data: bytes, suffix: str) -> Path:
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    handle.write(data)
    handle.close()
    return Path(handle.name)


def _ffmpeg_to_wav(src: Path) -> Optional[Path]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    dest = Path(tempfile.mkstemp(suffix=".wav")[1])
    try:
        subprocess.run(
            [ffmpeg, "-y", "-i", str(src), "-ac", "1", "-ar", "22050", str(dest)],
            check=True,
            capture_output=True,
            timeout=20,
        )
        return dest
    except (subprocess.SubprocessError, OSError) as exc:
        logger.warning(f"ffmpeg conversion failed: {exc}")
        dest.unlink(missing_ok=True)
        return None


def rhubarb_bin() -> Optional[str]:
    env = (os.environ.get("RHUBARB_BIN") or "").strip()
    if env and Path(env).exists():
        return env
    return shutil.which("rhubarb")


def _run_rhubarb(wav_path: Path, dialog: Optional[str] = None) -> List[Dict[str, Any]]:
    binary = rhubarb_bin()
    if not binary:
        return []
    cmd = [binary, "-f", "json", "-q", "--extendedShapes", "GHX", str(wav_path)]
    dialog_path: Optional[Path] = None
    if dialog:
        dialog_path = Path(tempfile.mkstemp(suffix=".txt")[1])
        dialog_path.write_text(dialog, encoding="utf-8")
        cmd.extend(["-d", str(dialog_path)])
    try:
        completed = subprocess.run(cmd, check=True, capture_output=True, timeout=25, text=True)
        payload = json.loads(completed.stdout or "{}")
        return visemes_from_rhubarb_json(payload)
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError) as exc:
        logger.warning(f"Rhubarb viseme extraction failed: {exc}")
        return []
    finally:
        if dialog_path:
            dialog_path.unlink(missing_ok=True)


def get_viseme_timeline(
    audio_file_path_or_buffer: Optional[AudioSource] = None,
    *,
    text: Optional[str] = None,
    alignment: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Return [{time, viseme, duration}] for the given audio.

    Order: ElevenLabs alignment → Rhubarb → PCM energy envelope.
    """
    from_alignment = visemes_from_elevenlabs_alignment(alignment)
    if from_alignment:
        return from_alignment

    temp_paths: List[Path] = []
    wav_path: Optional[Path] = None
    try:
        if isinstance(audio_file_path_or_buffer, (str, Path)):
            src = Path(audio_file_path_or_buffer)
            if src.suffix.lower() == ".wav":
                wav_path = src
            else:
                converted = _ffmpeg_to_wav(src)
                if converted:
                    temp_paths.append(converted)
                    wav_path = converted
        elif isinstance(audio_file_path_or_buffer, (bytes, bytearray)):
            header = bytes(audio_file_path_or_buffer[:4])
            suffix = ".wav" if header == b"RIFF" else ".mp3"
            src = _write_temp_audio(bytes(audio_file_path_or_buffer), suffix)
            temp_paths.append(src)
            if suffix == ".wav":
                wav_path = src
            else:
                converted = _ffmpeg_to_wav(src)
                if converted:
                    temp_paths.append(converted)
                    wav_path = converted

        if wav_path:
            rhubarb_cues = _run_rhubarb(wav_path, dialog=text)
            if rhubarb_cues:
                return rhubarb_cues
            pcm = _read_wav_pcm(wav_path)
            if pcm:
                frames, rate, width = pcm
                energy = visemes_from_pcm_energy(frames, rate, width)
                if energy:
                    return energy
    finally:
        for path in temp_paths:
            path.unlink(missing_ok=True)

    return []


async def get_viseme_timeline_async(
    audio_file_path_or_buffer: Optional[AudioSource] = None,
    *,
    text: Optional[str] = None,
    alignment: Optional[Dict[str, Any]] = None,
    timeout_s: float = 1.5,
) -> List[Dict[str, Any]]:
    """Non-blocking wrapper. Returns [] if viseme extraction is slow or fails."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(
                get_viseme_timeline,
                audio_file_path_or_buffer,
                text=text,
                alignment=alignment,
            ),
            timeout=timeout_s,
        )
    except Exception as exc:
        logger.warning(f"Viseme timeline skipped: {exc}")
        return []
