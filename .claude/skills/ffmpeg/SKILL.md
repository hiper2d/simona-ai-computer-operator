---
name: ffmpeg
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

### Mode B: Slideshow (two types)

Two slideshow variants based on how voice aligns with visuals:

#### B1: Unsynced slideshow (one voice over all slides)

One continuous narration plays over all slides. Slides transition via crossfade independently of the voice. Use when the narration is a single thought that flows over atmospheric imagery.

**Steps:**
1. Build each slide as a Ken Burns zoom clip (~2.5-3.2s each):
```bash
FRAMES=$((SLIDE_DUR_MS * 25 / 1000))
ffmpeg -y -loop 1 -i slide.png \
  -vf "scale=7680:4320:force_original_aspect_ratio=decrease,pad=7680:4320:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.0+0.12*on/${FRAMES}':x='iw/2-(iw/(1.0+0.12*on/${FRAMES})/2)':y='ih/2-(ih/(1.0+0.12*on/${FRAMES})/2)':d=${FRAMES}:s=7680x4320:fps=25,scale=1920:1080" \
  -c:v libx264 -pix_fmt yuv420p -t SLIDE_DUR -an -r 25 slide_clip.mp4
```

2. Chain crossfade transitions (0.3s each). Must chain step by step — ffmpeg xfade on 5+ inputs in one filter_complex is unreliable. Use **dynamic offsets** — read the previous clip's duration instead of hardcoding:
```bash
# First pair
ffmpeg -y -i slide1.mp4 -i slide2.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.3:offset=2.7[v]" \
  -map "[v]" -c:v libx264 -pix_fmt yuv420p -r 25 -an x2.mp4

# Then loop: offset = prev_duration - 0.3
for i in 3 4 5 6 7 8; do
  prev_dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 x$((i-1)).mp4)
  offset=$(python3 -c "print(round(${prev_dur} - 0.3, 1))")
  ffmpeg -y -i x$((i-1)).mp4 -i slide${i}.mp4 \
    -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.3:offset=${offset}[v]" \
    -map "[v]" -c:v libx264 -pix_fmt yuv420p -r 25 -an x${i}.mp4
done
cp x8.mp4 slideshow-visual.mp4
```

3. Overlay the single narration audio:
```bash
ffmpeg -y -i slideshow_visual.mp4 -i narration.wav \
  -filter_complex "[1:a]adelay=300|300,apad=whole_dur=TOTAL[a]" \
  -map "0:v" -map "[a]" -t TOTAL \
  -c:v libx264 -pix_fmt yuv420p -ar 48000 -ac 2 -c:a aac -b:a 192k \
  slideshow_final.mp4
```

**Planning**: total_slides = ceil(narration_duration / slide_duration). Target ~2.5-3.2s per slide.

#### B2: Synced slideshow (per-slide voice chunks)

Each slide has its own dedicated voice chunk. Use when each slide explains something specific (e.g., role cards, feature screenshots). Generate separate audio per slide, build each slide to match its audio duration, then concatenate.

