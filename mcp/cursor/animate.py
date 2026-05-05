#!/usr/bin/env python3
"""
Cursor click animation effect for video production.

Creates a video clip showing a cursor moving to a target position on a screenshot,
pausing briefly, and performing a click (with a subtle ripple effect).

Usage:
    python3 mcp/cursor/animate.py \
        --image screenshot.png \
        --start 100,50 \
        --target 700,400 \
        --output /tmp/video-assets/cursor-click.mp4 \
        [--duration 2.0] \
        [--pause 0.3] \
        [--fps 25] \
        [--click-effect ripple]

The output is a 1920x1080 video clip with the cursor animation overlaid on the screenshot.
"""

import argparse
import subprocess
import math
import os
import tempfile
import struct
import zlib


def create_cursor_png(path, size=40):
    """Generate a macOS-style cursor PNG."""
    W = size
    H = int(size * 1.45)
    pixels = [(0, 0, 0, 0)] * (W * H)

    def set_px(x, y, color):
        if 0 <= x < W and 0 <= y < H:
            pixels[y * W + x] = color

    # Scale factor relative to 40px base
    s = size / 40.0
    outer = [
        (int(1*s), int(1*s)), (int(1*s), int(44*s)),
        (int(12*s), int(34*s)), (int(19*s), int(50*s)),
        (int(26*s), int(46*s)), (int(19*s), int(31*s)),
        (int(30*s), int(31*s)), (int(1*s), int(1*s))
    ]
    inner = [
        (int(4*s), int(6*s)), (int(4*s), int(39*s)),
        (int(12*s), int(31*s)), (int(20*s), int(46*s)),
        (int(23*s), int(44*s)), (int(16*s), int(29*s)),
        (int(27*s), int(29*s)), (int(4*s), int(6*s))
    ]

    def fill_polygon(points, color):
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        for y in range(min_y, max_y + 1):
            intersections = []
            n = len(points) - 1
            for i in range(n):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                if y1 == y2:
                    continue
                if y < min(y1, y2) or y > max(y1, y2):
                    continue
                x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                intersections.append(x)
            intersections.sort()
            for j in range(0, len(intersections) - 1, 2):
                for x in range(int(intersections[j]), int(intersections[j + 1]) + 1):
                    set_px(x, y, color)

    fill_polygon(outer, (0, 0, 0, 255))
    fill_polygon(inner, (255, 255, 255, 255))

    # Write PNG
    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 6, 0, 0, 0))
    raw = b''
    for y in range(H):
        raw += b'\x00'
        for x in range(W):
            raw += bytes(pixels[y * W + x])
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')

    with open(path, 'wb') as f:
        f.write(header + ihdr + idat + iend)
    return W, H


