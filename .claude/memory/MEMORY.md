# Simona's Memory

## Project Notes

- `mcp/` directory name is a leftover — may rename to `tools/` eventually
- Dependencies: httpx, websockets, youtube-transcript-api, yt-dlp (managed by uv)

## Key Learnings

- YouTube Studio upload via browser automation works: navigate to studio.youtube.com → Create → Upload videos → use `DOM.setFileInputFiles` CDP method to inject file into hidden input
- Ken Burns zoom in ffmpeg: `zoompan=z='min(zoom+0.001,1.3)':d=FRAMES:s=1920x1080:fps=25`
- Video skill supports: zoom in/out, horizontal pan, vertical scroll (for code), static, and combinations
- `find_code_segments` had a bug: called `get_youtube_transcript()` with default `format="text"` then did `json.loads()` — fixed to use `format="segments"`

## Session Log

- 2026-03-02: First session. Personality setup (SOUL.md), CLAUDE.md, memory. Analyzed Wes Roth video. Fixed YouTube transcript tool.
- 2026-03-04: Converted MCP servers to skill-based CLI tools. Created supernova explainer video. Tested YouTube Studio upload via browser automation. Moved memory to project-local `.claude/memory/`.
- 2026-03-07: Removed custom worker loop (replaced by Claude Code's built-in loop). Cleaned up memory and CLAUDE.md.
