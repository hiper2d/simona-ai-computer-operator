---
name: ltx-video
description: Generate AI videos using LTX-2.3 API. Supports image-to-video with audio at up to 4K. Synchronous API — no polling needed. Use when the user asks to generate a video with LTX.
argument-hint: <image path> [--prompt "motion description"] [--duration 6] [--resolution 1920x1080] [--fast] [--no-audio]
allowed-tools: Bash, Read, Glob
---

Generate video with LTX: $ARGUMENTS

## How it works

Uses the LTX Video API to generate videos from images. The API is **synchronous** — it returns the MP4 directly in the response (no polling). Supports image-to-video with AI-generated audio.

## Models

| Model | ID | Quality | Cost (1080p) | Cost (1440p) | Cost (4K) |
|-------|----|---------|--------------|--------------|-----------|
| **2.3 Pro** | `ltx-2-3-pro` | Best | $0.06/s | $0.12/s | $0.24/s |
| **2.3 Fast** | `ltx-2-3-fast` | Good | $0.04/s | $0.08/s | $0.16/s |

Default: **ltx-2-3-pro**. Use `--fast` flag for the fast model.

## Supported resolutions

| Label | Landscape | Portrait |
|-------|-----------|----------|
| 1080p | `1920x1080` | `1080x1920` |
| 1440p | `2560x1440` | `1440x2560` |
| 4K | `3840x2160` | `2160x3840` |

## Default settings

- **Model**: ltx-2-3-pro
- **Duration**: 6 seconds (minimum is 6s, max 10s for pro, 20s for fast at 1080p)
- **Resolution**: 1920x1080
- **FPS**: 24
- **Audio**: enabled (AI-generated)

Override with flags in $ARGUMENTS:
- `--duration N` — 6 to 10 seconds (pro) or 6 to 20 seconds (fast at 1080p)
- `--fast` — use ltx-2-3-fast instead of pro
- `--resolution WxH` — e.g. `--resolution 2560x1440`
- `--portrait` — use portrait orientation (swap width/height)
- `--no-audio` — disable audio generation
- `--camera MOTION` — camera motion: dolly_in, dolly_out, dolly_left, dolly_right, jib_up, jib_down, static, focus_shift
- `--prompt "text"` — motion/scene description
- `--fps N` — 24, 25, 48, or 50

## Steps

1. Parse $ARGUMENTS to extract the image path, prompt, and flags.

2. Read the API key from `.env` (variable `LTX_K`).

3. Upload the image to LTX storage:

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
export $(grep LTX_K .env | xargs) && \

# Step 1: Get a signed upload URL
UPLOAD_RESPONSE=$(curl -s -X POST "https://api.ltx.video/v1/upload" \
  -H "Authorization: Bearer $LTX_K" \
  -H "Content-Type: application/json") && \
UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.upload_url') && \
STORAGE_URI=$(echo "$UPLOAD_RESPONSE" | jq -r '.storage_uri') && \
CONTENT_RANGE=$(echo "$UPLOAD_RESPONSE" | jq -r '.required_headers["x-goog-content-length-range"]') && \

# Step 2: PUT the image to the signed URL
curl -s -o /dev/null -w "%{http_code}" -X PUT "$UPLOAD_URL" \
  -H "x-goog-content-length-range: $CONTENT_RANGE" \
  -H "Content-Type: image/png" \
  --data-binary @IMAGE_PATH && \
echo "Uploaded: $STORAGE_URI"
```

4. Generate the video (synchronous — returns MP4 directly):

```bash
MODEL="ltx-2-3-pro"  # or "ltx-2-3-fast" if --fast flag
RESOLUTION="1920x1080"
DURATION=6
FPS=24
GENERATE_AUDIO=true

