# Simona's Memory

## Project Notes

- `mcp/` directory name is a leftover — may rename to `tools/` eventually
- Dependencies: httpx, websockets, youtube-transcript-api, yt-dlp, kokoro-onnx, soundfile, numpy (managed by uv)
- Local TTS: `mcp/kokoro/` + `.claude/skills/kokoro/` + `.claude/hooks/speak-response.sh` (Stop hook). Reads my responses aloud via Kokoro-82M on CPU. Control via `simona <mute|unmute|stop|pause|continue|replay|status>` (CLI in `mcp/simona/cli.py`, sourced from `mcp/kokoro/aliases.sh`). Same verbs work in chat as whole-prompt phrases via `voice-control.sh`. See skill doc for details.

## Key Learnings

- Hyperrealistic image prompts: adding camera specs (Canon EOS R5, 35mm, f/2.8), technical details (8k, raw), skin/texture cues (subsurface scattering, pores visible, stray hairs, fabric texture, dust particles), and specific lighting setups (direct overhead sunlight, candlelight with soft orange fill) massively improves realism over generic "highly detailed" prompts. Works with Gemini Flash Image model.
- YouTube Studio upload via browser automation works: navigate to studio.youtube.com → Create → Upload videos → use `DOM.setFileInputFiles` CDP method to inject file into hidden input
- Ken Burns zoom: use 4K internal resolution (3840x2160) + downscale to 1080p to fix zoompan jitter. Do NOT use 8K — it causes frame count bugs on some images leading to zoom-reset loops. Always prescale separately + use `-frames:v N` hard cap.
- Video skill supports: zoom in/out, horizontal pan, vertical scroll (for code), static, sectioned scroll, animated highlights
- Sectioned scroll: for tall pages (>3000px), crop into sections and scroll each slowly (~80-120 px/s) instead of one fast continuous scroll
- Highlight tool (`mcp/highlight/cli.py`): config-driven animated SVG borders on DOM elements via CDP. Frame-by-frame capture with paused Web Animations API. Reusable across any web page.
- CDP full-page screenshots: use `max_size=20*1024*1024` on websocket (default too small for tall pages)
- `find_code_segments` had a bug: called `get_youtube_transcript()` with default `format="text"` then did `json.loads()` — fixed to use `format="segments"`
- Veo 3.1 API: use `bytesBase64Encoded` for images (NOT `inlineData`/`fileData`). `durationSeconds` must be a number, only 4/6/8 accepted. Costs $0.40/s ($3.20 per 8s clip at 720p)
- ElevenLabs voice: **Lily** (`pFZP5JQG7iQjIQuC4Bku`) — velvety British, stability=0.5, style=0.6. Use `eleven_multilingual_v2` model (NOT turbo — turbo causes artifacts around names/pauses). Avoid em dashes in text near names. Preferred over Sarah for longer narration (deeper, more natural). Use informal, discovery-oriented narration style — not tutorial/guide tone
- Video concat audio sync: all clips must use `-ar 48000 -ac 2 -c:a aac -b:a 192k`. Mismatched sample rates cause audio drift
- Background music volume: use `volume=0.04` (4%) under narration. Narration stays at 1.0. This applies to any ambient/background audio — original video sounds, music, etc. Just enough to feel without competing with voice.
- xfade requires matching fps between clips. Veo outputs 24fps, our standard is 25fps — convert with `fps=25` filter
- xfade + acrossfade MUST use the same duration. Mismatched durations cause progressive audio/video drift (frozen slides bug). Add 0.5s silence bookends to audio chunks: pad END of all chunks, pad START of all chunks except the first. This way acrossfade blends silence-to-silence and speech always plays at full volume.
- Voice post-processing for character voices: pitch down 15% (`asetrate=44100*0.85,aresample=44100`) + hall echo (`aecho=0.8:0.7:40:0.3`). George (ElevenLabs British storyteller) pitched down makes a great werewolf narrator.
- When extending Kling clips to cover longer audio: freeze LAST frame + zoom (not source image). Extract last frame with `ffmpeg -ss <near_end> -vframes 1`, then zoompan on it, crossfade from Kling clip.
- Gemini TTS outputs raw PCM (audio/L16, 24kHz mono). Convert with: `ffmpeg -f s16le -ar 24000 -ac 1 -i input.pcm output.wav`
- Keep reusable intermediates in `/tmp/video-assets/` during iteration, clean up with `/cleanup` skill when done
- Cursor click animation tool: `mcp/cursor/animate.py` — overlays a moving cursor on a screenshot with button highlight on click. Use `--total-duration` to place click at end of segment (creates "click → next page" transition). Use `--button X,Y,W,H` for full button highlight.
- Browser viewport for video: always `uv run python mcp/browser/cli.py viewport 1920x1080 --scale 1` before capturing. Screenshots are 2x retina (3840x2160) — downscale with `scale=1920:1080:flags=lanczos`. CSS pixel coords from JS map 1:1 to image pixels after downscale.
- App walkthrough scroll: capture full page with `cdp "Page.captureScreenshot" '{"captureBeyondViewport":true,...}'`, scale to 1920 width, use `crop` filter with time-based y expression. Get element positions via JS `getBoundingClientRect()` + `scrollY`.
- OpenAI gpt-image-2: great for thematic/conceptual images (VS battles, corporate scenes, campsite day/night). Use 1792x1024 landscape. Always prescale to 7680x4320 before zoompan to avoid frame count bugs.
- Browser screenshots on retina Mac: `Page.captureScreenshot` always captures at 2x regardless of `Emulation.setDeviceMetricsOverride` deviceScaleFactor. To get clean 1280-wide README screenshots, capture as-is (returns 2560x1600) then `sips -z H W input.png --out output.png` to downscale. Helper: `bash /tmp/capture.sh <name>.png` writes 1280x800 PNGs straight into the target folder.
- Werewolf game UI scrolls inside `<main>` (not document body). To scroll the chat: `document.querySelector('main').scrollTop = N`. Day selector is a `<button>` with text "Day N" — clicking opens a dropdown with each day as a `<button>` text "Day X"; past days load read-only ("Day N history" banner).

