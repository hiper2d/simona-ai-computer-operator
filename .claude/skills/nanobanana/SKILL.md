---
name: nanobanana
description: Generate images using Google's Nano Banana 2 (Gemini) API. Use when the user asks to create, generate, or draw an image.
argument-hint: <prompt describing the image>
allowed-tools: Bash, Read, Glob
---

Generate an image from the prompt: $ARGUMENTS

## How it works

Uses the Gemini 3.1 Flash Image model via curl. Supports text-only prompts, image+text prompts (for style transfer, editing), and multi-reference prompts (for character consistency).

**API guide**: https://ai.google.dev/gemini-api/docs/image-generation

## Modes

| Mode | Use case | Max references |
|------|----------|----------------|
| **Text-only** | New image from scratch | 0 |
| **Image+text** | Edit an image, style transfer | 1 |
| **Multi-reference** | Character consistency across scenes | Up to 10 object + 4 character images |

## imageConfig options

Always include `imageConfig` in `generationConfig` for better results:

- **aspectRatio**: `"1:1"`, `"3:4"`, `"4:3"`, `"9:16"`, `"16:9"`, `"21:9"`, etc.
- **imageSize**: `"512"`, `"1K"`, `"2K"`, `"4K"` — default to `"2K"` for quality

## Reference image detection

**Before generating**, check if the user referenced an existing image or wants character consistency (e.g. "like the cyberpunk image", "same person as", "based on @generated-images/foo.png"). If so:

1. Identify the reference image path(s) (use Glob to find in `generated-images/` if needed).
2. For **character consistency**: use **multiple references** (2-3 images of the same character from different angles). This produces much better face/identity consistency than a single reference.
3. Use the appropriate flow below.

## Prompt tips

Structure prompts in three parts:
- **Subject**: The primary object or person
- **Context/Background**: Surrounding environment
- **Style**: Artistic or photographic approach

Photography modifiers that work well:
- Camera proximity: close-up, medium shot, wide shot, over-the-shoulder
- Angles: low angle, high angle, eye level, bird's eye
- Lighting: natural, dramatic, warm, cold, moody, neon
- Lens: macro, fisheye, wide-angle, bokeh

For character consistency, specify in prompt: "This is the same woman/man shown in these reference photos. Same face, same glasses, same hair, same clothing."

## Steps

1. Parse $ARGUMENTS as the image prompt.

2. Read the API key from `.env` (variable `GOOGLE_K`).

3a. **Text-only** (no reference image):

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-images && \
curl -s --max-time 60 -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key=$(grep GOOGLE_K .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "PROMPT_HERE"}]}],
    "generationConfig": {
      "responseModalities": ["TEXT", "IMAGE"],
      "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"}
    }
  }' | jq -r '.candidates[0].content.parts[] | select(.inlineData) | .inlineData.data' | \
  base64 --decode > generated-images/SLUG.png && \
echo "Image saved to: generated-images/SLUG.png"
```

3b. **Single reference** (editing, style transfer):

Base64-encode the reference image to a temp file, then build JSON with `jq --rawfile`:

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-images && \
base64 -i REFERENCE_IMAGE_PATH > /tmp/ref_img_b64.txt && \
jq -n --rawfile img /tmp/ref_img_b64.txt --arg prompt "PROMPT_HERE" '{
  "contents": [{"parts": [
    {"text": $prompt},
    {"inline_data": {"mime_type": "image/png", "data": ($img | gsub("\\n";""))}}
  ]}],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"],
    "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"}
  }
}' > /tmp/gemini_req.json && \
curl -s --max-time 90 -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key=$(grep GOOGLE_K .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d @/tmp/gemini_req.json | jq -r '.candidates[0].content.parts[] | select(.inlineData) | .inlineData.data' | \
  base64 --decode > generated-images/SLUG.png && \
echo "Image saved to: generated-images/SLUG.png"
```

3c. **Multi-reference** (character consistency — PREFERRED for Simona images):

Use 2-3 reference images of the same character from different angles. This gives the model multiple views to maintain identity.

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-images && \
base64 -i REF_IMAGE_1 > /tmp/ref1_b64.txt && \
base64 -i REF_IMAGE_2 > /tmp/ref2_b64.txt && \
base64 -i REF_IMAGE_3 > /tmp/ref3_b64.txt && \
jq -n \
  --rawfile img1 /tmp/ref1_b64.txt \
  --rawfile img2 /tmp/ref2_b64.txt \
  --rawfile img3 /tmp/ref3_b64.txt \
  --arg prompt "PROMPT_HERE" \
'{
  "contents": [{"parts": [
    {"text": $prompt},
    {"inline_data": {"mime_type": "image/png", "data": ($img1 | gsub("\\n";""))}},
    {"inline_data": {"mime_type": "image/png", "data": ($img2 | gsub("\\n";""))}},
    {"inline_data": {"mime_type": "image/png", "data": ($img3 | gsub("\\n";""))}}
  ]}],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"],
    "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"}
  }
}' > /tmp/gemini_multi_req.json && \
curl -s --max-time 120 -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key=$(grep GOOGLE_K .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d @/tmp/gemini_multi_req.json | jq -r '.candidates[0].content.parts[] | select(.inlineData) | .inlineData.data' | \
  base64 --decode > generated-images/SLUG.png && \
echo "Image saved to: generated-images/SLUG.png"
```

**Best reference images for Simona** (use these 3 for character consistency):
- `generated-images/simona-streamer-studio.png` (front-facing, primary reference)
- `generated-images/simona-younger-pointy-nose.png` (side angle)
- `generated-images/simona-night-coding.png` (3/4 angle, coding)

Replace REF_IMAGE_1/2/3, PROMPT_HERE, and SLUG appropriately.

4. Log the API call to `api-spending.csv` in the project root:

```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),gemini,gemini-3.1-flash-image,image,SLUG,0.067" >> api-spending.csv
```

5. Use the Read tool to show the generated image to the user.

## Output directory

Images are saved to `generated-images/` in the project root.

## Troubleshooting

- If you get a 400 error, the prompt might be too vague or violate content policy. Try rephrasing.
- If you get a 403/401 error, the API key in `.env` may be invalid or expired.
- If the output file is empty or corrupt, check the jq filter — the response field might be `inline_data` (REST) vs `inlineData` (SDK). Try both.
- If curl hangs, the `--max-time` flag will kill it after the timeout.
- For image+text, if the reference image is too large (>4MB), resize it first with `sips --resampleWidth 1024`.
- Maximum prompt length: 480 tokens.
