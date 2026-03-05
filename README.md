# Simona: AI Computer Operator

<img src="images/simona.png" width="600">

## Who is Simona?

Simona is an autonomous AI assistant built on Claude Code that can operate a computer, create content, and grow more capable over time. She has her own personality, voice, and visual identity — and she's building herself.

The goal: an AI that can run media channels, create software projects, produce videos about them, and operate independently with minimal human input.

## Capabilities

### Content Creation
| Skill | Command | What it does |
|-------|---------|--------------|
| **image** | `/image <prompt>` | Generate images using Gemini 3.1 Flash |
| **voice** | `/voice <text>` | Generate speech with Gemini TTS (Kore voice by default) |
| **video** | `/video <instructions>` | Combine images + audio into videos with ffmpeg (Ken Burns zoom, pan, scroll effects) |

### Research & Browsing
| Skill | Command | What it does |
|-------|---------|--------------|
| **browser** | `/browser [url]` | Browse the web, read pages, click, fill forms via Chrome DevTools Protocol |
| **youtube** | `/youtube <url>` | Analyze YouTube videos — extract transcripts, code, and content |

### Pipeline Example

Skills chain together naturally. For example, "make a 1-minute video explaining this YouTube video" triggers:

1. `/youtube` — fetch transcript, understand the content
2. `/image` — generate scene images from the script
3. `/voice` — narrate the script
4. `/video` — stitch images + audio with Ken Burns effects into a final MP4

All from a single natural language instruction.

## Architecture

### Claude Code + CLI Tools + Skills

The engine is **Claude Code** (Anthropic's CLI agent), extended with:
- **Skills** (`.claude/skills/`) — reusable workflows triggered as slash commands
- **Tool libraries** (`mcp/`) — pure Python modules with CLI entry points, called by skills via bash
- **Memory** (`.claude/memory/`) — persistent context across sessions, self-updated

```
.claude/
├── skills/          # Skill definitions (youtube, browser, image, voice, video)
└── memory/          # Persistent memory, updated each session

mcp/
├── youtube/         # tools.py + cli.py — transcript, code detection, frames
└── browser/         # tools.py + cli.py + cdp_client.py — Chrome automation
```

Skills invoke CLI tools like `uv run python mcp/browser/cli.py navigate "https://..."` — no MCP servers, no extra processes, no token overhead from idle tool definitions.

## Setup

```bash
# Install Python dependencies (requires uv and Python 3.13+)
uv sync

# Start Chrome with debug port for browser automation
bash mcp/browser/start-chrome.sh

# Add your Google API key to .env (used for image gen and TTS)
echo "GOOGLE_K=your-key-here" > .env
```

## What's Next

- **YouTube channel automation** — scripting, recording, editing, publishing
- **REPL Loop** — autonomous worker loop that picks up tasks without supervision
- **Social media automation** — posting, scheduling, engagement
