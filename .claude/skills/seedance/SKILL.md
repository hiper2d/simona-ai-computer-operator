---
name: seedance
description: Generate AI videos using Seedance 1.5 Pro (ByteDance) via fal.ai API. Supports image-to-video with native audio at up to 1080p. Use when the user asks to generate a video with Seedance.
argument-hint: <image path> [--prompt "motion description"] [--duration 5] [--resolution 1080p] [--no-audio]
allowed-tools: Bash, Read, Glob
---

Generate video with Seedance: $ARGUMENTS

## How it works

Uses the fal.ai queue API to generate videos with Seedance 1.5 Pro (ByteDance). Supports image-to-video with native audio generation. The API is async — submit to queue, poll status, fetch result.

## Model

| Model | ID | Resolution | Cost (with audio) | Cost (no audio) |
|-------|----|------------|--------------------|-----------------|
| **1.5 Pro** | `fal-ai/bytedance/seedance/v1.5/pro/image-to-video` | up to 1080p | ~$0.58/5s 1080p | ~$0.29/5s 1080p |

Pricing formula: tokens = `(height × width × FPS × duration) / 1024`. With audio: $2.4/1M tokens. Without audio: $1.2/1M tokens.

## Default settings

- **Resolution**: 1080p
- **Duration**: 5 seconds (supports 4-12s)
- **Audio**: enabled (native audio generation)
- **Aspect ratio**: 16:9
- **FPS**: 24

Override with flags in $ARGUMENTS:
- `--duration N` — 4 to 12 seconds
- `--resolution RES` — 480p, 720p, or 1080p
- `--aspect RATIO` — 21:9, 16:9, 4:3, 1:1, 3:4, 9:16, auto
- `--no-audio` — disable audio generation
- `--camera-fixed` — lock camera position
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
RESPONSE=$(curl -s -X POST "https://queue.fal.run/fal-ai/bytedance/seedance/v1.5/pro/image-to-video" \
  -H "Authorization: Key ${FAL_K}" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "'"$FILE_URL"'",
    "prompt": "PROMPT_HERE",
    "resolution": "1080p",
    "duration": "5",
    "generate_audio": true,
    "aspect_ratio": "16:9"
  }')

REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id')
echo "Submitted: $REQUEST_ID"
```

5. Poll for completion (typically 2-4 min):

```bash
curl -s "https://queue.fal.run/fal-ai/bytedance/requests/${REQUEST_ID}/status" \
  -H "Authorization: Key ${FAL_K}"
```

Poll every 60 seconds. When `"status": "COMPLETED"`, proceed.

6. Fetch the result:

```bash
RESULT=$(curl -s "https://queue.fal.run/fal-ai/bytedance/requests/${REQUEST_ID}" \
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
DURATION=5  # actual duration
RESOLUTION="1080p"
AUDIO=true

# Calculate cost via token formula
# tokens = (height * width * fps * duration) / 1024
# With audio: $2.4/1M tokens, without: $1.2/1M tokens
# 5s 1080p with audio ≈ $0.58
COST=0.58  # adjust based on resolution/duration/audio

echo "$(date +%Y-%m-%dT%H:%M:%S%z),fal-ai,seedance-v1.5-pro-i2v,video,SLUG,$COST" >> api-spending.csv
```

10. Report the file path, duration, resolution, and cost to the user.

## Output directory

Videos are saved to `generated-videos/` in the project root.

## API gotchas

- **Auth format**: `Authorization: Key YOUR_KEY` — uses "Key" scheme, not "Bearer"
- **Queue is async**: submit returns request_id, poll status, then fetch result
- **Status/result endpoints** use `fal-ai/bytedance/requests/` path (not the full model path)
- **Duration is a string** — `"5"` not `5`
- **Slower inference** than Kling (~3-4 min vs ~2 min) but produces true 1920x1080
- **Native audio** — generates speech-synced audio when `generate_audio: true`
- **Supports end frame** — use `end_image_url` to interpolate between two images

## Prompt tips

- Describe the **motion** you want, not the image content
- Include speech if relevant: "she says: Hello world"
- For talking head: describe facial expressions and tone
- Negative prompt not needed (no parameter for it in 1.5)

## When to use Seedance vs other models

- **LTX Pro**: Cheapest, good for drafts. $0.36/6s. Synchronous API.
- **Seedance 1.5 Pro (this skill)**: Great quality with native audio. ~$0.58/5s at 1080p. Comparable to Kling.
- **Kling Pro**: Best motion quality. $0.70/5s at 1080p. Comparable to Seedance.
- **Veo**: Most expensive ($3.20/8s). Only for text-to-video (no input image).
- **ffmpeg**: Free, instant. Camera motion over static images.
