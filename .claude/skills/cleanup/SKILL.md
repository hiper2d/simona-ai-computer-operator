---
name: cleanup
description: Clean up temporary files from video production, image generation, and other skills. Use when the user asks to clean up, free disk space, or remove temp files. Lists files before deleting.
argument-hint: [--dry-run] [--keep-assets]
allowed-tools: Bash, Read, Glob
---

Clean up temporary files: $ARGUMENTS

## How it works

Scans known temp locations for files created by video production and other skills. Lists everything found, then deletes after confirmation.

## Flags

- `--dry-run` — list files without deleting
- `--keep-assets` — clean up final temp files but keep `/tmp/video-assets/` (reusable intermediates)

## Steps

1. Scan and report what's found:

```bash
echo "=== /tmp/video-assets/ ==="
if [ -d /tmp/video-assets ]; then
  du -sh /tmp/video-assets
  ls -lh /tmp/video-assets/
else
  echo "(empty)"
fi

echo ""
echo "=== Video production temp files ==="
ls -lh /tmp/clip*.mp4 /tmp/scene*.mp4 /tmp/s[0-9]*.mp4 \
  /tmp/*-scaled.png /tmp/*-fullpage.png /tmp/section-*.png \
  /tmp/concat*.txt /tmp/black*.mp4 \
  /tmp/veo-*.json /tmp/veo-*.txt \
  /tmp/*-video.mp4 /tmp/*-audio.aac \
  /tmp/cover-*.mp4 /tmp/veo-*.mp4 /tmp/intro-*.mp4 2>/dev/null || echo "(none)"

echo ""
echo "=== Highlight capture frames ==="
ls -d /tmp/*-frames/ 2>/dev/null && du -sh /tmp/*-frames/ || echo "(none)"

echo ""
echo "=== Highlight configs ==="
ls -lh /tmp/*-highlights*.json 2>/dev/null || echo "(none)"

echo ""
echo "=== Browser screenshots ==="
ls -lh /tmp/*-screenshot*.png /tmp/*-fullpage*.png 2>/dev/null || echo "(none)"
```

2. If `--dry-run`, stop here and report total size.

3. If `--keep-assets`, skip `/tmp/video-assets/`.

4. Delete everything found:

```bash
# Video production
rm -f /tmp/clip*.mp4 /tmp/scene*.mp4 /tmp/s[0-9]*.mp4
rm -f /tmp/*-scaled.png /tmp/*-fullpage.png /tmp/section-*.png
rm -f /tmp/concat*.txt /tmp/black*.mp4
rm -f /tmp/veo-*.json /tmp/veo-*.txt
rm -f /tmp/*-video.mp4 /tmp/*-audio.aac
rm -f /tmp/cover-*.mp4 /tmp/veo-*.mp4 /tmp/intro-*.mp4

# Highlight capture
rm -rf /tmp/*-frames/
rm -f /tmp/*-highlights*.json

# Browser screenshots
rm -f /tmp/*-screenshot*.png /tmp/*-fullpage*.png

# Video assets (unless --keep-assets)
rm -rf /tmp/video-assets/

echo "Cleanup complete."
```

5. Report what was deleted and how much space was freed.

## What is NOT cleaned

- `generated-videos/` — final output, never auto-deleted
- `generated-audio/` — narration files, never auto-deleted
- `generated-images/` — image files, never auto-deleted
- `.env` — credentials, never touched

These directories are only cleaned manually by the user.
