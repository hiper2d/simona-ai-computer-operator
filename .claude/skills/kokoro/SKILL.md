---
name: kokoro
description: Local CPU text-to-speech with Kokoro-82M. Used for the auto-read-aloud Stop hook and on-demand WAV generation when Alex wants spoken output without paying for ElevenLabs/Gemini.
---

# Kokoro Local TTS

Local TTS via `kokoro-onnx` (Kokoro-82M). Runs on Apple Silicon CPU at ~2× real-time. Used by the **Stop hook** to read assistant responses aloud and as a free TTS option for drafts.

When to prefer Kokoro vs the cloud voices:
- **Kokoro**: live read-aloud, drafts, anything where free + offline matters more than maximum naturalness.
- **ElevenLabs (Lily)**: final video narration. Don't downgrade to Kokoro for published content.
- **Gemini TTS**: video narration drafts.

## Files

- `mcp/kokoro/cli.py` — CLI entry point
- `mcp/kokoro/tools.py` — synthesis + markdown stripping + sentence chunker
- `mcp/kokoro/models/` — `kokoro-v1.0.onnx` (310 MB) + `voices-v1.0.bin` (27 MB), gitignored
- `.claude/hooks/speak-response.sh` — Stop hook, wired in `.claude/settings.json`

## Reading files on demand

When Alex asks "read me X" / "read this file" / "read lines 50-80 of foo.py" — use the wrapper, not the speak CLI directly:

```bash
bash mcp/kokoro/read-file.sh <path>                       # whole file
bash mcp/kokoro/read-file.sh <path> --start 50 --end 80   # line range
bash mcp/kokoro/read-file.sh <path> --start 100           # from line N to end
```

The wrapper:
- Runs the read in background (`& disown`) so the bash tool returns instantly — Alex can keep talking while I read.
- Kills any prior playback first so consecutive reads don't overlap.
- Sets `/tmp/simona-reading.flag` for the duration. The Stop hook checks this and skips its own playback so my "Reading SKILL.md..." closing text doesn't override the file. Cleared on completion or interruption (`trap`).

To stop a read mid-stream: `simona-shutup`, `shut up`/`stop talking` in chat, or `simona-mute` (persistent).

Don't read code files aloud unprompted — they're miserable to listen to. Suggest a doc/comment range first or summarize instead.

## CLI usage

```bash
# Speak text from stdin (live playback via afplay)
echo "Hello Alex" | uv run python mcp/kokoro/cli.py speak

# Pick a voice
echo "Hello" | uv run python mcp/kokoro/cli.py speak --voice bf_emma --speed 1.0

# Write to WAV instead of playing
echo "Hello" | uv run python mcp/kokoro/cli.py speak --output /tmp/out.wav

# List voices
uv run python mcp/kokoro/cli.py voices
```

Voices worth trying:
- `af_heart` — default. Warm female US, the most natural one out of the box.
- `af_sarah`, `af_nicole` — female US alternatives
- `am_michael`, `am_onyx` — male US
- `bf_emma`, `bf_lily` — female British (different from ElevenLabs Lily)
- `bm_george` — male British storyteller

Speed: `--speed 1.0` is natural. 1.1–1.3 is comfortable for skimming long replies. Below 0.8 sounds drunk.

## Streaming auto read-aloud

Two hooks share one script (`speak-response.sh`):
- **PreToolUse** — fires before each tool call. Enqueues any text blocks emitted since the last enqueue, so intermediate narration ("let me check X") starts speaking *while the tool runs*.
- **Stop** — fires when the turn ends. Enqueues the closing text.

Each hook invocation:
1. Reads the JSONL transcript.
2. Finds the last real user prompt timestamp (excludes tool_results, which are also `type: "user"`).
3. Reads `/tmp/simona-last-queued.ts` marker — only entries newer than this get enqueued (no double-speaking).
4. Writes each new text block to `/tmp/simona-queue/<seq>.txt` and updates the marker.
5. Spawns the persistent drainer (`mcp/kokoro/drainer.py`) if it isn't already running.

