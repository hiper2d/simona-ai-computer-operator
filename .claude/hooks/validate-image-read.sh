#!/bin/bash
# PreToolUse hook for Read: refuse to read malformed image files so the API
# never sees bad bytes that would 400 ("Could not process image") and kill
# the session. Validates size + magic bytes for png/jpg/gif/webp/bmp.

set -euo pipefail

input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')

[ -z "$file_path" ] && exit 0
[ ! -f "$file_path" ] && exit 0

ext=$(printf '%s' "${file_path##*.}" | tr '[:upper:]' '[:lower:]')
case "$ext" in
  png|jpg|jpeg|gif|webp|bmp) ;;
  *) exit 0 ;;
esac

size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo 0)
if [ "$size" -lt 100 ]; then
  echo "Refusing to read $file_path: only ${size} bytes — almost certainly corrupted (real images are >1KB). Delete or regenerate before retrying." >&2
  exit 2
fi

header=$(xxd -p -l 12 "$file_path" 2>/dev/null | tr -d '\n')

case "$ext" in
  png)
    case "$header" in
      89504e47*) ;;
      *) echo "Refusing to read $file_path: .png extension but file starts with '$header' (PNG magic is 89504e47). Corrupted file." >&2; exit 2 ;;
    esac
    ;;
  jpg|jpeg)
    case "$header" in
      ffd8ff*) ;;
      *) echo "Refusing to read $file_path: .jpg extension but file starts with '$header' (JPEG magic is ffd8ff). Corrupted file." >&2; exit 2 ;;
    esac
    ;;
  gif)
    case "$header" in
      474946383761*|474946383961*) ;;
      *) echo "Refusing to read $file_path: .gif extension but file starts with '$header' (GIF magic is GIF87a/GIF89a). Corrupted file." >&2; exit 2 ;;
    esac
    ;;
  webp)
    case "$header" in
      52494646????????57454250*) ;;
      *) echo "Refusing to read $file_path: .webp extension but does not match RIFF/WEBP container. Corrupted file." >&2; exit 2 ;;
    esac
    ;;
  bmp)
    case "$header" in
      424d*) ;;
      *) echo "Refusing to read $file_path: .bmp extension but file starts with '$header' (BMP magic is 424d). Corrupted file." >&2; exit 2 ;;
    esac
    ;;
esac

exit 0
