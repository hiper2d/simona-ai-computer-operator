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

### Effect selection rules

Choose the effect FIRST, then generate (or request) the image in the correct format.

| Effect | Use when | Image format | Image generation hint |
|--------|----------|-------------|----------------------|
| **Zoom** | Photos, illustrations, UI screenshots, anything visual | Standard 16:9 (1920x1080 or similar) | Default — no special instructions |
| **Vertical scroll** | Code listings, terminal output, tall diagrams, long documents | **Tall portrait** — width=1080, height=1920+ | Prompt: "Generate a TALL PORTRAIT image (vertical, 9:16 aspect ratio)..." |
| **Horizontal scroll** | Timelines, wide flowcharts, panoramas, side-by-side comparisons | **Wide panoramic** — width=2560+, height=1080 | Prompt: "Generate a WIDE PANORAMIC image (ultrawide, 21:9 or wider)..." |

**Critical rules:**
- **Vertical scroll images MUST be taller than 1080px** with width exactly fitting the output (1920px or scaled to fit). No side cuts ever — the full width of the image must be visible at all times.
- **Horizontal scroll images MUST be wider than 1920px** with height exactly fitting 1080px. No top/bottom cuts.
- **Zoom images use standard 16:9.** The zoom range (1.0→1.3) is gentle enough to avoid pixelation.
- If the image generator doesn't produce the right aspect ratio, **scale the image** to fit: for vertical scroll, scale width to 1920 (height follows); for horizontal scroll, scale height to 1080 (width follows).
- Never zoom on code — it becomes unreadable. Use vertical scroll or static.
- Never horizontal-scroll on portrait content — it makes no sense.

### Ken Burns zoom (cinematic scenes)

Use `zoompan` to slowly zoom in or out.

**IMPORTANT — zoompan jitter bug:** Do NOT use `x` and `y` expressions that depend on `zoom` (e.g., `x='(iw-iw/zoom)/2'`). As zoom changes by tiny increments each frame, the x/y values oscillate between adjacent pixels, causing visible wobble/shaking. Even `trunc()` doesn't fully fix it.

**Use direct formula zoom** — calculates zoom from frame number, not accumulation. Fills entire duration, never freezes, always smooth:

```bash
FRAMES=$((DURATION_SEC * 25))

# Zoom IN (1.0x → 1.15x) over full duration
ffmpeg -y -loop 1 -i scene.png \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.0+0.15*on/${FRAMES}':d=${FRAMES}:s=1920x1080:fps=25" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4

# Zoom OUT (1.15x → 1.0x) over full duration — starts close, slowly reveals
ffmpeg -y -loop 1 -i scene.png \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.15-0.15*on/${FRAMES}':d=${FRAMES}:s=1920x1080:fps=25" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

**Shaky center-zoom** — intentionally jittery, adds intensity. Use only for short dramatic moments (2-5 seconds):

```bash
ffmpeg -y -loop 1 -i scene.png \
  -vf "zoompan=z='min(zoom+0.002,1.3)':x='trunc((iw-iw/zoom)/2)':y='trunc((ih-ih/zoom)/2)':d=${FRAMES}:s=1920x1080:fps=25" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

### Scene pacing and effect mixing

**Max scene duration: 15-20 seconds per image.** If a narration segment is longer, split it into multiple sub-scenes with different images and alternate effects.

**Alternate effects between consecutive scenes** for visual variety:
- zoom-in → zoom-out → scroll-h → zoom-in → static → zoom-out → scroll-v → ...
- Never use the same effect on 3+ consecutive scenes
- Use zoom-in for opening/establishing shots
- Use zoom-out for reveals and closing shots
- Use static (no effect) for text-heavy or quick transition shots

Tuning: `0.15` zoom range is subtle and cinematic. Going past `0.25` looks pixelated on standard images.

### Horizontal scroll (wide content)

For WIDE panoramic images (wider than 1920px). The image height must fit 1080px exactly — no top/bottom cropping.

```bash
# 1. Scale image so height = 1080, width scales proportionally (will be >1920)
ffmpeg -y -i wide_image.png -vf "scale=-1:1080" wide_scaled.png

# 2. Get scaled width
IMG_W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 wide_scaled.png)

# 3. Scroll from left to right — crop a 1920x1080 window that moves right
SCROLL_PX=$(python3 -c "print($IMG_W - 1920)")
ffmpeg -y -loop 1 -i wide_scaled.png \
  -vf "crop=1920:1080:'min(t/${DURATION_SEC}*${SCROLL_PX},${SCROLL_PX})':0" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4

# Clean up
rm wide_scaled.png
```

The full height is always visible. Only the horizontal position changes.

For right-to-left scroll, reverse the x expression: `'max(${SCROLL_PX}-t/${DURATION_SEC}*${SCROLL_PX},0)'`

### Vertical scroll (code / long content)

For TALL portrait images (taller than 1080px). The image width must fit 1920px exactly — no side cropping.

```bash
# 1. Scale image so width = 1920, height scales proportionally (will be >1080)
ffmpeg -y -i tall_image.png -vf "scale=1920:-1" tall_scaled.png

# 2. Get scaled height
IMG_H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 tall_scaled.png)

# 3. Scroll from top to bottom — crop a 1920x1080 window that moves down
SCROLL_PX=$(python3 -c "print($IMG_H - 1080)")
FRAMES=$((DURATION_SEC * 25))
ffmpeg -y -loop 1 -i tall_scaled.png \
  -vf "crop=1920:1080:0:'min(t/${DURATION_SEC}*${SCROLL_PX},${SCROLL_PX})'" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4

# Clean up
rm tall_scaled.png
```

The full width is always visible. Only the vertical position changes. Scroll speed is automatically calculated from image height and duration.

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
