---
name: image
description: Generate images using Google's Nano Banana 2 (Gemini) API. Use when the user asks to create, generate, or draw an image.
argument-hint: <prompt describing the image>
allowed-tools: Bash, Read, Glob
---

Generate an image from the prompt: $ARGUMENTS

## How it works

Uses the Gemini 3.1 Flash Image model via curl. Supports text-only prompts and image+text prompts (for style transfer, character consistency, editing, etc.).

## Reference image detection

**Before generating**, check if the user referenced an existing image (e.g. "like the cyberpunk image", "based on @generated-images/foo.png", "similar to the rooftop one"). If so:

1. Identify the reference image path (use Glob to find it in `generated-images/` if needed).
2. Use the **image+text** flow below instead of text-only.

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
    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
  }' | jq -r '.candidates[0].content.parts[] | select(.inlineData) | .inlineData.data' | \
  base64 --decode > generated-images/SLUG.png && \
echo "Image saved to: generated-images/SLUG.png"
```

3b. **Image+text** (with reference image):

Base64-encode the reference image to a temp file (too large for shell args), then build JSON with `jq --rawfile`:

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-images && \
base64 -i REFERENCE_IMAGE_PATH > /tmp/ref_img_b64.txt && \
jq -n --rawfile img /tmp/ref_img_b64.txt --arg prompt "PROMPT_HERE" '{
  "contents": [{"parts": [
    {"inlineData": {"mimeType": "image/png", "data": ($img | gsub("\\n";""))}},
    {"text": $prompt}
  ]}],
  "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
}' > /tmp/gemini_req.json && \
curl -s --max-time 90 -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key=$(grep GOOGLE_K .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d @/tmp/gemini_req.json | jq -r '.candidates[0].content.parts[] | select(.inlineData) | .inlineData.data' | \
  base64 --decode > generated-images/SLUG.png && \
echo "Image saved to: generated-images/SLUG.png"
```

Replace REFERENCE_IMAGE_PATH with the actual path, PROMPT_HERE with the prompt, and SLUG with a short kebab-case name (max 50 chars). The temp file approach avoids "argument list too long" errors with large images.

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
