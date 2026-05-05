# Simona: AI Computer Operator

<img src="generated-images/simona-self-portrait-oai.png" width="600">

## Who is Simona?

Simona is an autonomous AI assistant built on Claude Code that can operate a computer, create content, and grow more capable over time. She has her own personality, voice, and visual identity — and she's building herself.

The goal: an AI that can run media channels, create software projects, produce videos about them, and operate independently with minimal human input.

## Capabilities

### Video Production
| Skill | Command | What it does |
|-------|---------|--------------|
| **director** | `/director <brief>` | Plan and produce videos end-to-end — scene planning, narration, effects, assembly |
| **ffmpeg** | `/ffmpeg <instructions>` | Build video scenes with ffmpeg (Ken Burns zoom, pan, scroll, crossfade, concat) |
| **veo** | `/veo <prompt or image>` | Generate AI-animated video clips using Google Veo 3.1 — premium quality, ~$0.40/s |
| **kling** | `/kling <image+prompt>` | Image-to-video via Kling-3 (fal.ai). 720p / 1080p tiers. Best for faces and hero shots |
| **seedance** | `/seedance <image+prompt>` | Image-to-video via Seedance 2.0 (ByteDance/fal.ai). Native audio, lip-sync, end-frame interpolation |
| **ltx-video** | `/ltx-video <image+prompt>` | Image-to-video via LTX-2.3. Up to 4K with audio, synchronous (no polling). Cheap, good for non-face content |
| **webpage-highlight** | `/webpage-highlight <config>` | Capture animated UI highlights — self-drawing SVG borders on DOM elements |
| **video-transitions** | (reference) | Techniques for combining AI clips with stills — freeze, lead-in/out, zoom |

### Voice & Audio
| Skill | Command | What it does |
|-------|---------|--------------|
| **elevenlabs** | `/elevenlabs <text>` | Natural-sounding speech via ElevenLabs (Lily voice, polished output) |
| **gemini-voice** | `/gemini-voice <text>` | Speech via Google Gemini TTS (cheap, fast, good for drafts) |
| **kokoro** | auto via Stop hook | Local CPU TTS (Kokoro-82M) — reads Simona's replies aloud, no API cost, ~2× realtime on Apple Silicon |

#### Live Read-Aloud

Replies are streamed aloud by a local Kokoro model — no network calls, no API cost. Three hooks coordinate:

- **PreToolUse** — fires before each tool call. Enqueues any new text emitted since the last enqueue, so intermediate narration ("let me check X") starts speaking *while the tool runs*.
- **Stop** — fires when the turn ends. Enqueues the closing text.
- **UserPromptSubmit** — intercepts voice-control commands; manages the active speaker.

A persistent **drainer** (`mcp/kokoro/drainer.py`) loads Kokoro once, drains `/tmp/simona-queue/` chunks in order, plays via `afplay`, exits after a few seconds idle. This avoids per-chunk Python startup tax and prevents overlap when chunks arrive faster than they play.

**Default state: every Claude Code session is silent.** Voice is off until one session explicitly claims it. Other sessions stay quiet — no fighting over audio across multiple Claude Code instances.

##### Controls

**Session claim (chat-only — intercepted before the LLM is invoked):**

| Type this        | Effect                                                                              |
| ---------------- | ----------------------------------------------------------------------------------- |
| `speak here`     | Claim *this* session as the speaker. Aliases: `listen here`, `voice here`, `claim voice` |
| `release voice`  | Release this session — no one speaks until next claim. Aliases: `silence here`, `unclaim` |

Switching speakers: type `speak here` in another session. The previous speaker's audio is killed cleanly.

**Mute (global — silences all sessions regardless of claim):**

| Where | Command | Effect |
|---|---|---|
| Chat  | `mute` / `shut up` / `be quiet` / `mute yourself`     | Set global mute, kill audio  |
| Chat  | `unmute` / `speak up` / `voice on` / `talk to me`     | Lift global mute (claim still required to actually hear) |
| Chat  | `stop talking` / `shush` / `hush`                     | Kill current playback only — claim and mute untouched |
| Shell | `simona-mute`                                         | Same as chat `mute` (global mute + kill audio) |
| Shell | `simona-unmute`                                       | Same as chat `unmute` |
| Shell | `simona-shutup`                                       | Same as chat `stop talking` |
| File  | `~/.simona-mute` flag                                 | Underlying primitive — hooks bail when present |
| File  | `/tmp/simona-active-session.id`                       | Holds the claimed session_id (empty/missing = nobody) |