```bash
# Build each slide to match its audio
for i in 1 2 3; do
  AUD_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 narration_${i}.wav)
  TOTAL=$(python3 -c "print(${AUD_DUR} + 0.5)")
  # Build zoom clip
  ffmpeg -y -loop 1 -i slide${i}.png ... -t ${TOTAL} -an slide${i}_clip.mp4
  # Combine with audio
  ffmpeg -y -i slide${i}_clip.mp4 -i narration_${i}.wav \
    -filter_complex "[1:a]adelay=500|500,apad=whole_dur=${TOTAL}[a]" \
    -map "0:v" -map "[a]" -t ${TOTAL} ... slide${i}_final.mp4
done
# Concatenate all
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy slideshow.mp4
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

Choose the effect based on the **content type**, not just the image format. The effect should match what the viewer needs to see.

| Effect | Use when | Image format | How to get the image |
|--------|----------|-------------|----------------------|
| **Zoom in/out** | Panoramic/cinematic images, backgrounds (space, nature, illustrations), cover art, generated artwork | Standard 16:9 (1920x1080 or similar) | Image generation or standard screenshots |
| **Vertical scroll (down)** | Website/app UI, chat messages, code listings, articles, any vertically-scrolling content | **Tall portrait** — width=1920, height=2000+ | Full-page browser screenshots (stitch multiple screenshots by scrolling), or tall generated images |
| **Horizontal scroll (right)** | Timelines, wide diagrams, tables, side-by-side comparisons, panoramic photos | **Wide panoramic** — width=2560+, height=1080 | Wide generated images or stitched horizontal screenshots |
| **Static** | Text-heavy content, quick transitions, simple UI states | Standard 16:9 | Any screenshot |

**Content-to-effect mapping (common cases):**
- Cover art, generated illustrations → **zoom in** (opening) or **zoom out** (reveal/closing)
- App UI showing a chat/feed/list → **scroll down** (reveals content naturally, like the user is reading)
- App UI showing a form or modal → **static** or **gentle zoom**
- Code or terminal output → **scroll down** (never zoom — text becomes unreadable)
- Nature/space/cinematic backgrounds → **zoom in/out**
- Flowcharts, architecture diagrams → **horizontal scroll** (if wide) or **static**

**Getting tall screenshots for scroll-down:**
When showing app/website UI with scroll-down effect, you need screenshots taller than 1080px. To capture these:
1. Use the browser skill to navigate to the page
2. Take a screenshot at the top
3. Scroll down and take another screenshot
4. Stitch them vertically using ffmpeg/ImageMagick: `convert top.png bottom.png -append tall.png`
5. Or use CDP's `Page.captureScreenshot` with `captureBeyondViewport: true` and `max_size=20*1024*1024` on the websocket for full-page capture (default websocket limit is too small for tall pages)

**Sectioned scroll for long pages (recommended for pages > 3000px tall):**

When a full-page screenshot is very tall (e.g., a chat feed, long article, game log), do NOT scroll the entire page in one continuous clip — it will be too fast and unreadable. Instead:

1. **Capture the full page** as one tall screenshot
2. **Scale to 1920px width**: `ffmpeg -y -i fullpage.png -vf "scale=1920:-1" fullpage-scaled.png`
3. **Identify content sections** by extracting horizontal strips at regular intervals (every ~1000px) and viewing them to find where sections change (e.g., introductions → discussion → voting)
4. **Crop each section** into separate tall images:
   ```bash
   ffmpeg -y -i fullpage-scaled.png -vf "crop=1920:SECTION_HEIGHT:0:Y_START" section.png
   ```
   Each section should be 1500-3000px tall (enough for slow scroll but not overwhelming)
5. **Build a scroll clip for each section** — each scrolls slowly through just its portion:
   ```bash
   SCROLL_PX=$((SECTION_HEIGHT - 1080))
   ffmpeg -y -loop 1 -i section.png \
     -vf "crop=1920:1080:0:'min(t/${DURATION_SEC}*${SCROLL_PX},${SCROLL_PX})'" \
     -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
   ```
6. **Match sections to narration** — each clip shows what the narrator is talking about (e.g., narrator describes voting → show the voting section)

**Target scroll speed**: ~80-120 px/s for readable text. For a 1500px section with 1080 visible, that's ~420px of scroll = ~4-5 seconds. For longer sections (2500px), ~1420px scroll over ~12-15s.

**Freeze-then-scroll**: For UI that benefits from first showing the full context before scrolling (e.g., a form page), hold the top frame static for 2-3 seconds before starting the scroll:
```bash
# Hold top for 3s, then scroll for remaining duration
HOLD_SEC=3
SCROLL_SEC=$((DURATION_SEC - HOLD_SEC))
ffmpeg -y -loop 1 -i section.png \
  -vf "crop=1920:1080:0:'if(lt(t,${HOLD_SEC}),0,min((t-${HOLD_SEC})/${SCROLL_SEC}*${SCROLL_PX},${SCROLL_PX}))'" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

