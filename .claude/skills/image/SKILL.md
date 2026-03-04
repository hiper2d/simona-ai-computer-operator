---
name: image
description: Generate images using Google's Nano Banana 2 (Gemini) API. Use when the user asks to create, generate, or draw an image.
argument-hint: <prompt describing the image>
allowed-tools: Bash, Read
---

Generate an image from the prompt: $ARGUMENTS

## How it works

Uses the Gemini 3.1 Flash Image model via curl. Outputs a PNG file.

## Steps

1. Parse $ARGUMENTS as the image prompt.

2. Read the API key from `.env` (variable `GOOGLE_K`).

3. Generate the image with curl, extract with jq + base64 decode:

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

Replace PROMPT_HERE and SLUG with appropriate values. SLUG should be a short kebab-case name derived from the prompt (max 50 chars).

4. Use the Read tool to show the generated image to the user.

## Output directory

Images are saved to `generated-images/` in the project root.

## Troubleshooting

- If you get a 400 error, the prompt might be too vague or violate content policy. Try rephrasing.
- If you get a 403/401 error, the API key in `.env` may be invalid or expired.
- If the output file is empty or corrupt, check the jq filter — the response field might be `inline_data` (REST) vs `inlineData` (SDK). Try both.
- If curl hangs, the `--max-time 60` flag will kill it after 60 seconds.