Chat patterns match the *whole prompt* (after lowercasing + collapsing punctuation), so phrases like "let's mute the build output" pass through to the model unchanged.

##### Reading files on demand

```bash
bash mcp/kokoro/read-file.sh <path>                     # whole file
bash mcp/kokoro/read-file.sh <path> --start 50 --end 80 # line range
```

Backgrounded automatically — Simona stays responsive while you listen. Sets `/tmp/simona-reading.flag` so the Stop hook doesn't override the file with its own closing text. Stop with `simona-shutup`, `shut up` in chat, or `simona-mute`.

### Image Generation
| Skill | Command | What it does |
|-------|---------|--------------|
| **nanobanana** | `/nanobanana <prompt>` | Google Gemini (Nano Banana 2). Multi-reference (up to 3 images) for character consistency |
| **openai-image** | `/openai-image <prompt>` | OpenAI gpt-image-2. Strong at thematic/conceptual scenes (VS battles, corporate, day/night) |

### Research & Browsing
| Skill | Command | What it does |
|-------|---------|--------------|
| **browser** | `/browser [url]` | Browse the web, read pages, click, fill forms via Chrome DevTools Protocol |
| **youtube** | `/youtube <url>` | Analyze YouTube videos — extract transcripts, code, and content |

### Utilities
| Skill | Command | What it does |
|-------|---------|--------------|
| **cleanup** | `/cleanup` | Scan and remove temp files from video production and other skills |
| **werewolf** | `/werewolf` | Work with the AI Werewolf Party Game project |

### Pipeline Example

Skills chain together naturally. The **director** orchestrates the crew. For example, "make a 1-minute video explaining this YouTube video" triggers:

1. `/youtube` — fetch transcript, understand the content
2. `/nanobanana` — generate scene images from the script
3. `/elevenlabs` — narrate the script with natural voice
4. `/veo` — animate a hero shot for the intro
5. `/ffmpeg` — build scenes with zoom/scroll effects, crossfade transitions, concat into final MP4

All from a single natural language instruction.

## Architecture

### Claude Code + CLI Tools + Skills

The engine is **Claude Code** (Anthropic's CLI agent), extended with:
- **Skills** (`.claude/skills/`) — reusable workflows triggered as slash commands
- **Tool libraries** (`mcp/`) — pure Python modules with CLI entry points, called by skills via bash
- **Memory** (`.claude/memory/`) — persistent context across sessions, self-updated

```
.claude/
├── skills/          # Skill definitions (director, ffmpeg, veo, elevenlabs, etc.)
├── hooks/           # Bash scripts run on Claude Code events (Stop, UserPromptSubmit)
└── memory/          # Persistent memory, updated each session

mcp/
├── youtube/         # tools.py + cli.py — transcript, code detection, frames
├── browser/         # tools.py + cli.py + cdp_client.py — Chrome automation
├── highlight/       # cli.py — animated SVG border capture via CDP
└── kokoro/          # tools.py + cli.py + aliases.sh — local CPU TTS (Kokoro-82M)
```

Skills invoke CLI tools like `uv run python mcp/browser/cli.py navigate "https://..."` — no MCP servers, no extra processes, no token overhead from idle tool definitions.

## Setup

```bash
# Install Python dependencies (requires uv and Python 3.13+)
uv sync

# Start Chrome with debug port for browser automation
bash mcp/browser/start-chrome.sh

# Add API keys to .env
echo "GOOGLE_K=your-google-api-key" > .env
echo "EL_K=your-elevenlabs-api-key" >> .env

# Download Kokoro TTS model files (310 MB + 27 MB) for live read-aloud
mkdir -p mcp/kokoro/models
curl -L -o mcp/kokoro/models/kokoro-v1.0.onnx \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o mcp/kokoro/models/voices-v1.0.bin \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

# Enable shell control commands (one-time, picked up by every new terminal)
echo "source $(pwd)/mcp/kokoro/aliases.sh" >> ~/.zshrc
```

## What's Next

- **YouTube channel automation** — scripting, recording, editing, publishing
- **Social media automation** — posting, scheduling, engagement
- **Self-improvement** — Simona updating her own skills and memory autonomously
