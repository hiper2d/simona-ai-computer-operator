"""YouTube transcript extraction, code segment detection, and frame capture.

Pure library — no MCP dependency. Called by cli.py.
"""

import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi

CACHE_DIR = Path.home() / ".cache" / "youtube-analyzer"

# Code-related keywords used to detect code segments in transcripts
CODE_KEYWORDS = [
    "code", "function", "class", "method", "variable", "import", "return",
    "def ", "const ", "let ", "var ", "if ", "else ", "for ", "while ",
    "print", "console", "log", "error", "debug",
    "api", "endpoint", "request", "response",
    "html", "css", "javascript", "python", "java", "typescript",
    "react", "component", "hook", "state", "props",
    "database", "query", "sql", "table",
    "terminal", "command", "run", "install", "npm", "pip",
    "file", "directory", "path", "config",
    "here you can see", "as you can see", "let me show", "look at",
    "on the screen", "in the editor", "in the code", "this line",
    "type", "write", "paste", "copy", "snippet", "example",
]


def extract_video_id(video_url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    parsed = urlparse(video_url)

    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")

    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]
        if parsed.path.startswith("/embed/") or parsed.path.startswith("/v/"):
            return parsed.path.split("/")[2]

    raise ValueError(f"Could not extract video ID from URL: {video_url}")


def get_cache_path(video_id: str) -> Path:
    """Get the cache directory for a specific video."""
    path = CACHE_DIR / video_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_youtube_transcript(
    video_url: str,
    language: str = "en",
    format: str = "text",
    start_time: float = 0.0,
    end_time: float = 0.0,
) -> str:
    """Fetch captions/transcript from a YouTube video.

    Args:
        video_url: Full YouTube URL (e.g. https://www.youtube.com/watch?v=abc123)
        language: Language code for captions (default: "en")
        format: Output format — "text" for plain text, "segments" for JSON with timestamps.
        start_time: Only include segments starting at or after this time in seconds (0 = start)
        end_time: Only include segments up to this time in seconds (0 = entire video)

    Returns:
        If format="text": Plain transcript text with paragraph breaks every ~60 seconds.
        If format="segments": JSON array of {text, start, duration} objects.
    """
    video_id = extract_video_id(video_url)

    # Always fetch and cache full segments first
    cache_path = get_cache_path(video_id)
    transcript_file = cache_path / f"transcript_{language}.json"

    if transcript_file.exists():
        segments = json.loads(transcript_file.read_text())
    else:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=[language])

        segments = []
        for entry in transcript.snippets:
            segments.append({
                "text": entry.text,
                "start": entry.start,
                "duration": entry.duration,
            })

        transcript_file.write_text(json.dumps(segments, indent=2))

    # Apply time range filter
    if start_time > 0 or end_time > 0:
        filtered = []
        for seg in segments:
            seg_start = seg["start"]
            if start_time > 0 and seg_start < start_time:
                continue
            if end_time > 0 and seg_start > end_time:
                break
            filtered.append(seg)
        segments = filtered

    if not segments:
        return "No transcript segments found for the specified time range."

    # Return in requested format
    if format == "segments":
        return json.dumps(segments, indent=2)

    # Plain text format: concatenate with paragraph breaks every ~60s
    paragraphs = []
    current_para = []
    para_start_time = segments[0]["start"]

    for seg in segments:
        current_para.append(seg["text"])
        if seg["start"] - para_start_time >= 60.0:
            paragraphs.append(" ".join(current_para))
            current_para = []
            para_start_time = seg["start"]

    if current_para:
        paragraphs.append(" ".join(current_para))

    first_time = segments[0]["start"]
    last_seg = segments[-1]
    last_time = last_seg["start"] + last_seg["duration"]

    header = (
        f"[Transcript: {len(segments)} segments, "
        f"{first_time:.0f}s – {last_time:.0f}s]\n\n"
    )

    return header + "\n\n".join(paragraphs)


