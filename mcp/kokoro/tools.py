"""Kokoro TTS — local CPU text-to-speech (kokoro-onnx 0.5.x)."""

import re
from pathlib import Path

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "kokoro-v1.0.onnx"
VOICES_PATH = MODEL_DIR / "voices-v1.0.bin"

_kokoro = None


def get_kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        if not MODEL_PATH.exists() or not VOICES_PATH.exists():
            raise FileNotFoundError(
                f"Model files missing in {MODEL_DIR}. "
                "Download kokoro-v1.0.onnx and voices-v1.0.bin from "
                "https://github.com/thewh1teagle/kokoro-onnx/releases"
            )
        _kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
    return _kokoro


def strip_markdown(text: str) -> str:
    """Remove markdown so TTS reads natural prose, not punctuation soup."""
    # Fenced code blocks — drop entirely (reading code aloud is hell)
    text = re.sub(r"```[^\n]*\n.*?```", " ", text, flags=re.DOTALL)
    # Inline code — drop the backticks and content; usually identifiers
    text = re.sub(r"`[^`\n]+`", "", text)
    # Markdown links [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Headers
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
    # Bold/italic markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    # List bullets
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Blockquote markers
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r"^\s*[-=_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text: str, max_chars: int = 400) -> list[str]:
    """Split into sentence-ish chunks. Hard-cap by chars so single runaway lines
    don't stall the producer."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) <= max_chars:
            out.append(p)
            continue
        # Long sentence: break on commas/semicolons
        sub = re.split(r"(?<=[,;:])\s+", p)
        buf = ""
        for s in sub:
            if len(buf) + len(s) + 1 <= max_chars:
                buf = (buf + " " + s).strip()
            else:
                if buf:
                    out.append(buf)
                buf = s
        if buf:
            out.append(buf)
    return out


def synthesize(text: str, voice: str = "af_heart", speed: float = 1.0):
    """Returns (samples: np.ndarray, sample_rate: int)."""
    kokoro = get_kokoro()
    return kokoro.create(text, voice=voice, speed=speed, lang="en-us")