def ease_in_out(t):
    """Smooth ease-in-out curve (cubic)."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def build_cursor_animation(
    image_path: str,
    start_xy: tuple,
    target_xy: tuple,
    output_path: str,
    move_duration: float = 1.0,
    pause_duration: float = 0.3,
    click_hold: float = 0.25,
    fps: int = 25,
    click_effect: str = "highlight",
    button_rect: tuple = None,
    total_duration: float = None,
):
    """
    Build a video with cursor moving from start to target, pausing, and clicking.

    Args:
        image_path: Background screenshot
        start_xy: (x, y) cursor start position
        target_xy: (x, y) click target position
        output_path: Output video path
        move_duration: Time for cursor to move (seconds)
        pause_duration: Pause before click (seconds)
        click_hold: Duration of click visual effect (seconds)
        fps: Frame rate
        click_effect: "highlight" (brightens button), "ripple" (small box), or "none"
        button_rect: (x, y, w, h) of the button to highlight on click
        total_duration: If set, adds delay at start so click happens at the end
    """
    action_duration = move_duration + pause_duration + click_hold + 0.1
    if total_duration and total_duration > action_duration:
        delay = total_duration - action_duration
    else:
        delay = 0
        total_duration = action_duration

    cursor_dir = os.path.join(tempfile.gettempdir(), "video-assets")
    os.makedirs(cursor_dir, exist_ok=True)
    cursor_path = os.path.join(cursor_dir, "cursor.png")
    if not os.path.exists(cursor_path):
        create_cursor_png(cursor_path)

    sx, sy = start_xy
    tx, ty = target_xy

    dx = tx - sx
    dy = ty - sy
    md = move_duration

    # Eased position expressions (smoothstep), with delay offset
    # Before delay: cursor is hidden (off screen at -100,-100)
    # During move: smoothstep from start to target
    # After move: stays at target
    t_adj = f"(t-{delay})"  # adjusted time after delay
    move_expr = f"3*pow(min({t_adj}/{md},1),2)-2*pow(min({t_adj}/{md},1),3)"
    x_expr = f"if(lt(t,{delay}),-100,{sx}+{dx}*({move_expr}))"
    y_expr = f"if(lt(t,{delay}),-100,{sy}+{dy}*({move_expr}))"

    click_start = delay + move_duration + pause_duration
    click_end = click_start + click_hold

    if click_effect == "highlight" and button_rect:
        bx, by, bw, bh = button_rect
        # Draw a semi-transparent white overlay on the entire button + border
        highlight_filter = (
            f",drawbox=x={bx}:y={by}:w={bw}:h={bh}:"
            f"color=white@0.25:t=fill:"
            f"enable='between(t,{click_start},{click_end})'"
            f",drawbox=x={bx-2}:y={by-2}:w={bw+4}:h={bh+4}:"
            f"color=cyan@0.6:t=2:"
            f"enable='between(t,{click_start},{click_end})'"
        )
    elif click_effect == "ripple":
        highlight_filter = (
            f",drawbox=x={tx-30}:y={ty-15}:w=60:h=30:"
            f"color=white@0.3:t=fill:"
            f"enable='between(t,{click_start},{click_end})'"
        )
    else:
        highlight_filter = ""

    filter_complex = (
        f"[0:v]scale=1920:1080:flags=lanczos,setsar=1,fps={fps}{highlight_filter}[bg];"
        f"[bg][1:v]overlay=x='{x_expr}':y='{y_expr}':format=auto"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", cursor_path,
        "-filter_complex", filter_complex,
        "-t", str(total_duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-an",  # no audio - will be added later
        "-r", str(fps),
        output_path
    ]

    print(f"Generating cursor animation: {start_xy} -> {target_xy} ({total_duration:.1f}s)")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    print(f"Saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Cursor click animation")
    parser.add_argument("--image", required=True, help="Background screenshot")
    parser.add_argument("--start", required=True, help="Start position x,y")
    parser.add_argument("--target", required=True, help="Click target position x,y")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument("--duration", type=float, default=1.5, help="Move duration (seconds)")
    parser.add_argument("--pause", type=float, default=0.3, help="Pause before click")
    parser.add_argument("--click-hold", type=float, default=0.15, help="Click effect duration")
    parser.add_argument("--fps", type=int, default=25, help="Frame rate")
    parser.add_argument("--click-effect", default="highlight", choices=["highlight", "ripple", "none"])
    parser.add_argument("--button", help="Button rect x,y,w,h for highlight effect")
    parser.add_argument("--total-duration", type=float, default=None, help="Total clip duration (click at end)")
    args = parser.parse_args()

    sx, sy = map(int, args.start.split(","))
    tx, ty = map(int, args.target.split(","))

    button_rect = None
    if args.button:
        button_rect = tuple(map(int, args.button.split(",")))

    build_cursor_animation(
        image_path=args.image,
        start_xy=(sx, sy),
        target_xy=(tx, ty),
        output_path=args.output,
        move_duration=args.duration,
        pause_duration=args.pause,
        click_hold=args.click_hold,
        fps=args.fps,
        click_effect=args.click_effect,
        button_rect=button_rect,
        total_duration=args.total_duration,
    )


if __name__ == "__main__":
    main()
