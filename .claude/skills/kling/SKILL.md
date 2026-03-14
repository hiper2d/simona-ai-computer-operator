---
name: kling
description: Generate AI videos using Kling-3 (O3) via fal.ai API. Supports image-to-video with standard (720p) and pro (1080p) quality tiers. Use when the user asks to generate a video with Kling or fal.ai.
argument-hint: <image path> [--prompt "motion description"] [--duration 5] [--pro] [--no-audio]
allowed-tools: Bash, Read, Glob
---

Generate video with Kling: $ARGUMENTS

## How it works

Uses the fal.ai queue API to generate videos with Kling-3 (O3). Supports image-to-video: provide a starting image and an optional motion prompt. The API is async — submit to queue, poll status, fetch result.

## Quality tiers

| Tier | Endpoint | Resolution | Cost (audio off) | Cost (audio on) |
|------|----------|------------|-------------------|------------------|
| **Standard** | `fal-ai/kling-video/o3/standard/image-to-video` | ~720p (1300x708) | $0.084/s | $0.112/s |
| **Pro** | `fal-ai/kling-video/o3/pro/image-to-video` | 1080p | $0.112/s | $0.14/s |

Default: **pro** (1080p). Use `--standard` flag to downgrade if needed.

## Default settings

- **Tier**: pro (1080p)
- **Duration**: 5 seconds
- **Audio**: enabled (native audio generation)
- **Negative prompt**: "blur, distort, and low quality"
- **cfg_scale**: 0.5

Override with flags in $ARGUMENTS:
- `--duration N` — 3 to 15 seconds
- `--standard` — use standard tier (~720p) instead of pro
- `--no-audio` — disable audio generation
- `--prompt "text"` — motion/scene description

## Steps

1. Parse $ARGUMENTS to extract the image path, prompt, and flags.

2. Read the API key from `.env` (variable `FAL_K`).

3. Upload the image to fal.ai storage:

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
export $(grep FAL_K .env | xargs) && \
UPLOAD_RESPONSE=$(curl -s -X POST "https://rest.alpha.fal.ai/storage/upload/initiate" \
  -H "Authorization: Key ${FAL_K}" \
  -H "Content-Type: application/json" \
  -d '{"file_name": "INPUT_FILENAME", "content_type": "image/png"}') && \
FILE_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.file_url') && \
UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.upload_url') && \
curl -s -X PUT "$UPLOAD_URL" \
  -H "Content-Type: image/png" \
  --data-binary @IMAGE_PATH && \
echo "Uploaded: $FILE_URL"
```

4. Submit the video generation job to the queue:

```bash
TIER="pro"  # or "standard" if --standard flag
ENDPOINT="fal-ai/kling-video/o3/${TIER}/image-to-video"

RESPONSE=$(curl -s -X POST "https://queue.fal.run/${ENDPOINT}" \
  -H "Authorization: Key ${FAL_K}" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "'"$FILE_URL"'",
    "prompt": "PROMPT_HERE",
    "duration": "5",
    "generate_audio": true,
    "negative_prompt": "blur, distort, and low quality",
    "cfg_scale": 0.5
  }')

REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id')
echo "Submitted: $REQUEST_ID"
```

**IMPORTANT**: The `duration` value is a **string**, not a number (e.g. `"5"` not `5`).

5. Poll for completion (typically 1-3 min):

```bash
curl -s "https://queue.fal.run/fal-ai/kling-video/requests/${REQUEST_ID}/status" \
  -H "Authorization: Key ${FAL_K}"
```

Poll every 30 seconds. When `"status": "COMPLETED"`, proceed.

6. Fetch the result:

```bash
RESULT=$(curl -s "https://queue.fal.run/fal-ai/kling-video/requests/${REQUEST_ID}" \
  -H "Authorization: Key ${FAL_K}")
VIDEO_URL=$(echo "$RESULT" | jq -r '.video.url')
```

7. Download the video:

```bash
mkdir -p generated-videos
curl -s -o generated-videos/SLUG.mp4 "$VIDEO_URL"
```

8. Verify the output:

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate \
  -show_entries format=duration -of csv=p=0 generated-videos/SLUG.mp4
```

9. **ALWAYS** log the API call to `api-spending.csv`:

```bash
DURATION=5  # actual duration used
AUDIO=true  # whether audio was enabled
TIER="standard"  # or "pro"

# Calculate cost
if [ "$TIER" = "pro" ]; then
  RATE=$([ "$AUDIO" = "true" ] && echo "0.14" || echo "0.112")
else
  RATE=$([ "$AUDIO" = "true" ] && echo "0.112" || echo "0.084")
fi
COST=$(python3 -c "print(round($DURATION * $RATE, 3))")

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),fal-ai,kling-video-o3-${TIER},video,SLUG,$COST" >> api-spending.csv
```

10. Report the file path, duration, resolution, and cost to the user.

## Output directory

Videos are saved to `generated-videos/` in the project root.

## API gotchas

- **Auth format**: `Authorization: Key YOUR_KEY` — uses "Key" scheme, not "Bearer"
- **`duration` is a string** — `"5"` not `5`
- **Upload is two-step**: initiate (POST to get signed URL) then PUT the file
- **Queue is async**: submit returns a request_id, poll status endpoint, then fetch result
- **Status/result endpoints** use the base model path (`fal-ai/kling-video`), not the full tier path
- **Standard tier outputs non-standard resolution** (~1300x708), not clean 1280x720
- **Pro tier outputs 1080p** — use when quality matters

## Prompt tips

- Describe the **motion** you want, not the image content: "gentle head turn, soft breathing"
- Include atmosphere: "cinematic lighting", "ambient movement"
- Keep it focused — Kling works best with clear, specific motion descriptions
- For subtle animation of portraits: "slight head movement, blinking, gentle breathing motion"

## When to use Kling vs Veo vs ffmpeg

- **LTX Pro**: **Drafts**. $0.36 for 6s at 1080p. Cheap iteration.
- **Seedance 1.5 Pro**: **Final quality**. ~$0.58 for 5s at 1080p. Comparable to Kling.
- **Kling Pro (this skill)**: **Final quality**. $0.70 for 5s at 1080p. Comparable to Seedance.
- **Veo**: Most expensive ($3.20 for 8s). Only for text-to-video (no input image).
- **ffmpeg**: Free, instant. Camera motion over static images.
