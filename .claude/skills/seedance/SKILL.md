---
name: seedance
description: Generate AI videos using Seedance 2.0 (ByteDance) via fal.ai API. Supports image-to-video with native audio, end-frame interpolation, and lip-sync. Use when the user asks to generate a video with Seedance.
argument-hint: <image path> [--prompt "motion description"] [--duration 5] [--end-frame path] [--no-audio]
allowed-tools: Bash, Read, Glob
---

Generate video with Seedance: $ARGUMENTS

## How it works

Uses the fal.ai queue API to generate videos with Seedance 2.0 (ByteDance). Supports image-to-video with native audio generation and end-frame interpolation. The API is async — submit to queue, poll status, fetch result.

## Model

| Model | ID | Aspect Ratios | Duration |
|-------|----|---------------|----------|
| **2.0 i2v** | `bytedance/seedance-2.0/image-to-video` | auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 | 4-15s |
| **2.0 r2v** | `bytedance/seedance-2.0/reference-to-video` | same | 4-15s |

**IMPORTANT**: endpoints do NOT use `fal-ai/` prefix — just `bytedance/seedance-2.0/...`.

## Picking the right endpoint

- **Talking head / character speaking a known line** → **r2v** with the dialogue WAV as `audio_urls`. The model lip-syncs to your audio and largely preserves voice character + timing. Use `@Image1` and `@Audio1` references inside the prompt so the model binds them. This is the only reliable path for "make this character say *these exact words in this exact voice*."
- **Silent motion / cinematic clip** → **i2v** with `generate_audio=false`. Use when you'll dub a voiceover later (no lip sync needed) — Part 1 host-reveal pattern.
- **Native voice OK** → **i2v** with `generate_audio=true`. Cheapest path but you get Seedance's voice, not yours.

**Don't try lip-sync-swap models** (`fal-ai/sync-lipsync`, `latentsync`, etc.) to retrofit a different voice onto a Seedance i2v video — they're trained on human faces and produce mushy/glitchy mouth motion on stylized or non-human characters (wolf, robot, creature). Verified failure 2026-05-19 on werewolf-host. r2v is the right tool.

**Use LTX-2.3 fast for cheap *drafts* only.** It generates its own voice and locks lip sync to it — you can't supply a custom voice. Good for quickly testing whether motion / framing works before committing to an r2v render. See `.claude/skills/ltx-video/`.

Pricing: $0.014 per 1,000 tokens. Token formula: `(height x width x 24 x duration) / 1024`. r2v has the same per-token pricing as i2v.

| Resolution | 5s cost | 10s cost |
|------------|---------|----------|
| 480p (854x480) | ~$0.56 | ~$1.12 |
| 720p (1280x720) | ~$1.51 | ~$3.02 |

Max resolution is 720p. Default is 720p.

## Default settings

- **Duration**: 5 seconds (supports 4-15s, or "auto")
- **Audio**: enabled (native audio generation)
- **Aspect ratio**: 16:9
- **Resolution**: 720p

Override with flags in $ARGUMENTS:
- `--duration N` — 4 to 15 seconds, or "auto"
- `--resolution RES` — 480p or 720p
- `--aspect RATIO` — auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16
- `--no-audio` — disable audio generation
- `--end-frame PATH` — end frame image for interpolation
- `--prompt "text"` — motion/scene description

## Steps

1. Parse $ARGUMENTS to extract the image path, prompt, and flags.

2. Read the API key from `.env` (variable `FAL_K`).

3. Upload the image(s) to fal.ai storage:

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

If `--end-frame` is specified, upload that image too and store as `END_FILE_URL`.

4. Submit the video generation job to the queue:

```bash
RESPONSE=$(curl -s -X POST "https://queue.fal.run/bytedance/seedance-2.0/image-to-video" \
  -H "Authorization: Key ${FAL_K}" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "'"$FILE_URL"'",
    "prompt": "PROMPT_HERE",
    "duration": "5",
    "generate_audio": true,
    "resolution": "720p",
    "aspect_ratio": "16:9"
  }')

REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id')
echo "Submitted: $REQUEST_ID"
```

If end frame is provided, add `"end_image_url": "'"$END_FILE_URL"'"` to the payload.

### Reference-to-video (talking head) payload

For r2v, upload the dialogue WAV the same way as the image (`content_type: audio/wav`), then:

