---
name: openai-image
description: Generate and edit images using OpenAI's gpt-image-2 model. Use when the user asks to create or edit an image with OpenAI/GPT.
argument-hint: <prompt describing the image>
allowed-tools: Bash, Read, Glob
---

Generate or edit an image using OpenAI gpt-image-2: $ARGUMENTS

## How it works

Uses OpenAI's Image API via curl. Two endpoints:

| Endpoint | URL | Format | Use case |
|----------|-----|--------|----------|
| **Generate** | `POST /v1/images/generations` | JSON | New image from text prompt |
| **Edit** | `POST /v1/images/edits` | Multipart form | Edit/combine existing images with a prompt |

## Parameters

### Generation

| Parameter | Values | Default |
|-----------|--------|---------|
| `size` | `1024x1024`, `1024x1792`, `1792x1024` | `1024x1024` |
| `quality` | `low`, `medium`, `high`, `auto` | `auto` |
| `output_format` | `png`, `webp`, `jpeg` | `png` |
| `n` | 1-4 | 1 |

### Edit

| Parameter | Values |
|-----------|--------|
| `image[]` | One or more input image files (multipart) |
| `mask` | Optional PNG with transparent areas marking edit region |
| `size` | Same as generation |

## Prompt tips

Same as nanobanana — structure prompts in three parts:
- **Subject**: Primary object or person
- **Context/Background**: Surrounding environment
- **Style**: Artistic or photographic approach

For photorealism: mention specific camera models ("shot on Canon EOS R5"), technical specs ("8k, raw"), micro-textures ("pores visible", "fabric texture"), and explicit lighting setups.

## Reference image detection

**Before generating**, check if the user referenced an existing image (e.g. "edit the pool image", "based on @generated-images/foo.png"). If so, use the **Edit** flow.

For **character consistency** with Simona, use multiple reference images in the edit endpoint:
- `generated-images/simona-streamer-studio.png` (front-facing, primary reference)
- `generated-images/simona-younger-pointy-nose.png` (side angle)
- `generated-images/simona-night-coding.png` (3/4 angle, coding)

## Steps

1. Parse $ARGUMENTS as the image prompt.

2. Read the API key from `.env` (variable `OAI_K`).

3a. **Generate** (no reference image — text-to-image):

Pick an appropriate size: `1024x1024` for square, `1792x1024` for landscape, `1024x1792` for portrait.

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-images && \
curl -s --max-time 120 -X POST "https://api.openai.com/v1/images/generations" \
  -H "Authorization: Bearer $(grep OAI_K .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "PROMPT_HERE",
    "size": "1792x1024",
    "quality": "high",
    "n": 1
  }' | jq -r '.data[0].b64_json' | \
  base64 --decode > generated-images/SLUG.png && \
echo "Image saved to: generated-images/SLUG.png"
```

3b. **Edit** (one or more reference images):

Uses multipart form data. Each reference image is sent as `image[]=@path`.

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-images && \
curl -s --max-time 120 -X POST "https://api.openai.com/v1/images/edits" \
  -H "Authorization: Bearer $(grep OAI_K .env | cut -d= -f2)" \
  -F "model=gpt-image-2" \
  -F "image[]=@REFERENCE_IMAGE_1" \
  -F 'prompt=PROMPT_HERE' \
  -F "size=1792x1024" \
  | jq -r '.data[0].b64_json' | \
  base64 --decode > generated-images/SLUG.png && \
echo "Image saved to: generated-images/SLUG.png"
```

For multiple reference images (character consistency, combining objects):

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-images && \
curl -s --max-time 120 -X POST "https://api.openai.com/v1/images/edits" \
  -H "Authorization: Bearer $(grep OAI_K .env | cut -d= -f2)" \
  -F "model=gpt-image-2" \
  -F "image[]=@REF_IMAGE_1" \
  -F "image[]=@REF_IMAGE_2" \
  -F "image[]=@REF_IMAGE_3" \
  -F 'prompt=PROMPT_HERE' \
  -F "size=1792x1024" \
  | jq -r '.data[0].b64_json' | \
  base64 --decode > generated-images/SLUG.png && \
echo "Image saved to: generated-images/SLUG.png"
```

3c. **Edit with mask** (inpainting — edit specific region):

Create a mask PNG where transparent pixels mark the area to edit:

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-images && \
curl -s --max-time 120 -X POST "https://api.openai.com/v1/images/edits" \
  -H "Authorization: Bearer $(grep OAI_K .env | cut -d= -f2)" \
  -F "model=gpt-image-2" \
  -F "image[]=@REFERENCE_IMAGE" \
  -F "mask=@MASK_IMAGE" \
  -F 'prompt=PROMPT_HERE' \
  -F "size=1792x1024" \
  | jq -r '.data[0].b64_json' | \
  base64 --decode > generated-images/SLUG.png && \
echo "Image saved to: generated-images/SLUG.png"
```

4. Log the API call to `api-spending.csv` in the project root:

```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),openai,gpt-image-2,image,SLUG,0.08" >> api-spending.csv
```

Note: actual cost varies by quality — low ~$0.02, medium ~$0.05, high ~$0.08 for 1024x1024. Adjust the logged amount based on quality and size used.

5. Use the Read tool to show the generated image to the user.

## Output directory

Images are saved to `generated-images/` in the project root.

## Troubleshooting

- If you get `null` from jq, the response likely has an error. Pipe to `jq .` first to see the full response.
- If you get a 401 error, the API key in `.env` (`OAI_K`) may be invalid.
- If you get a 429 error, you've hit rate limits — wait and retry.
- If you get a 400 error about content policy, rephrase the prompt.
- For edits, images must be PNG or WEBP. If the reference is JPEG, convert first: `sips -s format png input.jpg --out input.png`
- If images are too large (>25MB), resize first: `sips --resampleWidth 2048 input.png --out input_resized.png`
- The `--max-time 120` flag kills curl after 2 minutes if the API hangs.
