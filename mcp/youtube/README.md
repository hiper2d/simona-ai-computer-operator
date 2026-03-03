# YouTube Video Analyzer MCP Server

MCP server for extracting and analyzing content from YouTube videos — transcripts, code detection, and frame extraction.

## Prerequisites

- Python 3.13+
- `ffmpeg` (install via `brew install ffmpeg`)
- Shared venv managed by the parent `mcp/` project

## Setup

From the `mcp/` directory:

```bash
uv sync
```

## Register with Claude Code

Add to your Claude Code settings (`.claude/settings.json` or `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "youtube-analyzer": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp", "python", "mcp/youtube/server.py"]
    }
  }
}
```

The server uses stdio transport — Claude Code launches it directly as a subprocess, no proxy needed.

## Tools

### `get_youtube_transcript(video_url, language="en")`

Fetches timestamped captions from a YouTube video. Returns JSON with segments containing `text`, `start` (seconds), and `duration`.

### `find_code_segments(video_url, language="en")`

Analyzes the transcript using keyword heuristics to find time ranges where code is likely shown on screen. Uses a sliding window (30s window, 15s step) and returns segments with confidence scores.

### `get_video_frames(video_url, start_time, end_time, fps=0.5)`

Downloads the video at lowest quality via `yt-dlp`, then extracts frames as PNG images using `ffmpeg`. Returns absolute file paths that Claude can read with its vision capability.

- Default `fps=0.5` = one frame every 2 seconds
- Videos are cached at `~/.cache/youtube-analyzer/`

### `cleanup_cache(max_age_hours=24, delete_all=False)`

Removes old cached videos and extracted frames from `~/.cache/youtube-analyzer/`.

## `/youtube` Skill Usage

The `/youtube` slash command triggers the full analysis pipeline. Pass a URL and optionally describe what to focus on.

### Basic (extract everything)

```
/youtube https://youtu.be/eD4CEZ-_-sk
```

### With focus instructions

```
/youtube https://youtu.be/abc123 extract the bash script and the docker-compose.yaml
```

```
/youtube https://youtu.be/abc123 I need the Python FastAPI server code and the .env config
```

```
/youtube https://youtu.be/abc123 focus on the Terraform modules shown around the 5-minute mark
```

```
/youtube https://youtu.be/abc123 extract all shell commands the author runs in the terminal
```

Any text after the URL is free-form — just describe what you care about in plain English.

### What it does

1. Fetches the transcript and identifies code segments
2. Extracts frames where code is shown on screen
3. Saves files to `youtube-extracts/<video-id>/` in the project root:
   - `summary.md` — video summary with timestamps and key takeaways
   - `transcript.json` — full raw transcript
   - Code files — named as shown in the video (e.g., `ralph.sh`, `config.yaml`)
4. Partially visible files get **reconstructed** from context (marked with comments so you know what was inferred vs. directly extracted)
5. User instructions steer what gets prioritized

### Analysis approaches

**Approach A: MCP Tools (automated, recommended)**

1. `get_youtube_transcript` — fetches captions
2. `find_code_segments` — identifies code-heavy time ranges
3. `get_video_frames` — extracts frames from high-confidence segments
4. Read frames with Claude's vision to extract code

**Approach B: Chrome Browser (interactive)**

1. Open video at timestamp: `https://www.youtube.com/watch?v=ID&t=SECONDS`
2. Pause, screenshot, read with vision
3. Seek to next timestamp, repeat

## Cache

All downloads and frames are stored in `~/.cache/youtube-analyzer/<video-id>/`. Use `cleanup_cache` to manage disk usage.