## Feedback
- Always ask Alex which AI video model to use before generating — don't auto-pick
- Static images are too dry — use "animate + extend" technique: gen-AI short clip (5-6s) → crossfade to last frame + zoom/pan effect. Aim for 2-3 AI video clips per video. Use 1-2 Kling (faces, hero shots) + LTX for the rest (cheap, good for non-face content).
- YouTube shows ads — always skip/wait for ads before capturing screenshots. Never include ad content in video captures.

## Personal
- [Horror Games Wishlist](horror_games_wishlist.md) — Games Alex wants to play, for research and picking
- [USF MS in AI Application](usf_ms_ai_application.md) — Alex applying to USF Tampa MS in AI. Full plan in `.claude/skills/usf-application/SKILL.md`.

## Active Conversations (read these to pick up mid-discussion)
- [2026-05-05: AI consciousness documentary](conversations/2026-05-05_ai-consciousness-doc.md) — Discussing Cameron Berg AE Studio doc. Last topic: long-loop + memory predictions. Alex wants to continue.

## Session Log

- 2026-03-02: First session. Personality setup (SOUL.md), CLAUDE.md, memory. Analyzed Wes Roth video. Fixed YouTube transcript tool.
- 2026-03-04: Converted MCP servers to skill-based CLI tools. Created supernova explainer video. Tested YouTube Studio upload via browser automation. Moved memory to project-local `.claude/memory/`.
- 2026-03-07: Removed custom worker loop (replaced by Claude Code's built-in loop). Cleaned up memory and CLAUDE.md.
- 2026-03-10: Built highlight capture tool (`mcp/highlight/`). Config-driven animated SVG borders on web pages. Updated video skill with sectioned scroll and highlight integration. Werewolf game review video v3.
- 2026-03-11: Added Veo 3.1 skill, ElevenLabs TTS skill. Created director skill (orchestrates all video production) and cleanup skill. Produced werewolf review v8 with Veo intro + crossfade + highlight walkthrough. Alex chose Sarah as ElevenLabs voice.
- 2026-03-12: Fixed zoompan center-zoom jitter (4K internal res trick). Renamed skills: image→nanobanana, video→ffmpeg, voice→gemini-voice, highlight→webpage-highlight. Updated README. Produced v11 with 4-image slideshow intro (crossfades) + Veo clips.
- 2026-03-14: Added `type` and `select` actions to highlight tool (React-aware typing + dropdown changes). Fixed 3 highlight bugs: sticky nav offset, generic selectors after scroll, viewport reset wiping React state. Produced werewolf game creation walkthrough video (13 scenes, 70s). Updated ElevenLabs skill: Gemini for drafts, ElevenLabs only for final cuts.
- 2026-03-15–18: Full werewolf preview video (2:06, final: `werewolf-full-preview-lily-v2.mp4`). Seedance talking head + slideshow + app showcase. Switched from Sarah to Lily voice (deeper, British). Switched narration style from tutorial to casual/discovery. Major editing learnings saved to director skill (scene planning, pacing, audio, scrolling rules). Added `center` scroll + auto overlay cleanup to highlight tool. Transcripts stored in `generated-videos/transcripts/`.
- 2026-03-18–19: "Meet Simona" channel intro video (4:08). 11 iterations (v1–v11). Key production learnings: animate+extend technique (AI clip → crossfade to original image → static effect), 8K zoompan for all directions, background music at 4% volume, skip YouTube ads before capture, use `eleven_multilingual_v2` not turbo. Updated nanobanana skill with multi-reference (3 images) + imageConfig from Gemini guide. Generated consistent Simona images (over-shoulder, server-room, presenting-v3). Final: `simona-intro-v11-lily.mp4` (Lily) + `simona-intro-v9-gemini.mp4` (Gemini).
- 2026-05-05: Built local Kokoro TTS skill + Stop hook to read responses aloud (auto-TTS without API cost). Sentence-streamed via afplay, ~2× realtime on Apple Silicon.
- 2026-04-19–27: Werewolf rules video v3 (`video-projects/werewolf-rules-v3/`). 17 iterations. Built 3 new video effects: cursor click animation, dropdown scroll slideshow, scroll-to-element + highlight. Added `viewport` and `cdp` commands to browser CLI. Two slideshow types: synced (per-slide voice) and unsynced (one voice over all). Seedance start+end frame interpolation for dark→light reveal. OpenAI gpt-image-2 for thematic images. Current draft: v17 (~1:40, Gemini draft voice). Still needs: in-game footage, special roles section, final ElevenLabs voice, outro.