def find_code_segments(
    video_url: str,
    language: str = "en",
) -> str:
    """Analyze transcript to find time ranges where code is likely shown on screen.

    Returns:
        JSON string with list of detected code segments.
    """
    # Must request segments format so we can json.loads() the result
    transcript_json = get_youtube_transcript(video_url, language, format="segments")
    segments = json.loads(transcript_json)

    if not segments:
        return json.dumps([])

    # Sliding window: 30s window, 15s step
    window_size = 30.0
    step_size = 15.0

    video_end = max(s["start"] + s["duration"] for s in segments)
    code_segments = []

    current_start = 0.0
    while current_start < video_end:
        window_end = current_start + window_size

        window_text = ""
        for seg in segments:
            seg_start = seg["start"]
            seg_end = seg_start + seg["duration"]
            if seg_start < window_end and seg_end > current_start:
                window_text += " " + seg["text"]

        window_text_lower = window_text.lower()

        keywords_found = []
        for kw in CODE_KEYWORDS:
            if kw.lower() in window_text_lower:
                keywords_found.append(kw.strip())

        keywords_found = list(set(keywords_found))

        if keywords_found:
            confidence = min(len(keywords_found) / 8.0, 1.0)

            if confidence >= 0.25:
                code_segments.append({
                    "start_time": round(current_start, 1),
                    "end_time": round(min(window_end, video_end), 1),
                    "confidence": round(confidence, 2),
                    "keywords_found": keywords_found,
                })

        current_start += step_size

    # Merge overlapping segments
    merged = []
    for seg in code_segments:
        if merged and seg["start_time"] <= merged[-1]["end_time"]:
            prev = merged[-1]
            prev["end_time"] = seg["end_time"]
            prev["confidence"] = max(prev["confidence"], seg["confidence"])
            prev["keywords_found"] = list(
                set(prev["keywords_found"] + seg["keywords_found"])
            )
        else:
            merged.append(dict(seg))

    return json.dumps(merged, indent=2)


def get_video_frames(
    video_url: str,
    start_time: float,
    end_time: float,
    fps: float = 0.5,
) -> str:
    """Download a YouTube video segment and extract frames as PNG images.

    Returns:
        JSON string with list of extracted frame file paths.
    """
    video_id = extract_video_id(video_url)
    cache_path = get_cache_path(video_id)

    video_file = cache_path / "video.mp4"
    if not video_file.exists():
        try:
            subprocess.run(
                [
                    "yt-dlp",
                    "-f", "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst",
                    "-o", str(video_file),
                    "--no-playlist",
                    "--quiet",
                    video_url,
                ],
                check=True,
                timeout=90,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            return json.dumps({"error": f"Failed to download video: {e.stderr}"})

    if not video_file.exists():
        return json.dumps({"error": "Video file was not created after download"})

    segment_hash = hashlib.md5(
        f"{start_time}-{end_time}-{fps}".encode()
    ).hexdigest()[:8]
    frames_dir = cache_path / f"frames_{segment_hash}"
    frames_dir.mkdir(exist_ok=True)

    existing_frames = sorted(frames_dir.glob("*.png"))
    if existing_frames:
        return json.dumps({
            "frames": [str(f) for f in existing_frames],
            "count": len(existing_frames),
            "segment": {"start_time": start_time, "end_time": end_time, "fps": fps},
        }, indent=2)

    duration = end_time - start_time
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-ss", str(start_time),
                "-i", str(video_file),
                "-t", str(duration),
                "-vf", f"fps={fps}",
                "-frame_pts", "1",
                str(frames_dir / "frame_%04d.png"),
                "-y",
                "-loglevel", "error",
            ],
            check=True,
            timeout=60,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        return json.dumps({"error": f"Failed to extract frames: {e.stderr}"})

    extracted_frames = sorted(frames_dir.glob("*.png"))

    return json.dumps({
        "frames": [str(f) for f in extracted_frames],
        "count": len(extracted_frames),
        "segment": {"start_time": start_time, "end_time": end_time, "fps": fps},
    }, indent=2)


def cleanup_cache(
    max_age_hours: float = 24.0,
    delete_all: bool = False,
) -> str:
    """Remove old cached videos and extracted frames.

    Returns:
        JSON string with cleanup summary.
    """
    if not CACHE_DIR.exists():
        return json.dumps({"message": "Cache directory does not exist", "deleted": 0})

    deleted_count = 0
    freed_bytes = 0
    now = time.time()
    max_age_seconds = max_age_hours * 3600

    if delete_all:
        for item in CACHE_DIR.iterdir():
            if item.is_dir():
                size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                freed_bytes += size
                shutil.rmtree(item)
                deleted_count += 1
    else:
        for item in CACHE_DIR.iterdir():
            if item.is_dir():
                mtime = item.stat().st_mtime
                if (now - mtime) > max_age_seconds:
                    size = sum(
                        f.stat().st_size for f in item.rglob("*") if f.is_file()
                    )
                    freed_bytes += size
                    shutil.rmtree(item)
                    deleted_count += 1

    freed_mb = round(freed_bytes / (1024 * 1024), 2)

    return json.dumps({
        "deleted_videos": deleted_count,
        "freed_mb": freed_mb,
        "cache_dir": str(CACHE_DIR),
    }, indent=2)
