# Simona's Memory

## Project Notes

- `mcp/` directory name is a leftover — may rename to `tools/` eventually
- Dependencies: httpx, websockets, youtube-transcript-api, yt-dlp (managed by uv)

## Key Learnings

- YouTube Studio upload via browser automation works: navigate to studio.youtube.com → Create → Upload videos → use `DOM.setFileInputFiles` CDP method to inject file into hidden input
- Ken Burns zoom: use 8K internal resolution (7680x4320) + downscale to 1080p to fix zoompan jitter on ANY direction (center, diagonal, etc). 4K works for center zoom only; diagonal/pan movements need 8K
- Video skill supports: zoom in/out, horizontal pan, vertical scroll (for code), static, sectioned scroll, animated highlights
- Sectioned scroll: for tall pages (>3000px), crop into sections and scroll each slowly (~80-120 px/s) instead of one fast continuous scroll
- Highlight tool (`mcp/highlight/cli.py`): config-driven animated SVG borders on DOM elements via CDP. Frame-by-frame capture with paused Web Animations API. Reusable across any web page.
- CDP full-page screenshots: use `max_size=20*1024*1024` on websocket (default too small for tall pages)
- `find_code_segments` had a bug: called `get_youtube_transcript()` with default `format="text"` then did `json.loads()` — fixed to use `format="segments"`
- Veo 3.1 API: use `bytesBase64Encoded` for images (NOT `inlineData`/`fileData`). `durationSeconds` must be a number, only 4/6/8 accepted. Costs $0.40/s ($3.20 per 8s clip at 720p)
- ElevenLabs voice: **Lily** (`pFZP5JQG7iQjIQuC4Bku`) — velvety British, stability=0.35, style=0.6. Preferred over Sarah for longer narration (deeper, more natural). Use informal, discovery-oriented narration style — not tutorial/guide tone
- Video concat audio sync: all clips must use `-ar 48000 -ac 2 -c:a aac -b:a 192k`. Mismatched sample rates cause audio drift
- Background music volume: use `volume=0.04` (4%) under narration. Narration stays at 1.0. This applies to any ambient/background audio — original video sounds, music, etc. Just enough to feel without competing with voice.
- xfade requires matching fps between clips. Veo outputs 24fps, our standard is 25fps — convert with `fps=25` filter
- Single narration over visual transitions: build combined visual track first (xfade), then lay audio on top. Avoids voice cuts at scene boundaries
- Keep reusable intermediates in `/tmp/video-assets/` during iteration, clean up with `/cleanup` skill when done

## Feedback
- Always ask Alex which AI video model to use before generating — don't auto-pick
- Static images are too dry — use "animate + extend" technique: gen-AI short clip (5-6s) → crossfade back to ORIGINAL source image → extend with static zoom/pan effect. NEVER freeze on AI animation's last frame (unpredictable poses, closed eyes). Always crossfade to the clean source image. Aim for 2-3 AI video clips per video. Use 1-2 Kling (faces, hero shots) + LTX for the rest (cheap, good for non-face content).
- YouTube shows ads — always skip/wait for ads before capturing screenshots. Never include ad content in video captures.

## Session Log

- 2026-03-02: First session. Personality setup (SOUL.md), CLAUDE.md, memory. Analyzed Wes Roth video. Fixed YouTube transcript tool.
- 2026-03-04: Converted MCP servers to skill-based CLI tools. Created supernova explainer video. Tested YouTube Studio upload via browser automation. Moved memory to project-local `.claude/memory/`.
- 2026-03-07: Removed custom worker loop (replaced by Claude Code's built-in loop). Cleaned up memory and CLAUDE.md.
- 2026-03-10: Built highlight capture tool (`mcp/highlight/`). Config-driven animated SVG borders on web pages. Updated video skill with sectioned scroll and highlight integration. Werewolf game review video v3.
- 2026-03-11: Added Veo 3.1 skill, ElevenLabs TTS skill. Created director skill (orchestrates all video production) and cleanup skill. Produced werewolf review v8 with Veo intro + crossfade + highlight walkthrough. Alex chose Sarah as ElevenLabs voice.
- 2026-03-12: Fixed zoompan center-zoom jitter (4K internal res trick). Renamed skills: image→nanobanana, video→ffmpeg, voice→gemini-voice, highlight→webpage-highlight. Updated README. Produced v11 with 4-image slideshow intro (crossfades) + Veo clips.
- 2026-03-14: Added `type` and `select` actions to highlight tool (React-aware typing + dropdown changes). Fixed 3 highlight bugs: sticky nav offset, generic selectors after scroll, viewport reset wiping React state. Produced werewolf game creation walkthrough video (13 scenes, 70s). Updated ElevenLabs skill: Gemini for drafts, ElevenLabs only for final cuts.
- 2026-03-15–18: Full werewolf preview video (2:06, final: `werewolf-full-preview-lily-v2.mp4`). Seedance talking head + slideshow + app showcase. Switched from Sarah to Lily voice (deeper, British). Switched narration style from tutorial to casual/discovery. Major editing learnings saved to director skill (scene planning, pacing, audio, scrolling rules). Added `center` scroll + auto overlay cleanup to highlight tool. Transcripts stored in `generated-videos/transcripts/`.
