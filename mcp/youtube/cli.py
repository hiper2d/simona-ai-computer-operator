#!/usr/bin/env python3
"""CLI entry point for YouTube tools.

Usage:
    uv run python mcp/youtube/cli.py transcript URL [--format text|segments] [--start SEC] [--end SEC] [--lang CODE]
    uv run python mcp/youtube/cli.py code-segments URL [--lang CODE]
    uv run python mcp/youtube/cli.py frames URL --start SEC --end SEC [--fps N]
    uv run python mcp/youtube/cli.py cleanup [--max-age-hours N] [--all]
"""

import sys
from pathlib import Path

# Ensure the package directory is importable
sys.path.insert(0, str(Path(__file__).parent))
from tools import get_youtube_transcript, find_code_segments, get_video_frames, cleanup_cache


def _usage_and_exit():
    print(__doc__.strip())
    sys.exit(1)


def _parse_flag(args: list[str], flag: str, default: str | None = None) -> str | None:
    """Extract --flag value from args list, removing both flag and value."""
    for i, a in enumerate(args):
        if a == flag and i + 1 < len(args):
            val = args[i + 1]
            del args[i:i + 2]
            return val
    return default


def _has_flag(args: list[str], flag: str) -> bool:
    """Check if a boolean flag is present, removing it."""
    if flag in args:
        args.remove(flag)
        return True
    return False


def main():
    args = sys.argv[1:]
    if not args:
        _usage_and_exit()

    command = args.pop(0)

    if command == "transcript":
        if not args:
            print("Error: URL required")
            sys.exit(1)
        url = args.pop(0)
        fmt = _parse_flag(args, "--format", "text")
        lang = _parse_flag(args, "--lang", "en")
        start = float(_parse_flag(args, "--start", "0"))
        end = float(_parse_flag(args, "--end", "0"))
        print(get_youtube_transcript(url, language=lang, format=fmt, start_time=start, end_time=end))

    elif command == "code-segments":
        if not args:
            print("Error: URL required")
            sys.exit(1)
        url = args.pop(0)
        lang = _parse_flag(args, "--lang", "en")
        print(find_code_segments(url, language=lang))

    elif command == "frames":
        if not args:
            print("Error: URL required")
            sys.exit(1)
        url = args.pop(0)
        start = _parse_flag(args, "--start")
        end = _parse_flag(args, "--end")
        if start is None or end is None:
            print("Error: --start and --end are required for frames")
            sys.exit(1)
        fps = float(_parse_flag(args, "--fps", "0.5"))
        print(get_video_frames(url, start_time=float(start), end_time=float(end), fps=fps))

    elif command == "cleanup":
        max_age = float(_parse_flag(args, "--max-age-hours", "24"))
        delete_all = _has_flag(args, "--all")
        print(cleanup_cache(max_age_hours=max_age, delete_all=delete_all))

    else:
        print(f"Unknown command: {command}")
        _usage_and_exit()


if __name__ == "__main__":
    main()
