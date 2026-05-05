#!/usr/bin/env python3
"""Kokoro TTS CLI — local CPU text-to-speech.

Usage:
    uv run python mcp/kokoro/cli.py speak [--voice af_heart] [--speed 1.0] [--output FILE.wav] [--text TEXT]
        Read text from stdin (or --text) and play it via afplay.
        With --output, write WAV instead of playing.
    uv run python mcp/kokoro/cli.py voices
        List built-in voice names.

Streaming: text is split by sentence; sentence N+1 is synthesized while N is
playing. First audio starts within ~1s for typical input.

Mute: create ~/.simona-mute to silence playback (synthesis still skipped).
Kill: pkill afplay
"""

import os
import queue
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tools import strip_markdown, split_sentences, synthesize  # noqa: E402

MUTE_FLAG = Path.home() / ".simona-mute"

VOICES = [
    "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica", "af_kore",
    "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
    "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael",
    "am_onyx", "am_puck", "am_santa",
    "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
    "bm_daniel", "bm_fable", "bm_george", "bm_lewis",
]


def _parse_flag(args: list[str], flag: str, default=None):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            val = args[i + 1]
            del args[i:i + 2]
            return val
    return default


def _stream_speak(text: str, voice: str, speed: float):
    """Producer/consumer: synth sentences in order, afplay them gaplessly."""
    import soundfile as sf

    sentences = split_sentences(text)
    if not sentences:
        return

    audio_q: queue.Queue = queue.Queue(maxsize=4)
    sentinel = object()

    def producer():
        for s in sentences:
            try:
                samples, sr = synthesize(s, voice=voice, speed=speed)
                fd, path = tempfile.mkstemp(suffix=".wav", prefix="kokoro_")
                os.close(fd)
                sf.write(path, samples, sr)
                audio_q.put(path)
            except Exception as e:
                print(f"[kokoro] synth error: {e}", file=sys.stderr)
        audio_q.put(sentinel)

    t = threading.Thread(target=producer, daemon=True)
    t.start()

    while True:
        path = audio_q.get()
        if path is sentinel:
            break
        try:
            subprocess.run(["afplay", path], check=False)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    t.join()


def cmd_speak(args: list[str]):
    voice = _parse_flag(args, "--voice", "af_heart")
    speed = float(_parse_flag(args, "--speed", "1.0"))
    output = _parse_flag(args, "--output")
    text = _parse_flag(args, "--text")

    if text is None:
        text = sys.stdin.read()

    text = strip_markdown(text)
    if not text.strip():
        return

    if output is None and MUTE_FLAG.exists():
        return

    if output:
        import numpy as np
        import soundfile as sf
        sentences = split_sentences(text)
        all_samples = []
        sr = 24000
        for s in sentences:
            samples, sr = synthesize(s, voice=voice, speed=speed)
            all_samples.append(samples)
        if all_samples:
            sf.write(output, np.concatenate(all_samples), sr)
            print(f"wrote {output}")
    else:
        _stream_speak(text, voice, speed)


def cmd_voices(args: list[str]):
    print("\n".join(VOICES))


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)
    cmd = sys.argv[1]
    args = list(sys.argv[2:])
    if cmd == "speak":
        cmd_speak(args)
    elif cmd == "voices":
        cmd_voices(args)
    else:
        print(__doc__.strip())
        sys.exit(1)


if __name__ == "__main__":
    main()