```bash
curl -s -X POST "https://queue.fal.run/bytedance/seedance-2.0/reference-to-video" \
  -H "Authorization: Key ${FAL_K}" \
  -H "Content-Type: application/json" \
  -d '{
    "image_urls": ["'"$IMAGE_FILE_URL"'"],
    "audio_urls": ["'"$AUDIO_FILE_URL"'"],
    "prompt": "The character from @Image1 speaks the dialogue from @Audio1 with synchronized lip movement matching every word and pause. Preserve the exact voice character and timing of @Audio1. <SCENE/MOTION DESCRIPTION HERE>.",
    "duration": "7",
    "resolution": "720p",
    "aspect_ratio": "16:9",
    "generate_audio": true
  }'
```

**Critical schema notes:**
- Use **plural array** params: `image_urls`, `audio_urls`. Singular `audio_url` is silently ignored — the model will regenerate its own voice and you'll wonder why your audio didn't lock in.
- Reference assets in the prompt via `@Image1`, `@Audio1` so the model binds them to instructions.
- Set `duration` to roughly the audio length (rounded up; min 4s, valid integer seconds). Too-long duration causes the model to extrapolate extra speech.
- The output audio is baked into the returned MP4 — extract or use as-is. r2v output sample rate is often 44.1kHz; re-encode to 48kHz to match the rest of your project pipeline.

5. Poll for completion (typically 2-3 min):

```bash
curl -s "https://queue.fal.run/bytedance/seedance-2.0/requests/${REQUEST_ID}/status" \
  -H "Authorization: Key ${FAL_K}"
```

Poll every 60 seconds. When `"status": "COMPLETED"`, proceed.

6. Fetch the result:

```bash
RESULT=$(curl -s "https://queue.fal.run/bytedance/seedance-2.0/requests/${REQUEST_ID}" \
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
# tokens = (height * width * 24 * duration) / 1024
# cost = tokens / 1000 * 0.014
COST=1.51  # adjust based on resolution/duration (see pricing table above)

echo "$(date +%Y-%m-%dT%H:%M:%S%z),fal-ai,seedance-v2.0-i2v,video,SLUG,$COST" >> api-spending.csv
```

10. Report the file path, duration, resolution, and cost to the user.

## Output directory

Videos are saved to `generated-videos/` in the project root.

## API gotchas

- **No `fal-ai/` prefix** — endpoint is `bytedance/seedance-2.0/image-to-video`, NOT `fal-ai/bytedance/...`. Using `fal-ai/` prefix silently fails (returns instant "COMPLETED" with 0.05s inference, then 404 on result fetch)
- **Auth format**: `Authorization: Key YOUR_KEY` — uses "Key" scheme, not "Bearer"
- **Queue is async**: submit returns request_id, poll status, then fetch result
- **Status/result endpoints** use `bytedance/seedance-2.0/requests/` path (same prefix as submit, without the `/image-to-video` suffix)
- **Duration is a string** — `"5"` not `5`
- **Same param names as 1.5**: `image_url`, `generate_audio`, `end_image_url` (NOT `start_frame`/`audio`/`end_frame`)
- **Max resolution is 720p** — no 1080p option
- **End frame support** — use `end_image_url` to interpolate between two images
- **Native audio** — generates speech-synced audio when `generate_audio: true`
- **Content moderation** — audio may be flagged as "sensitive content" if prompt is too vague. Always use descriptive prompts with clear speech text
- **Inference time** — ~2-3 min for 5s video at 720p

## Prompt tips

- Describe the **motion** you want, not the image content
- Include speech if relevant: "she says: Hello world"
- For talking head: describe facial expressions and tone

## Start + End frame interpolation

Use `end_image_url` when you want a **transition between two states** — e.g., dark room → lights on, door closed → door open, calm scene → action. Seedance interpolates smoothly between the frames.

**When to use:** dramatic reveals, lighting changes, environmental transformations. Not needed for simple talking head or character movement — single start frame is enough for those.

**Tips for good interpolation:**
- Keep the same camera angle and basic composition in both frames
- Change one major thing (lighting, visibility, character poses) — not everything at once
- The more similar the frames, the smoother the transition
- Generate both frames with the same prompt structure, varying only the changing element

**Content policy workaround:** Seedance blocks realistic human faces. Show characters from behind or use stylized/non-human characters (werewolves, robots). Back-of-head shots pass the filter.

## When to use Seedance vs other models

- **LTX Pro**: Cheapest, good for drafts. $0.36/6s. Synchronous API.
- **Seedance 2.0 (this skill)**: High quality with native audio and end-frame interpolation. ~$1.51/5s at 720p.
- **Kling Pro**: Best motion quality. $0.70/5s at 1080p. Good balance of cost and quality.
- **Veo**: Most expensive ($3.20/8s). Only for text-to-video (no input image).
- **ffmpeg**: Free, instant. Camera motion over static images.