The **drainer** is a long-lived Python process that loads Kokoro once and stays warm. It pops queue files in order, synthesizes via `_stream_speak`, plays via `afplay`, deletes the file, repeats. Self-exits after 4s of idle, single-instance via `/tmp/simona-drainer.pid`.

This avoids two problems with the naive "spawn-per-chunk" approach: (a) overlap when chunk 2 starts before chunk 1 finishes, and (b) ~1.5s Python+ONNX startup on every chunk.

**Session gating.** `speak-response.sh` reads `/tmp/simona-active-session.id`. If empty (no claim) or doesn't match the current `session_id` from the hook input, the hook bails. Only the claimed session enqueues.

`UserPromptSubmit` hook (`voice-control.sh`) cuts off in-flight audio at the start of a new turn — but only if THIS session is the active speaker. Other sessions don't touch the audio state at all.

If a new turn starts before the previous one finishes speaking, the new hook `pkill`s the in-flight `afplay` + `kokoro/cli.py` so the old audio stops cleanly.

## Controls

**Default state: every session is silent until one claims the voice.** You opt in by typing `speak here` in the session you want to hear. Other sessions stay quiet. This avoids the multi-session chaos where two Claude Code instances would talk over each other.

**In chat (intercepted by `voice-control.sh` UserPromptSubmit hook — no LLM call):**

| Type this        | Effect                                                    |
| ---------------- | --------------------------------------------------------- |
| `speak here`     | Claim *this* session as the speaker. Aliases: `listen here`, `voice here`, `claim voice`. |
| `release voice`  | Release this session. No one speaks until next claim. Aliases: `silence here`, `stop speaking here`, `unclaim`. |
| `mute`           | Global mute — silences ALL sessions. Aliases: `shut up`, `be quiet`, `mute yourself`, `simona mute`. |
| `unmute`         | Lift global mute. (Claim is independent — still need an active claim to actually hear anything.) Aliases: `speak up`, `voice on`, `talk to me`. |
| `stop talking`   | Kill current playback only — claim and mute state untouched. Aliases: `shush`, `hush`. |

These match the *whole prompt* (after lowercasing + stripping punctuation) so phrases like "let's mute the build output" pass through to the model unchanged.

**Switching speakers:** type `speak here` in another session — the prior speaker's audio is killed cleanly and the new session takes over. Two sessions can't be active simultaneously.

**In shell:**
```bash
touch ~/.simona-mute    # mute
rm ~/.simona-mute       # unmute
pkill -f kokoro/cli.py ; pkill -x afplay   # stop now
export SIMONA_VOICE=bf_emma   # change default voice in ~/.zshrc
```

Suggested shell aliases (drop in `~/.zshrc`, or `source mcp/kokoro/aliases.sh`):
```bash
alias simona-mute='touch ~/.simona-mute && echo muted'
alias simona-unmute='rm -f ~/.simona-mute && echo unmuted'
alias simona-shutup='pkill -f kokoro/cli.py 2>/dev/null; pkill -x afplay 2>/dev/null; echo stopped'
```

`simona-mute`/`simona-unmute` toggle the flag file (persistent state).
`simona-shutup` only kills in-flight playback — future responses still speak.

## Markdown stripping

The CLI strips before synthesis to avoid reading punctuation aloud:
- Fenced code blocks → dropped entirely (do not read code)
- Inline `code` → dropped
- `[link text](url)` → "link text"
- `**bold**`, `*italic*`, `__under__` → unwrapped
- Headers, list bullets, blockquotes, hrules → stripped
- Whitespace collapsed

## Performance

- Model load: ~2 s (one-time per `cli.py` invocation)
- RTF on M-series Mac: ~0.5 (1s of audio in 0.5s of compute)
- Time-to-first-audio for a long reply: ~1 s after the first sentence is synthesized
- No network calls, no API cost

## Updating the model

If `kokoro-onnx` ships a new model version, update URLs in this file and re-download to `mcp/kokoro/models/`. Keep filenames as `kokoro-v1.0.onnx` + `voices-v1.0.bin` or update `tools.py` paths.

Source: https://github.com/thewh1teagle/kokoro-onnx/releases
