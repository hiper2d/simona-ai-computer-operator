---
name: elevenlabs
description: Generate high-quality, natural-sounding speech using ElevenLabs TTS API. Use when the user asks for realistic voice, narration, or spoken audio — especially for final/polished output. Prefer over the Google voice skill when natural-sounding speech is important.
argument-hint: <text to speak> [--voice NAME] [--stability N] [--style N]
allowed-tools: Bash, Read
---

Generate speech from: $ARGUMENTS

## How it works

Uses the ElevenLabs text-to-speech API via curl. Outputs an MP3 file. Produces much more natural, human-sounding speech than Google TTS — better prosody, natural pauses, emotional range.

## Default voice

- **Voice**: Sarah (`EXAVITQu4vr4xnSDxMaL`) — Mature, Reassuring, Confident. American, young female.
- **Model**: `eleven_multilingual_v2` (highest quality, slower but worth it)
- **Settings**: stability=0.5, similarity_boost=0.75, style=0.5

Override with flags in $ARGUMENTS:
- `--voice NAME` — use a different voice (see table below)
- `--stability N` — 0.0 (very expressive) to 1.0 (very consistent), default 0.4
- `--style N` — 0.0 (neutral) to 1.0 (very stylized), default 0.5
- `--model MODEL_ID` — override model (default: eleven_multilingual_v2). Only use eleven_turbo_v2_5 if explicitly asked for speed over quality

## Available female voices

| Name | Voice ID | Style | Accent | Age |
|------|----------|-------|--------|-----|
| **Sarah** | EXAVITQu4vr4xnSDxMaL | Mature, Reassuring, Confident | American | Young |
| **Jessica** | cgSgspJ2msm6clMCkdW9 | Playful, Bright, Warm | American | Young |
| **Lily** | pFZP5JQG7iQjIQuC4Bku | Velvety Actress | British | Middle-aged |
| **Laura** | FGY2WhTYpPnrIDTdsKH5 | Enthusiast, Quirky Attitude | American | Young |
| **Matilda** | XrExE9yKIg1WjnnlVkGX | Knowledgeable, Professional | American | Middle-aged |
| **Alice** | Xb7hH8MSUJpSbSDYk0k2 | Clear, Engaging Educator | British | Middle-aged |
| **Bella** | hpp4J3VqNfWAUOO0d1Us | Professional, Bright, Warm | American | Middle-aged |

## Available male voices

| Name | Voice ID | Style | Accent | Age |
|------|----------|-------|--------|-----|
| **Roger** | CwhRBWXzGAHq8TQ4Fs17 | Laid-Back, Casual, Resonant | American | Middle-aged |
| **George** | JBFqnCBsd6RMkjVDRZzb | Warm, Captivating Storyteller | British | Middle-aged |
| **Charlie** | IKne3meq5aSn9XLyUdCD | Deep, Confident, Energetic | Australian | Young |
| **Eric** | cjVigY5qzO86Huf0OWal | Smooth, Trustworthy | American | Middle-aged |
| **Daniel** | onwK4e9ZLuTAKqWW03F9 | Steady Broadcaster | British | Middle-aged |
| **Brian** | nPczCjzI2devNBz1zQrb | Deep, Resonant, Comforting | American | Middle-aged |

## Neutral voice

| Name | Voice ID | Style | Accent | Age |
|------|----------|-------|--------|-----|
| **River** | SAz9YHcvj6GT2YYXdXww | Relaxed, Neutral, Informative | American | Middle-aged |

## Steps

1. Parse $ARGUMENTS to extract the text and optional flags.

2. Read the API key from `.env` (variable `EL_K`).

3. Resolve the voice ID — if `--voice NAME` is given, look up the voice ID from the tables above. Default to Sarah.

4. Generate the audio:

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-audio && \
curl -s --max-time 90 \
  "https://api.elevenlabs.io/v1/text-to-speech/VOICE_ID_HERE" \
  -H "xi-api-key: $(grep EL_K .env | head -1 | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "TEXT_HERE",
    "model_id": "eleven_turbo_v2_5",
    "voice_settings": {
      "stability": 0.4,
      "similarity_boost": 0.75,
      "style": 0.5
    }
  }' \
  --output generated-audio/SLUG.mp3 && \
echo "Audio saved to: generated-audio/SLUG.mp3"
```

Replace VOICE_ID_HERE, TEXT_HERE, and SLUG. SLUG should be a short kebab-case name (max 50 chars).

5. Verify the output is audio (not an error JSON):

```bash
SIZE=$(wc -c < generated-audio/SLUG.mp3 | tr -d ' ')
if [ "$SIZE" -lt 1000 ]; then
  echo "ERROR: $(cat generated-audio/SLUG.mp3)"
else
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 generated-audio/SLUG.mp3)
  echo "Duration: ${DUR}s, Size: $(ls -lh generated-audio/SLUG.mp3 | awk '{print $5}')"
fi
```

6. Log the API call to `api-spending.csv`:

```bash
echo "$(date +%Y-%m-%dT%H:%M:%S%z),elevenlabs,eleven_turbo_v2_5,voice,SLUG,0.30" >> api-spending.csv
```

Note: cost is approximate — ElevenLabs charges per character (~$0.30/1000 chars). A 60s narration (~4000 chars) costs ~$1.20.

7. Report the file path and duration to the user.

## Voice settings guide

- **stability** (0.0–1.0): Lower = more expressive, varied delivery. Higher = more consistent, predictable. Use 0.3–0.5 for narration, 0.5–0.7 for professional/formal content.
- **similarity_boost** (0.0–1.0): How closely to match the original voice. Keep at 0.75 for pre-made voices.
- **style** (0.0–1.0): Amplifies the voice's natural style. Higher = more character. Use 0.3–0.5 for narration, 0.0 for neutral reading.

## When to use ElevenLabs vs Google TTS

**IMPORTANT: Use Gemini/Google voice for ALL prototyping and iteration. Only use ElevenLabs for final polished cuts that Alex has approved.** ElevenLabs costs add up fast (~$0.30/clip, 13 clips = ~$3.90 wasted on a draft).

- **ElevenLabs**: Final video narration only, after Alex confirms the cut is ready. More natural, expensive (~$1/min).
- **Google/Gemini TTS**: All drafts, prototyping, testing narration timing, iterating on scripts. Nearly free.

## Troubleshooting

- **"missing_permissions"**: The API key needs `text_to_speech` and `voices_read` permissions in the ElevenLabs dashboard.
- **"concurrent_limit_exceeded"**: Free/starter plans allow max 2-4 parallel requests. Generate sequentially.
- **Small output file (<1KB)**: It's a JSON error, not audio. Check the content with `cat`.
- **For long texts**: ElevenLabs handles long text well (up to 5000 chars per request). For very long narration, split into chunks.
