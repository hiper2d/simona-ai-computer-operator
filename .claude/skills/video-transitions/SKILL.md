---
name: video-transitions
description: Techniques for combining AI-generated video clips with static images — freeze, lead-in, lead-out, and zoom effects. Reference guide for video production.
argument-hint: <transition technique to apply>
allowed-tools: Bash, Read, Glob
---

Apply a video transition technique: $ARGUMENTS

## Overview

AI-generated video clips (Kling, Seedance, Veo, LTX) are typically 5–8 seconds. To cover longer narration segments, we combine them with static images using these transition techniques.

## Freeze techniques

Extend an AI clip by holding its **last frame** with an optional zoom effect. Creates a seamless continuation — the viewer doesn't notice the clip ended.

### Freeze

Hold the last frame, no effect. Just fills time.

```bash
# Extract last frame
ffmpeg -y -sseof -0.1 -i ai-clip.mp4 -vframes 1 -q:v 1 /tmp/lastframe.png

# Static hold
ffmpeg -y -loop 1 -i /tmp/lastframe.png \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p -t ${DURATION} -an /tmp/freeze.mp4
```

### Freeze-zoom-in

Last frame with gentle zoom in. Continues forward momentum. Best default choice — adds subtle life without being distracting.

```bash
ffmpeg -y -sseof -0.1 -i ai-clip.mp4 -vframes 1 -q:v 1 /tmp/lastframe.png

FRAMES=$((DURATION_SEC * 25))
ffmpeg -y -loop 1 -i /tmp/lastframe.png \
  -vf "scale=7680:4320:force_original_aspect_ratio=decrease,pad=7680:4320:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.0+0.08*on/${FRAMES}':x='iw/2-(iw/(1.0+0.08*on/${FRAMES})/2)':y='ih/2-(ih/(1.0+0.08*on/${FRAMES})/2)':d=${FRAMES}:s=7680x4320:fps=25,scale=1920:1080" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an /tmp/freeze-zoomin.mp4
```

Use `0.08` zoom range for subtle continuation. Go up to `0.12` for more noticeable push.

### Freeze-zoom-out

Last frame with zoom out. Reveals wider context after the action. Good for endings or when transitioning to a different scene.

```bash
ffmpeg -y -sseof -0.1 -i ai-clip.mp4 -vframes 1 -q:v 1 /tmp/lastframe.png

FRAMES=$((DURATION_SEC * 25))
ffmpeg -y -loop 1 -i /tmp/lastframe.png \
  -vf "scale=7680:4320:force_original_aspect_ratio=decrease,pad=7680:4320:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.15-0.15*on/${FRAMES}':x='iw/2-(iw/(1.15-0.15*on/${FRAMES})/2)':y='ih/2-(ih/(1.15-0.15*on/${FRAMES})/2)':d=${FRAMES}:s=7680x4320:fps=25,scale=1920:1080" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an /tmp/freeze-zoomout.mp4
```

### Combining freeze with AI clip

Use xfade to seamlessly transition from the AI clip to the frozen frame:

```bash
# 1. Scale AI clip to match (1920x1080, 25fps)
ffmpeg -y -i ai-clip.mp4 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=25" \
  -c:v libx264 -pix_fmt yuv420p -an /tmp/ai-scaled.mp4

# 2. Get AI clip duration
AI_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 /tmp/ai-scaled.mp4)

# 3. xfade into freeze clip
OFFSET=$(python3 -c "print(round(${AI_DUR} - 0.5, 3))")
ffmpeg -y \
  -i /tmp/ai-scaled.mp4 -i /tmp/freeze-zoomin.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=${OFFSET}[vout]" \
  -map "[vout]" -c:v libx264 -pix_fmt yuv420p -an /tmp/combined.mp4
```

## Lead-in

Build anticipation before an AI clip starts. Show the **source image** with a zoom effect, then crossfade into the AI animation. The image "comes alive."

```bash
# Source image zoom in → crossfade → AI clip
FRAMES=$((DURATION_SEC * 25))
ffmpeg -y -loop 1 -i source-image.png \
  -vf "scale=7680:4320:force_original_aspect_ratio=decrease,pad=7680:4320:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.0+0.15*on/${FRAMES}':x='iw/2-(iw/(1.0+0.15*on/${FRAMES})/2)':y='ih/2-(ih/(1.0+0.15*on/${FRAMES})/2)':d=${FRAMES}:s=7680x4320:fps=25,scale=1920:1080" \
  -c:v libx264 -pix_fmt yuv420p -t ${DURATION_SEC} -an /tmp/leadin.mp4

# Crossfade into AI clip
OFFSET=$(python3 -c "print(round(${DURATION_SEC} - 0.5, 3))")
ffmpeg -y \
  -i /tmp/leadin.mp4 -i /tmp/ai-scaled.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=${OFFSET}[vout]" \
  -map "[vout]" -c:v libx264 -pix_fmt yuv420p -an /tmp/combined.mp4
```

Zoom direction matters:
- **Zoom in** — approaching the subject, building intensity
- **Zoom out** — revealing the scene before it animates (used for card-draw reveal)

## Lead-out

AI clip ends, crossfade back to the **source image** with a zoom effect. Use when you want to return to a "clean" version of the image after the AI animation.

```bash
# AI clip → crossfade → source image with zoom out
OFFSET=$(python3 -c "print(round(${AI_DUR} - 0.5, 3))")
ffmpeg -y \
  -i /tmp/ai-scaled.mp4 -i /tmp/zoomout-clip.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=${OFFSET}[vout]" \
  -map "[vout]" -c:v libx264 -pix_fmt yuv420p -an /tmp/combined.mp4
```

## Quick reference

| Technique | Frame source | Zoom | When to use |
|-----------|-------------|------|-------------|
| **Freeze** | Last frame | None | Fill time, minimal distraction |
| **Freeze-zoom-in** | Last frame | In (0.08) | Default extension, subtle life |
| **Freeze-zoom-out** | Last frame | Out | Reveal/ending after action |
| **Lead-in (zoom in)** | Source image | In | Approach subject before animation |
| **Lead-in (zoom out)** | Source image | Out | Reveal scene before animation |
| **Lead-out** | Source image | Any | Return to clean image after animation |

## Key rules

- **Always use 8K internal resolution** (7680x4320) for zoompan to avoid jitter. Downscale to 1920x1080.
- **Extract last frame** with `ffmpeg -sseof -0.1 -vframes 1` — not the first frame.
- **Freeze-zoom-in is the default** when extending AI clips. Only use plain freeze or zoom-out when specifically requested.
- **Lead-in/lead-out use the source image**, freeze techniques use the **last frame**. Don't mix them up.
- **xfade duration**: 0.5s is standard between AI clip and static frame.
- Kling/Seedance output at 24fps with odd resolutions — always scale to 1920x1080 and convert to 25fps before combining.
