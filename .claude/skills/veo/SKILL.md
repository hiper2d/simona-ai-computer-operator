---
name: veo
description: Generate short AI videos using Google Veo 3.1 API. Use when the user asks to animate an image, generate a video clip from a prompt, or create AI-generated video content.
argument-hint: <prompt or image path> [--duration 8] [--aspect 16:9] [--resolution 720p]
allowed-tools: Bash, Read, Glob
---

Generate video: $ARGUMENTS

## How it works

Uses the Google Veo 3.1 API (`predictLongRunning`) to generate short video clips. Supports text-to-video and image-to-video (animate a static image). Returns an MP4 file.

**NOTE**: For image-to-video, prefer `/kling` or `/seedance` instead — they're much cheaper ($0.58-$0.70 vs $3.20) at 1080p with comparable quality. Use Veo only for text-to-video (no input image).

## Modes

### Mode A: Text-to-Video

Generate a video from a text prompt only.

### Mode B: Image-to-Video

Animate a static image. The image becomes the starting frame and Veo generates motion from it. Great for cover art, illustrations, and establishing shots.

## Default settings

- **Model**: `veo-3.1-generate-preview`
- **Duration**: 8 seconds
- **Resolution**: `720p` (1280x720)
- **Aspect ratio**: `16:9`

Override with flags in $ARGUMENTS:
- `--duration N` — 4, 6, or 8 seconds (8 required for 1080p/4k)
- `--aspect RATIO` — `16:9` (default) or `9:16`
- `--resolution RES` — `720p` (default), `1080p`, `4k`

## Steps

1. Parse $ARGUMENTS to extract the prompt, optional image path, and flags.

2. Read the API key from `.env` (variable `GOOGLE_K`).

3. If an image is provided, base64-encode it to a temp file:

```bash
base64 -i IMAGE_PATH > /tmp/veo-img-b64.txt
```

4. Build the request JSON with Python (handles large base64 data):

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-videos && \
API_KEY=$(grep GOOGLE_K .env | head -1 | cut -d= -f2) && \
python3 -c "
import json

prompt = 'PROMPT_HERE'
image_path = '/tmp/veo-img-b64.txt'  # or None for text-to-video
duration = 8
aspect = '16:9'
resolution = '720p'

instance = {'prompt': prompt}

# Image-to-video: add bytesBase64Encoded
if image_path:
    with open(image_path) as f:
        b64 = f.read().strip()
    instance['image'] = {
        'bytesBase64Encoded': b64,
        'mimeType': 'image/png'
    }

payload = {
    'instances': [instance],
    'parameters': {
        'aspectRatio': aspect,
        'resolution': resolution,
        'durationSeconds': duration
    }
}

with open('/tmp/veo-request.json', 'w') as f:
    json.dump(payload, f)
print('Request ready')
"
```

**IMPORTANT**: Use `bytesBase64Encoded` for image data, NOT `inlineData` or `fileData` — those are not supported by Veo.

5. Submit the request:

```bash
curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-preview:predictLongRunning" \
  -H "x-goog-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/veo-request.json
```

Response returns an operation name:
```json
{"name": "models/veo-3.1-generate-preview/operations/OPERATION_ID"}
```

6. Poll for completion (typically 30s–2min, up to 6min at peak):

```bash
curl -s -H "x-goog-api-key: $API_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-preview/operations/OPERATION_ID"
```

When `"done": true`, extract the video URI from:
```
.response.generateVideoResponse.generatedSamples[0].video.uri
```

7. Download the video:

```bash
curl -s -L -o generated-videos/SLUG.mp4 \
  -H "x-goog-api-key: $API_KEY" \
  "VIDEO_URI"
```

8. Verify the output:

```bash
ffprobe -v error -show_entries stream=width,height -show_entries format=duration \
  -of csv=p=0 generated-videos/SLUG.mp4
```

9. Log the API call to `api-spending.csv`:

```bash
COST=$(python3 -c "print(DURATION * 0.40)")
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),google-veo,veo-3.1-generate-preview,video,SLUG,$COST" >> api-spending.csv
```

**Pricing** (standard quality, as of March 2026):
- 720p / 1080p: **$0.40/second** — an 8s video costs **$3.20**
- 4k: **$0.60/second** — an 8s video costs **$4.80**

10. Clean up temp files:

```bash
rm -f /tmp/veo-img-b64.txt /tmp/veo-request.json
```

11. Report the file path, duration, and resolution to the user.

## API gotchas

- **`durationSeconds` must be a number**, not a string — `8` not `"8"`
- **`bytesBase64Encoded`** is the only supported image format — `inlineData` and `fileData` both fail
- **Duration 5 doesn't work** — only 4, 6, or 8 are accepted (despite docs saying 4–8 inclusive)
- **Videos are retained for 2 days** on Google's servers — download promptly
- **SynthID watermark** is applied automatically to all generated videos
- **Max latency**: ~6 minutes during peak hours, typically 30s–2min

## Prompt tips

- Be descriptive about the motion you want: "slow cinematic zoom", "mist drifting", "camera panning left"
- For image-to-video: describe what should animate in the image, not the image itself
- Keep prompts focused — Veo works best with clear, specific motion descriptions
- Include atmosphere cues: "atmospheric", "mysterious", "dramatic lighting"

## When to use Veo vs ffmpeg effects

- **Veo**: When you want actual AI-generated motion — characters moving, elements animating, atmospheric effects (mist, light, particles). More expensive, slower, but creates real animation.
- **ffmpeg (Ken Burns / scroll)**: When you just need camera motion over a static image — zoom, pan, scroll. Free, instant, predictable. Use for most video production.
- **Best practice**: Use Veo for 1-2 hero shots (opening, key moments), ffmpeg effects for everything else.
