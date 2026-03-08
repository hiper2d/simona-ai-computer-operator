---
name: voice
description: Generate speech audio using Google's Gemini TTS API. Use when the user asks to generate voice, narration, or spoken audio.
argument-hint: <text to speak> [--voice NAME] [--style STYLE]
allowed-tools: Bash, Read
---

Generate speech from: $ARGUMENTS

## How it works

Uses the Gemini 2.5 Flash TTS model via curl. Outputs a WAV file.

## Default voice

- **Voice**: Kore (Simona's voice — clear, composed, intelligent female)
- **Style prefix**: "Speak in a clear, calm, and slightly dry tone with subtle confidence:"

Override the voice with `--voice VoiceName` in the arguments.
Override the style with `--style "your style instructions"` in the arguments.

Available voices: Zephyr, Puck, Charon, Kore, Fenrir, Leda, Orus, Aoede, Callirrhoe, Autonoe, Enceladus, Iapetus, Umbriel, Algieba, Despina, Erinome, Algenib, Rasalgethi, Laomedeia, Achernar, Alnilam, Schedar, Gacrux, Pulcherrima, Achird, Zubenelgenubi, Vindemiatrix, Sadachbia, Sadaltager, Sulafat

## Steps

1. Parse $ARGUMENTS to extract the text, and optionally `--voice` and `--style` overrides.

2. Read the API key from `.env` (variable `GOOGLE_K`).

3. Generate the audio with curl, decode with jq + base64, convert with ffmpeg:

```bash
cd /Users/hiper2d/projects/simona-ai-computer-operator && \
mkdir -p generated-audio && \
curl -s --max-time 60 \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key=$(grep GOOGLE_K .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts":[{"text": "STYLE_PREFIX: TEXT_HERE"}]}],
    "generationConfig": {
      "responseModalities": ["AUDIO"],
      "speechConfig": {
        "voiceConfig": {
          "prebuiltVoiceConfig": {
            "voiceName": "VOICE_NAME_HERE"
          }
        }
      }
    }
  }' | jq -r '.candidates[0].content.parts[0].inlineData.data' | \
  base64 --decode > generated-audio/SLUG.pcm && \
ffmpeg -y -f s16le -ar 24000 -ac 1 -i generated-audio/SLUG.pcm generated-audio/SLUG.wav && \
rm generated-audio/SLUG.pcm && \
echo "Audio saved to: generated-audio/SLUG.wav"
```

Replace STYLE_PREFIX, TEXT_HERE, VOICE_NAME_HERE, and SLUG with appropriate values. SLUG should be a short kebab-case name derived from the text (max 50 chars).

4. Log the API call to `api-spending.csv` in the project root:

```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),gemini,gemini-2.5-flash-tts,voice,SLUG,0.02" >> api-spending.csv
```

5. Report the file path to the user.

## Troubleshooting

- If audio sounds wrong, try a different voice or adjust the style prefix.
- If you get a 400 error, the text might be too long (32k token limit) or empty.
- For long texts, split into chunks and generate multiple files.
- If curl hangs, the `--max-time 60` flag will kill it after 60 seconds.
