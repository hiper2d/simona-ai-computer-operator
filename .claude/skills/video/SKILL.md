---
name: video
description: Create videos from images and audio using ffmpeg. Use when the user asks to make a video, combine image with voice, or create video content.
argument-hint: <instructions for what video to create>
allowed-tools: Bash, Read, Glob
---

Create a video: $ARGUMENTS

## How it works

Uses ffmpeg to combine static images with audio tracks into MP4 videos.

## Modes

### Mode A: Image + Audio → Video (most common)

Combine a single image with an audio file. The image displays for the duration of the audio.

```bash
ffmpeg -y -loop 1 -i IMAGE_PATH -i AUDIO_PATH \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -shortest \
  -movflags +faststart \
  OUTPUT_PATH
```

### Mode B: Multiple images + Audio → Slideshow

Combine multiple images with audio, each image shown for a set duration.

1. Create a concat file listing each image with its duration:
```
file 'image1.png'
duration 5
file 'image2.png'
duration 5
file 'image3.png'
duration 5
```

2. Run ffmpeg:
```bash
ffmpeg -y -f concat -safe 0 -i concat.txt -i AUDIO_PATH \
  -c:v libx264 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -shortest \
  -movflags +faststart \
  OUTPUT_PATH
```

### Mode C: Image + Audio + Subtitles

Same as Mode A but with burned-in subtitles from an SRT file:

```bash
ffmpeg -y -loop 1 -i IMAGE_PATH -i AUDIO_PATH \
  -vf "subtitles=SUBTITLE_PATH:force_style='FontSize=24,FontName=Arial,PrimaryColour=&Hffffff&'" \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -shortest \
  -movflags +faststart \
  OUTPUT_PATH
```

## Steps

1. Identify the input files. If not specified, check `generated-images/` and `generated-audio/` for the most recent files using Glob.

2. Pick the appropriate mode based on what the user wants.

3. Run the ffmpeg command. Output goes to `generated-videos/` with a descriptive filename.

4. Report the output file path and duration to the user.

## Output directory

Videos are saved to `generated-videos/` in the project root.

## Tips

- Always use `-pix_fmt yuv420p` for maximum compatibility
- `-movflags +faststart` makes the video streamable
- `-tune stillimage` optimizes encoding for static images
- For slow Ken Burns zoom effect, replace `-loop 1` with:
  `-loop 1 -vf "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1920x1080"`
- Use `-y` to overwrite output without prompting
