---
name: youtube
description: Analyze YouTube videos — extract transcripts, detect code segments, capture frames, and reconstruct code files shown in videos. Use when the user shares a YouTube URL or asks to extract content from a video.
argument-hint: <url> [focus instructions]
allowed-tools: Read, Write, Glob, Grep
---

Analyze the YouTube video at: $ARGUMENTS

The first argument is the URL. Any text after the URL is **user instructions** describing what to focus on or extract (e.g., specific code files, configs, techniques, "summarize", "what is this about"). If no extra instructions are given, extract everything relevant you find.

Extract the video ID from the URL (the `v=` parameter or the path after `youtu.be/`).

## Determine the task type

Choose the right workflow based on the user's request:

- **Summary / Analysis** — user wants to understand what the video is about, key points, opinions → Phase A
- **Code extraction** — user wants code files, configs, scripts shown in the video → Phase B
- **Both** — user wants full analysis plus code → Phase A then Phase B

## Phase A: Summary & Analysis (for discussion/news/tutorial videos)

1. Call `get_youtube_transcript` with `format="text"` to get the compact plain-text transcript.
   - For very long videos (>30 min), fetch in chunks using `start_time`/`end_time` to stay within context limits.
2. Read the full text and produce:
   - **Summary** — 3–5 sentence overview of the video content
   - **Key points** — Bulleted list of the main arguments, news items, or insights
   - **Notable quotes** — Any striking or important statements
   - **Context** — Background needed to understand the discussion

Skip saving files unless the user asks — just present the analysis inline.

## Phase B: Code Extraction (for coding/tutorial videos)

**Approach A: MCP Tools (automated, for batch extraction)**
1. Call `get_youtube_transcript` with `format="text"` for overall context
2. Call `find_code_segments` to identify time ranges where code is likely shown
3. Call `get_video_frames` for each high-confidence segment to extract frames
4. Read the frame images to extract code or analyze visual content

**Approach B: Chrome Browser (interactive, for exploration)**
1. Open the video at a specific timestamp: https://www.youtube.com/watch?v=VIDEO_ID&t=SECONDS
2. Pause the video and take a screenshot
3. Read the screenshot to extract code or content
4. Seek to next timestamp and repeat

Ask the user which approach they prefer, or recommend Approach A for thorough analysis and Approach B for quick spot-checks.

### Save Extracted Files

After extraction, save all code content to disk using the Write tool.

**Output directory naming:** Use the format `youtube-extracts/<short-name>_<video-id>/` where `<short-name>` is a concise kebab-case slug (2-4 words) derived from the video topic and user instructions. Examples:
- `youtube-extracts/ralph-loop-claude_eD4CEZ-_-sk/`
- `youtube-extracts/fastapi-auth-tutorial_abc123/`

The video ID suffix ensures uniqueness; the short name makes the folder scannable.

1. **`summary.md`** — Video summary including:
   - Video title and URL
   - Overall description of the video content
   - Key timestamps with descriptions of what happens
   - Key takeaways or insights

2. **`transcript.json`** — The full raw transcript (use `format="segments"` with time-range chunks if needed)

3. **Code files** — Any code, scripts, configs, or structured text extracted from video frames:
   - Use the filename shown in the video if visible (e.g., `ralph.sh`, `config.yaml`, `main.py`)
   - If the filename isn't visible, infer a reasonable name from the content and language
   - Extract the code as accurately as possible from the frames
   - **Fill in the gaps:** If a file is only partially visible, reconstruct using context from the transcript, visible fragments, and your knowledge. Mark reconstructed sections with `# Reconstructed from context — not shown in video`.
   - Pay special attention to the **user instructions** — prioritize what the user cares about most.

## Phase C: Report

After completing analysis, print:
- A summary or the output directory path (depending on task type)
- A list of all created files with brief descriptions (if files were saved)
- Key timestamps where important content appears
- Any code found (properly formatted in code blocks inline)
- Which parts of code files were directly extracted vs. reconstructed