**Critical rules:**
- **Vertical scroll images MUST be taller than 1080px** with width exactly fitting the output (1920px or scaled to fit). No side cuts ever — the full width of the image must be visible at all times.
- **Horizontal scroll images MUST be wider than 1920px** with height exactly fitting 1080px. No top/bottom cuts.
- **Zoom images use standard 16:9.** The zoom range (1.0→1.3) is gentle enough to avoid pixelation.
- If the image generator doesn't produce the right aspect ratio, **scale the image** to fit: for vertical scroll, scale width to 1920 (height follows); for horizontal scroll, scale height to 1080 (width follows).
- Never zoom on code — it becomes unreadable. Use vertical scroll or static.
- Never horizontal-scroll on portrait content — it makes no sense.
- **Never scroll the entire page in one clip if it's > 3000px tall** — split into sections first.

### Ken Burns zoom (cinematic scenes)

Use `zoompan` to slowly zoom in or out.

**IMPORTANT — zoompan jitter bug:** When using `x` and `y` expressions for centered zoom, the values oscillate between adjacent pixels, causing visible wobble. Even `trunc()` doesn't fix it at 1080p.

**Fix: run zoompan at 4K internally (3840x2160), downscale to 1080p.** The 1-pixel jitter at 4K becomes a sub-pixel shift after downscaling — invisible. Do NOT use 8K (7680x4320) — it causes frame count bugs with some images.

**Centered zoom IN** (1.0x → 1.15x) — smooth, no jitter:

```bash
FRAMES=$((DURATION_SEC * 25))

ffmpeg -y -loop 1 -i scene.png \
  -vf "scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.0+0.15*on/${FRAMES}':x='iw/2-(iw/(1.0+0.15*on/${FRAMES})/2)':y='ih/2-(ih/(1.0+0.15*on/${FRAMES})/2)':d=${FRAMES}:s=3840x2160:fps=25,scale=1920:1080" \
  -frames:v ${FRAMES}" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

**Centered zoom OUT** (1.15x → 1.0x) — starts close, slowly reveals:

```bash
ffmpeg -y -loop 1 -i scene.png \
  -vf "scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.15-0.15*on/${FRAMES}':x='iw/2-(iw/(1.15-0.15*on/${FRAMES})/2)':y='ih/2-(ih/(1.15-0.15*on/${FRAMES})/2)':d=${FRAMES}:s=3840x2160:fps=25,scale=1920:1080" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

**Top-left zoom IN** (no x/y needed, no jitter) — simpler, use when center doesn't matter:

```bash
ffmpeg -y -loop 1 -i scene.png \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.0+0.15*on/${FRAMES}':d=${FRAMES}:s=1920x1080:fps=25" \
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

**CRITICAL — zoompan loop bug:** When using `-loop 1` with zoompan, if zoompan's `d` frames run out before `-t` duration, the loop restarts the image AND resets zoompan — causing a visible "snap back to original size" mid-clip. **Fix:** always set `d=200` (8 seconds worth — way beyond any slide duration) so zoompan **never finishes its cycle**. Use `-t DURATION` to cut the clip. The zoom expression still references the real frame count for correct zoom speed (e.g., `on/75` for 3s). Never set `d` equal to or near the actual frame count.

**CRITICAL — zoompan prescale + resolution:** Pre-scale images to the zoompan internal resolution as a separate step. Use **4K (3840x2160)** not 8K — 8K causes frame count miscalculations on some images, leading to the loop bug even with oversized `d`. 4K is sufficient to eliminate jitter. Always add `-frames:v N` as a hard cap to guarantee no looping:
```bash
# Step 1: prescale to 4K
ffmpeg -y -i input.png -vf "scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2" prescaled.png
# Step 2: zoompan at 4K with hard frame cap
FRAME_COUNT=75  # 3.0s at 25fps — controls zoom speed
ffmpeg -y -loop 1 -i prescaled.png \
  -vf "zoompan=z='1.0+0.12*on/${FRAME_COUNT}':x='iw/2-(iw/(1.0+0.12*on/${FRAME_COUNT})/2)':y='ih/2-(ih/(1.0+0.12*on/${FRAME_COUNT})/2)':d=200:s=3840x2160:fps=25,scale=1920:1080" \
  -c:v libx264 -pix_fmt yuv420p -t 3.0 -an -r 25 clip.mp4
