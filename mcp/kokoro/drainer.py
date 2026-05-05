#!/usr/bin/env python3
"""Streaming TTS drainer.

Reads text chunks from /tmp/simona-queue/ in filename order, synthesizes via
Kokoro (loaded once, kept warm), plays via afplay. Exits when the queue stays
empty for a few seconds.

Single-instance: writes PID to /tmp/simona-drainer.pid; refuses to start if
another live drainer holds the lock.

The lifecycle:
  - Hooks (PreToolUse / Stop) write text chunks as `<seq>.txt` files in the
    queue dir, then ensure a drainer is running.
  - Drainer pops the lowest-numbered file, synthesizes, plays, deletes, repeats.
  - When the queue is empty for IDLE_EXIT seconds, drainer exits.
  - On a new user prompt, the UserPromptSubmit hook clears the queue and kills
    the drainer so the new turn starts fresh.
"""

import os
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cli import _stream_speak  # reuse existing producer/consumer  # noqa: E402

QUEUE_DIR = Path("/tmp/simona-queue")
LOCK = Path("/tmp/simona-drainer.pid")
IDLE_EXIT = 4.0  # seconds


def _another_drainer_alive() -> bool:
    if not LOCK.exists():
        return False
    try:
        pid = int(LOCK.read_text().strip())
    except (ValueError, OSError):
        return False
    if pid == os.getpid():
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False  # stale


def _release_lock():
    try:
        if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink()
    except OSError:
        pass


def _on_signal(signum, frame):
    _release_lock()
    sys.exit(0)


def main():
    QUEUE_DIR.mkdir(exist_ok=True)
    if _another_drainer_alive():
        sys.exit(0)
    LOCK.write_text(str(os.getpid()))
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    voice = os.environ.get("SIMONA_VOICE", "af_heart")
    speed = float(os.environ.get("SIMONA_SPEED", "1.0"))

    last_activity = time.time()
    try:
        while True:
            files = sorted(QUEUE_DIR.glob("*.txt"))
            if files:
                f = files[0]
                try:
                    text = f.read_text()
                except OSError:
                    time.sleep(0.05)
                    continue
                try:
                    f.unlink()
                except OSError:
                    pass
                if text.strip():
                    _stream_speak(text, voice=voice, speed=speed)
                last_activity = time.time()
            else:
                if time.time() - last_activity > IDLE_EXIT:
                    break
                time.sleep(0.2)
    finally:
        _release_lock()


if __name__ == "__main__":
    main()
