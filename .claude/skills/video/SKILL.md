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

## Motion effects for slideshows

When building a slideshow (Mode B), render each scene as a separate clip with motion effects, then concatenate + add audio. This gives per-clip control over effects.

### When to use motion effects

- **Cinematic / visual scenes** (landscapes, art, photos, diagrams) → Ken Burns zoom or pan. Makes static images feel alive.
- **Code / text-heavy images** → **No zoom**, or use **vertical scroll** if the image is taller than 1080px. Zooming on code makes it unreadable.
- **Mix of both** → Alternate effects per scene. Variety keeps the video engaging.

### Ken Burns zoom (cinematic scenes)

Use `zoompan` to slowly zoom in or out. Alternate direction between scenes for variety.

```bash
# Slow zoom IN (1.0x → 1.3x) — good for opening/establishing shots
FRAMES=$((DURATION_SEC * 25))
ffmpeg -y -loop 1 -i scene.png \
  -vf "zoompan=z='min(zoom+0.001,1.3)':d=${FRAMES}:s=1920x1080:fps=25" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4

# Slow zoom OUT (1.3x → 1.0x) — good for reveals, pulling back
ffmpeg -y -loop 1 -i scene.png \
  -vf "zoompan=z='if(eq(on,1),1.3,max(zoom-0.001,1.0))':d=${FRAMES}:s=1920x1080:fps=25" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

Tuning: `0.001` per frame is subtle and cinematic. Use `0.002` for faster zoom. Max zoom `1.3` keeps the image sharp; going past `1.5` looks pixelated.

### Pan (drift across image)

Use `zoompan` with `x` and `y` expressions to drift across a wide or tall image.

```bash
# Slow pan LEFT to RIGHT across a wide image (e.g. panorama, wide diagram)
ffmpeg -y -loop 1 -i wide_scene.png \
  -vf "zoompan=z=1.2:d=${FRAMES}:x='min(on*2,iw-iw/zoom)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=25" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4

# Slow pan RIGHT to LEFT
ffmpeg -y -loop 1 -i wide_scene.png \
  -vf "zoompan=z=1.2:d=${FRAMES}:x='max(iw-iw/zoom-on*2,0)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=25" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

### Vertical scroll (code / long content)

For images taller than 1080px (e.g. code screenshots, long documents), scroll top-to-bottom.

```bash
# Get image height first
IMG_H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 tall_image.png)

# Scroll from top to bottom over DURATION_SEC seconds
SCROLL_SPEED=$(echo "scale=6; ($IMG_H - 1080) / ($DURATION_SEC * 25)" | bc)
ffmpeg -y -loop 1 -i tall_image.png \
  -vf "crop=1920:1080:0:'min(t*${SCROLL_SPEED}*25,${IMG_H}-1080)'" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

For code, a steady scroll at readable speed works best. If the image is very tall, increase duration or split into multiple clips rather than scrolling too fast.

### Combining zoom + pan

```bash
# Zoom in while drifting right — dramatic establishing shot
ffmpeg -y -loop 1 -i scene.png \
  -vf "zoompan=z='min(zoom+0.001,1.3)':d=${FRAMES}:x='min(on*1.5,iw-iw/zoom)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=25" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

### Concatenating clips with audio

After rendering individual clips with effects:

```bash
# Create concat list
for i in 1 2 3 4 5; do echo "file 'clip${i}.mp4'" >> concat.txt; done

# Merge clips + add audio
ffmpeg -y -f concat -safe 0 -i concat.txt -i narration.wav \
  -c:v libx264 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -shortest -movflags +faststart \
  output.mp4

# Clean up temp clips
rm clip*.mp4 concat.txt
```

### No effect (static)

For code walkthroughs or text-heavy content where motion would distract:

```bash
ffmpeg -y -loop 1 -i code.png \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

## Tips

- Always use `-pix_fmt yuv420p` for maximum compatibility
- `-movflags +faststart` makes the video streamable
- `-tune stillimage` optimizes encoding for static images (use only for truly static clips, not zoompan)
- Use `-y` to overwrite output without prompting
- Use 25 fps for smooth zoompan; 30 also works but match it consistently
- Calculate `FRAMES = DURATION_SEC * FPS` for zoompan `d` parameter