# d=200 prevents loop reset, -t 3.0 cuts the clip, on/75 controls zoom speed
```

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

### Multi-chunk assembly pitfalls (learned the hard way 2026-05-23)

When chaining many xfades to assemble a multi-part video, two silent failures cost real iteration time. Both are easy to catch up front:

**Pitfall 1: format duration ≠ video stream duration in source chunks**

If any input chunk has `format=duration` longer than `stream=duration` (video), the xfade chain will silently truncate downstream. Common cause: using `-t N` on an output where the actual scene frames sum to less than N — the muxer pads format duration without adding frames.

```bash
# Always verify BEFORE chaining xfades. If video < audio, downstream xfade breaks.
for f in chunk*.mp4; do
  FMT=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  VID=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$f")
  AUD=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$f")
  printf "%-40s fmt=%s vid=%s aud=%s\n" "$f" "$FMT" "$VID" "$AUD"
done
```

**Fix for small mismatches (<0.5s)**: add `tpad` in the assembly filter to clone the last video frame across the gap. No re-encoding the source chunk needed:

```
[N:v]tpad=stop_mode=clone:stop_duration=0.2[vN]
```

**Fix for large mismatches**: rebuild the source chunk. Don't use `-t` to pad — use scene durations that actually sum to the audio length.

**Pitfall 2: timebase mismatch after `concat` filter**

`concat` produces output with timebase `1/1000000`. Subsequent `xfade` expects matching timebases — typically `1/12800` for project clips. You get `First input link main timebase (1/1000000) do not match the corresponding second input link xfade timebase (1/12800)` and the encoder never opens.

**Fix**: append `fps=25,settb=1/12800` after any concat that feeds into xfade:

```
[v0][v1]concat=n=2:v=1:a=0,fps=25,settb=1/12800[v01]
[v01][2:v]xfade=transition=fade:duration=0.4:offset=...[v012]
```

### Scene-change transition (cinematic → instructional or vice versa)

For mode-changing transitions (e.g. host scene → chalkboard slideshow), `xfade=fadeblack` doesn't give a real black hold — it's all curve, the midpoint is one frame. For an actual "lights out, lights on" beat with definite black, build it manually:

```
# Stream 0 fades to black, then holds black, then stream 1 fades in from black
[0:v]fade=t=out:st=END_MINUS_FADEDUR:d=0.3[v0a]
[v0a]tpad=stop_mode=add:stop_duration=0.4:color=black[v0]   # 0.4s pure black hold
[1:v]tpad=start_mode=clone:start_duration=0.3[v1a]           # held first frame...
[v1a]fade=t=in:st=0:d=0.3[v1]                                # ...that fades in from black
[v0][v1]concat=n=2:v=1:a=0,fps=25,settb=1/12800[v01]