curl -s -X POST "https://api.ltx.video/v1/image-to-video" \
  -H "Authorization: Bearer $LTX_K" \
  -H "Content-Type: application/json" \
  -o generated-videos/SLUG.mp4 \
  -w "\nHTTP_CODE:%{http_code}\nSIZE:%{size_download}" \
  -d '{
    "image_uri": "'"$STORAGE_URI"'",
    "prompt": "PROMPT_HERE",
    "model": "'"$MODEL"'",
    "duration": '"$DURATION"',
    "resolution": "'"$RESOLUTION"'",
    "fps": '"$FPS"',
    "generate_audio": '"$GENERATE_AUDIO"'
  }'
```

**IMPORTANT**: This call is synchronous and may take 1-3 minutes. Use a timeout of at least 300000ms (5 min).

If using `--camera` flag, add `"camera_motion": "MOTION_VALUE"` to the JSON body.

5. Verify the output:

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate \
  -show_entries format=duration -of csv=p=0 generated-videos/SLUG.mp4
```

6. **ALWAYS** log the API call to `api-spending.csv`:

```bash
DURATION=6  # actual duration
MODEL="ltx-2-3-pro"  # or "ltx-2-3-fast"
RESOLUTION="1920x1080"

# Cost per second based on model and resolution
# Pro:  1080p=$0.06, 1440p=$0.12, 4K=$0.24
# Fast: 1080p=$0.04, 1440p=$0.08, 4K=$0.16
RATE=0.06  # adjust based on model and resolution
COST=$(python3 -c "print(round($DURATION * $RATE, 3))")

echo "$(date +%Y-%m-%dT%H:%M:%S%z),ltx-video,${MODEL},video,SLUG,$COST" >> api-spending.csv
```

7. Report the file path, duration, resolution, and cost to the user.

## Output directory

Videos are saved to `generated-videos/` in the project root.

## API gotchas

- **Auth format**: `Authorization: Bearer YOUR_KEY` — standard Bearer scheme
- **Synchronous API**: No polling! The response IS the video file (application/octet-stream)
- **Upload is two-step**: POST to `/v1/upload` to get a signed GCS URL, then PUT the file there. Use the `storage_uri` (ltx:// scheme) as `image_uri` in the generation call
- **Minimum duration is 6 seconds** — unlike Kling (3s min)
- **Resolution must be exact pixels** — use `1920x1080` not `1080p`
- **Duration is a number**, not a string (unlike Kling)
- **Error responses are JSON** even though success is binary — check HTTP status code
- **422 = safety filter** — rephrase the prompt if you get this

## Prompt tips

- Describe the **motion** you want, not the image content
- Include speech if relevant: "she says: Hello world"
- Camera motions can be set via the `camera_motion` parameter instead of in the prompt
- For talking head videos: describe facial expressions and mouth movement

## Audio-to-video (audio-driven video generation)

LTX has a separate **Audio-to-Video** model (launched Jan 2026, ElevenLabs partnership) that takes audio as the primary input + optional image + text prompt to generate synchronized video.

**Not yet implemented as a skill.** Key specs from research:
- Audio-driven: provide voice/music/SFX audio → video synced to it
- Supports lip sync and ambient audio matching
- Duration: up to 20s (matches audio length)
- Native 4K at 50fps
- Supports music-to-video (visualizations, lyric videos)

This is different from the standard LTX image-to-video (which only generates native audio, doesn't accept audio input). When Alex gets access, create a separate skill or extend this one.

## When to use LTX vs Kling vs Veo vs ffmpeg

- **LTX Pro (this skill)**: **Drafts**. $0.36 for 6s at 1080p. Fast iteration — synchronous API, no polling.
- **Seedance 1.5 Pro**: **Final quality**. ~$0.58 for 5s at 1080p. Comparable to Kling.
- **Kling Pro**: **Final quality**. $0.70 for 5s at 1080p. Comparable to Seedance.
- **Veo**: Most expensive ($3.20 for 8s). Only for text-to-video (no input image).
- **ffmpeg**: Free, instant. Camera motion over static images.
