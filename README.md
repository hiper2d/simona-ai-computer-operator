# Simona: AI Computer Operator

<img src="images/simona.png" width="600">

## Who is Simona?

Simona is an autonomous AI assistant that can operate a computer, create content, and grow more capable over time. She has her own personality, voice, and visual identity — and she's building herself.

The goal: an AI that can run media channels, create software projects, produce videos about them, and operate independently with minimal human input.

## Capabilities

### Content Creation
| Skill | Command | What it does |
|-------|---------|--------------|
| **image** | `/image <prompt>` | Generate images using Google Nano Banana 2 (Gemini API) |
| **voice** | `/voice <text>` | Generate speech with Gemini TTS (Kore voice by default) |
| **video** | `/video <instructions>` | Combine images + audio into videos with ffmpeg |

### Research & Browsing
| Skill | Command | What it does |
|-------|---------|--------------|
| **browser** | `/browser [url]` | Browse the web, read pages, click, fill forms via Chrome DevTools Protocol |
| **youtube** | `/youtube <url>` | Analyze YouTube videos — extract transcripts, code, and content |

### Pipeline Example

Skills can be chained: generate an image → generate a voiceover → combine into a video. All from natural language instructions.

## Architecture

### Claude Code + MCP + Skills

The engine is **Claude Code** (Anthropic's CLI agent), extended with:
- **MCP servers** for tool integrations (browser control, YouTube analysis)
- **Skills** (`.claude/skills/`) for reusable workflows triggered as slash commands
- **Memory** for persistent context across sessions

### MCP Servers

All servers live in `mcp/` and share a Python venv managed by `uv`.

| Server | Description |
|--------|-------------|
| **[browser-cdp](mcp/browser/README.md)** | Control Chrome via DevTools Protocol — navigate, read, click, type, screenshot |
| **[youtube-analyzer](mcp/youtube/README.md)** | Extract transcripts, detect code segments, capture frames from YouTube |

Servers are registered in `.mcp.json` at the project root.

### Simona's LLM Brain (Local)

**Current Model**: [mradermacher/Qwen3-30B-A3B-abliterated-GGUF](https://huggingface.co/mradermacher/Qwen3-30B-A3B-abliterated-GGUF)

- Qwen3-30B-A3B-abliterated, quantized in GGUF format (Q3_K_S)
- Runs locally on a gaming PC via Ollama
- Strong reasoning, function calling support, reduced censorship

<details>
<summary>Deprecated models</summary>

**Deprecated**: [unsloth/Qwen3-30B-A3B-GGUF](https://huggingface.co/unsloth/Qwen3-30B-A3B-GGUF)
- A capable model as of early 2025. I could run `IQ3_XXS` quants locally with great results

**Deprecated**: [Quantized Mistral 3.1 Small](https://huggingface.co/bartowski/mistralai_Mistral-Small-3.1-24B-Instruct-2503-GGUF)
- Good, compact, supports functions, has a large (up to 128k) context window

**Deprecated**: [Dolphin3 R1-Mistral 24B (4-bit GGUF)](https://huggingface.co/bartowski/cognitivecomputations_Dolphin3.0-R1-Mistral-24B-GGUF)
- DeepSeek R1 distilled into Mistral 3 Small 22B. Thinking capabilities but no function call support.
</details>

## Setup

```bash
# One-time: install Python dependencies (requires uv and Python 3.13+)
uv sync --python 3.13

# After updating pyproject.toml dependencies:
uv sync

# Start Chrome with debug port for browser-cdp
bash mcp/browser/start-chrome.sh

# Add your Google API key to .env
echo "GOOGLE_K=your-key-here" > .env

# Claude Code picks up MCP servers from .mcp.json automatically
```

## What's Next

- **REPL Loop** — an autonomous worker loop that picks up tasks and executes them without supervision ([brainstorm](docs/repl-loop-brainstorm.md))
- **Video production pipeline** — scripting, recording, editing, publishing
- **Social media automation** — posting, scheduling, engagement