# Audio: pad stream 0 with silence to match the visual extension, delay stream 1
# so its first words don't start until after the chalk is fully visible
[0:a]apad=pad_dur=0.4,atrim=duration=NEW_END[a0]
[1:a]adelay=300|300[a1]
[a0][a1]concat=n=2:v=0:a=1[a01]
```

**Critical:** do NOT use `acrossfade` at this boundary. acrossfade overlaps both audio streams during the crossfade window, so the second stream's narration starts at the BEGINNING of the visual transition — words audible while the previous scene fades to black. Use `concat` with silence padding instead, so audio is genuinely silent during the black hold.

Tune the four numbers (fade-out, black hold, fade-in, audio delay) together. Typical range: 0.3/0.4/0.3/0.3 (quick), 0.4/0.7/0.4/0.4 (deliberate scene break).

### No effect (static)

For code walkthroughs or text-heavy content where motion would distract:

```bash
ffmpeg -y -loop 1 -i code.png \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p -t ${DURATION_SEC} -an clip.mp4
```

### App walkthrough effects

Three effects for showing web app UI in video walkthroughs. All require the **browser skill** for screenshots and the browser viewport set to 1920x1080:

```bash
uv run python mcp/browser/cli.py viewport 1920x1080 --scale 1
```

Screenshots come out at 3840x2160 (2x retina). Always downscale:
```bash
ffmpeg -y -i raw.png -vf "scale=1920:1080:flags=lanczos" screenshot.png
```

Use JS `getBoundingClientRect()` for element coordinates — CSS pixels map 1:1 to image pixels after downscale.

#### Cursor move + click on button

Shows a cursor smoothly moving to a button and clicking it. Use `mcp/cursor/animate.py`.

**Key parameters:**
- `--start X,Y` — cursor start position (keep close to target, ~200-300px away)
- `--target X,Y` — button center (from `getBoundingClientRect()`: `cx = x + w/2, cy = y + h/2`)
- `--button X,Y,W,H` — button rect for highlight effect on click (from `getBoundingClientRect()`)
- `--total-duration N` — total clip length; cursor moves late so **click happens at the end**, right before the transition to the next segment (creates "click → next page" illusion)

```bash
python3 mcp/cursor/animate.py \
  --image screenshot.png \
  --start 750,550 --target 861,780 \
  --button 740,748,242,64 \
  --total-duration 7.5 \
  --output cursor-click.mp4
```

**Getting button coordinates:**
```bash
uv run python mcp/browser/cli.py js "
var btn = document.querySelector('a.my-button');
var r = btn.getBoundingClientRect();
JSON.stringify({cx: Math.round(r.x+r.width/2), cy: Math.round(r.y+r.height/2), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)});
"
```

#### Dropdown scroll (showing list contents)

Captures multiple screenshots of a dropdown at different scroll positions, then builds a slideshow.

**Steps:**
1. Open the dropdown (click the trigger button)
2. Screenshot → downscale to 1920x1080 → save as `dropdown-1.png`
3. Scroll the dropdown container via JS: `el.scrollTop += 200`
4. Screenshot → save as `dropdown-2.png`
5. Repeat until all content is shown
6. Build a slideshow with `~1.7s` per frame:

```bash
cat > concat.txt << 'EOF'
file 'dropdown-1.png'
duration 1.7
file 'dropdown-2.png'
duration 1.7
file 'dropdown-3.png'
duration 1.7
file 'dropdown-3.png'
EOF

ffmpeg -y -f concat -safe 0 -i concat.txt \
  -vf "fps=25" -c:v libx264 -pix_fmt yuv420p -an -r 25 dropdown.mp4
```

**Scrolling a dropdown container via JS:**
```bash
uv run python mcp/browser/cli.py js "
var el = document.querySelector('.dropdown-menu');
// Or find scrollable parent of checkboxes:
// var el = document.querySelector('input[type=checkbox]').parentElement;
// while (el && el.scrollHeight <= el.clientHeight) el = el.parentElement;
el.scrollTop += 200;
JSON.stringify({scrollTop: el.scrollTop, scrollHeight: el.scrollHeight});
"
```

#### Scroll-to-element + highlight

Scrolls a full-page screenshot to center a specific element, pauses, and draws a highlight border around it. For explaining specific UI sections.

**Steps:**

1. **Capture full page** (needs CDP command, not regular screenshot):
```bash
uv run python mcp/browser/cli.py cdp "Page.captureScreenshot" \
  '{"format":"png","captureBeyondViewport":true,"clip":{"x":0,"y":0,"width":1920,"height":PAGE_HEIGHT,"scale":1}}'
