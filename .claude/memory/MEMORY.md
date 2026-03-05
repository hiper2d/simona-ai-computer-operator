# Simona's Memory

## Alex

- Name: Alex
- Loves horror movies and dark comedies
- Appreciates sarcastic, straightforward communication
- Goal: build Simona into a fully autonomous assistant for media and software projects

## Project Architecture

- **Skills** (`.claude/skills/`) are the primary interface — youtube, browser, image, voice, video
- **Tool libraries** (`mcp/`) — pure Python, no MCP dependency. CLI entry points called by skills via bash.
  - `mcp/youtube/` — tools.py (logic) + cli.py (CLI dispatcher)
  - `mcp/browser/` — tools.py (logic) + cli.py (CLI dispatcher) + cdp_client.py (CDP WebSocket client)
- `mcp/` directory name is a leftover — may rename to `tools/` eventually
- Dependencies: httpx, websockets, youtube-transcript-api, yt-dlp (managed by uv)

## Skills

- **youtube**: transcript extraction, code segment detection, frame capture
- **browser**: Chrome CDP automation (navigate, read, click, type, scroll, screenshot, JS execution)
- **image**: Gemini 3.1 Flash image generation
- **voice**: Gemini 2.5 Flash TTS (default voice: Kore)
- **video**: ffmpeg-based video creation with Ken Burns zoom, pan, scroll effects

## Key Learnings

- YouTube Studio upload via browser automation works: navigate to studio.youtube.com → Create → Upload videos → use `DOM.setFileInputFiles` CDP method to inject file into hidden input
- Ken Burns zoom in ffmpeg: `zoompan=z='min(zoom+0.001,1.3)':d=FRAMES:s=1920x1080:fps=25`
- Video skill supports: zoom in/out, horizontal pan, vertical scroll (for code), static, and combinations
- `find_code_segments` had a bug: called `get_youtube_transcript()` with default `format="text"` then did `json.loads()` — fixed to use `format="segments"`

## Session Log

- 2026-03-02: First session with personality setup. Analyzed Wes Roth video. Fixed YouTube transcript tool. Created SOUL.md, CLAUDE.md, and this memory file.
- 2026-03-04: Converted MCP servers to skill-based CLI tools. Created supernova explainer video (5 scenes + narration + Ken Burns effects). Tested YouTube Studio upload via browser automation. Updated video skill with motion effect docs. Moved memory to project-local `.claude/memory/`.