# Decode base64, save, then scale to 1920 width:
ffmpeg -y -i raw.png -vf "scale=1920:-1" fullpage.png
```

2. **Get element's page position** via JS (use `scrollY + getBoundingClientRect().y`):
```bash
uv run python mcp/browser/cli.py js "
var el = document.querySelector('.player-card');
var r = el.getBoundingClientRect();
JSON.stringify({
  pageY: Math.round(r.y + window.scrollY),
  x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height)
});
"
```

3. **Calculate scroll target** to center the element:
```
scroll_target = element_pageY + element_height/2 - 540  (viewport center = 540)
```

4. **Build the clip** with scroll + highlight:
```bash
# Element in viewport after scroll: viewport_y = pageY - scroll_target
ffmpeg -y -loop 1 -i fullpage.png \
  -vf "crop=1920:1080:0:'if(lt(t,HOLD),START_Y,if(lt(t,HOLD+SCROLL_DUR),START_Y+min((t-HOLD)/SCROLL_DUR*SCROLL_PX,SCROLL_PX),END_Y))',\
fps=25,\
drawbox=x=EL_X:y=EL_VIEWPORT_Y:w=EL_W:h=EL_H:color=cyan@0.5:t=4:enable='gte(t,HIGHLIGHT_START)'" \
  -c:v libx264 -pix_fmt yuv420p -t TOTAL -an -r 25 clip.mp4
```

**Continuous scroll across segments:** When multiple segments scroll the same page, each segment should start where the previous one ended:
- Seg A: scroll from y=200 to y=700
- Seg B: scroll from y=700 to y=712, then highlight
- Seg C: scroll from y=712 to y=4336, then highlight

**Highlight rules:**
- Use `drawbox` with `color=cyan@0.5:t=4` (thick border, visible on dark UIs)
- Get element dimensions from JS `getBoundingClientRect()` — use the actual DOM element's container div, not individual form fields
- For player cards / form sections: find the wrapper div by walking up from a known child element until you find one with `height > 200` and multiple child inputs

### Animated highlights (self-drawing borders on web pages)

For explaining UI — annotate real DOM elements with pixel-perfect self-drawing SVG borders and a cursor dot. Uses the **highlight skill** (`mcp/highlight/cli.py`).

```bash
uv run python mcp/highlight/cli.py capture \
  --url "http://localhost:3000/page" \
  --config highlights.json \
  --output /tmp/frames/ \
  --encode clip.mp4
```

Config-driven: define a sequence of `highlight`, `scroll`, `click`, `wait`, and `static` actions in a JSON file. See the **highlight skill** for full docs, config format, and action reference.

Output clips are at viewport size (e.g., 1400x900) — use `--scale 1920:1080` to match other video clips. Can be concatenated with zoom/scroll clips.

## Cleanup

**Always clean up temp files after the final video is assembled.** Video production generates a lot of intermediate files:

- `/tmp/clip*.mp4` — individual clip files
- `/tmp/section-*.png` — cropped screenshot sections
- `/tmp/*-scaled.png` — scaled images
- `/tmp/*-fullpage.png` — full-page screenshots
- `/tmp/concat.txt` — ffmpeg concat lists
- `/tmp/*-frames/` — highlight capture frame directories (can be 100-300MB each)
- `/tmp/*.json` — highlight config files

Run cleanup after the final video is saved to `generated-videos/`:

```bash
# Remove all temp clips, sections, scaled images, concat files
rm -f /tmp/clip*.mp4 /tmp/section-*.png /tmp/*-scaled.png /tmp/*-fullpage.png /tmp/concat.txt
# Remove highlight frame dirs (the highlight tool auto-cleans when --encode is used, but manual runs may leave them)
rm -rf /tmp/*-frames/
# Remove any temp config files
rm -f /tmp/*-highlights*.json
```

The highlight tool (`mcp/highlight/cli.py`) auto-cleans frame PNGs after encoding by default. Pass `--keep-frames` to keep them for debugging.

## Tips

- Always use `-pix_fmt yuv420p` for maximum compatibility
- `-movflags +faststart` makes the video streamable
- `-tune stillimage` optimizes encoding for static images (use only for truly static clips, not zoompan)
- Use `-y` to overwrite output without prompting
- Use 25 fps for smooth zoompan; 30 also works but match it consistently
- Calculate `FRAMES = DURATION_SEC * FPS` for zoompan `d` parameter
