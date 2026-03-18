"""
Animated highlight capture tool.

Captures frame-by-frame screenshots of a web page with self-drawing SVG
border highlights on DOM elements. Uses Chrome DevTools Protocol.

Usage:
    uv run python mcp/highlight/cli.py capture --url URL --config CONFIG --output DIR
    uv run python mcp/highlight/cli.py capture --url URL --config CONFIG --output DIR --encode OUTPUT.mp4

Config JSON format:
{
    "viewport": {"width": 1400, "height": 900},   // optional, default 1400x900
    "fps": 25,                                      // optional, default 25
    "border_color": "#5BA8D9",                      // optional, default soft blue
    "border_width": 2.5,                            // optional, default 2.5
    "sequence": [
        {"action": "static", "duration": 0.5},
        {"action": "highlight", "selector": "input.name", "duration": 0.8, "hold": 0.4},
        {"action": "highlight", "selector": "button:has-text('Submit')", "duration": 1.2, "hold": 0.6},
        {"action": "clear"},
        {"action": "scroll", "to": "selector:.preview-section", "duration": 1.5},
        {"action": "scroll", "to": "bottom", "duration": 6.0},
        {"action": "click", "selector": "button:has-text('Submit')"},
        {"action": "wait", "condition": "text:Loading complete", "timeout": 60},
        {"action": "static", "duration": 1.0}
    ]
}

Sequence actions:
    static      — Capture frames at current state for `duration` seconds
    highlight   — Draw a self-drawing SVG border around an element
                  selector: CSS selector (supports :has-text('...') for text matching)
                  duration: drawing animation time in seconds
                  hold: seconds to hold after drawing completes (default 0.3)
                  color: override border color for this element (optional)
    clear       — Remove all highlights from the page
    scroll      — Smooth scroll with easing
                  to: pixel value, "bottom", "top", or "selector:CSS_SELECTOR"
                  duration: scroll time in seconds
    click       — Click an element (selector supports :has-text)
    type        — Type text character by character into an input/textarea
                  selector: CSS selector for the input element
                  text: the text to type
                  speed: characters per second (default 12)
                  hold: seconds to hold after typing (default 0.5)
                  focus: whether to focus element first (default true)
    select      — Change a <select> dropdown value (React-aware)
                  selector: CSS selector for the <select>
                  value: option value to select, OR
                  index: option index to select
                  hold: seconds to hold after (default 0.3)
    wait        — Wait for a condition before continuing
                  condition: "text:SOME TEXT" (wait for text to appear on page)
                             "selector:CSS_SELECTOR" (wait for element to exist)
                  timeout: max seconds to wait (default 60)
    js          — Execute arbitrary JavaScript
                  expression: JS code to run
"""
import argparse
import asyncio
import json
import base64
import os
import sys
import httpx
import websockets


HIGHLIGHT_JS_TEMPLATE = """
(() => {{
    if (document.getElementById('hl-overlay')) document.getElementById('hl-overlay').remove();
    const overlay = document.createElement('div');
    overlay.id = 'hl-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99999;';
    document.body.appendChild(overlay);
    window.__hlAnims = [];
    window.__hlCursors = [];
    window.__hlDefaultColor = '{color}';
    window.__hlBorderWidth = {border_width};

    window.__findElement = function(selector) {{
        if (selector.includes(':has-text(')) {{
            const match = selector.match(/(.*):has-text\\('(.*)'\\)/);
            const base = match[1] || '*';
            const text = match[2];
            for (const c of document.querySelectorAll(base)) {{
                if (c.textContent.trim().includes(text)) return c;
            }}
            return null;
        }}
        return document.querySelector(selector);
    }};

    window.__addHighlight = function(selector, durationMs, color) {{
        color = color || window.__hlDefaultColor;
        const el = window.__findElement(selector);
        if (!el) {{ console.error('Not found:', selector); return -1; }}

        const rect = el.getBoundingClientRect();
        const pad = 6;
        const x = rect.left - pad, y = rect.top - pad;
        const w = rect.width + pad * 2, h = rect.height + pad * 2;
        const perimeter = 2 * (w + h);
        const bw = window.__hlBorderWidth;

        const svgNS = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(svgNS, 'svg');
        svg.style.cssText = `position:fixed;left:${{x}}px;top:${{y}}px;width:${{w}}px;height:${{h}}px;overflow:visible;`;
        const border = document.createElementNS(svgNS, 'rect');
        border.setAttribute('x', String(bw/2));
        border.setAttribute('y', String(bw/2));
        border.setAttribute('width', w - bw);
        border.setAttribute('height', h - bw);
        border.setAttribute('rx', '4'); border.setAttribute('ry', '4');
        border.setAttribute('fill', 'none');
        border.setAttribute('stroke', color);
        border.setAttribute('stroke-width', String(bw));
        border.setAttribute('stroke-dasharray', perimeter);
        border.setAttribute('stroke-dashoffset', perimeter);
        border.setAttribute('stroke-linecap', 'round');
        svg.appendChild(border);
        overlay.appendChild(svg);

        const anim = border.animate(
            [{{ strokeDashoffset: perimeter }}, {{ strokeDashoffset: 0 }}],
            {{ duration: durationMs, fill: 'forwards', easing: 'ease-in-out' }}
        );
        anim.pause();

        const cursor = document.createElement('div');
        cursor.style.cssText = `
            position:fixed;width:12px;height:12px;border-radius:50%;display:none;z-index:100000;
            background:radial-gradient(circle,rgba(255,255,255,0.95) 0%,rgba(91,168,217,0.8) 50%,rgba(91,168,217,0) 100%);
            box-shadow:0 0 8px 2px rgba(91,168,217,0.5);pointer-events:none;`;
        overlay.appendChild(cursor);

        const idx = window.__hlAnims.length;
        window.__hlAnims.push({{ anim, border, x, y, w, h, perimeter, durationMs }});
        window.__hlCursors.push(cursor);
        return idx;
    }};

    window.__stepAnimation = function(idx, timeMs) {{
        const info = window.__hlAnims[idx];
        if (!info) return;
        info.anim.currentTime = Math.min(timeMs, info.durationMs);
        const cursor = window.__hlCursors[idx];
        const progress = Math.min(timeMs / info.durationMs, 1);
        if (progress <= 0 || progress >= 1) {{ cursor.style.display = 'none'; return; }}
        cursor.style.display = 'block';
        const {{ x, y, w, h, perimeter }} = info;
        const dist = progress * perimeter;
        let cx, cy;
        if (dist <= w) {{ cx = x + dist; cy = y; }}
        else if (dist <= w + h) {{ cx = x + w; cy = y + (dist - w); }}
        else if (dist <= 2 * w + h) {{ cx = x + w - (dist - w - h); cy = y + h; }}
        else {{ cx = x; cy = y + h - (dist - 2 * w - h); }}
        cursor.style.left = (cx - 6) + 'px';
        cursor.style.top = (cy - 6) + 'px';
    }};

    window.__clearHighlights = function() {{
        overlay.innerHTML = '';
        window.__hlAnims = [];
        window.__hlCursors = [];
    }};

    return 'Highlight system injected';
}})()
"""


class HighlightCapture:
    def __init__(self, config, output_dir, fps=25):
        self.config = config
        self.output_dir = output_dir
        self.fps = config.get("fps", fps)
        self.viewport = config.get("viewport", {"width": 1400, "height": 900})
        self.border_color = config.get("border_color", "#5BA8D9")
        self.border_width = config.get("border_width", 2.5)
        self.frame_num = 0
        self.ws = None
        self.msg_id = 0
        self._hl_injected = False

    async def send(self, method, params=None):
        self.msg_id += 1
        msg = {"id": self.msg_id, "method": method}
        if params:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))
        while True:
            resp = json.loads(await self.ws.recv())
            if resp.get("id") == self.msg_id:
                return resp

    async def js(self, expr):
        r = await self.send("Runtime.evaluate", {
            "expression": expr,
            "awaitPromise": True,
            "returnByValue": True,
        })
        result = r.get("result", {}).get("result", {})
        if result.get("type") == "undefined":
            return None
        return result.get("value")

    async def screenshot(self):
        path = os.path.join(self.output_dir, f"frame_{self.frame_num:05d}.png")
        r = await self.send("Page.captureScreenshot", {"format": "png"})
        with open(path, "wb") as f:
            f.write(base64.b64decode(r["result"]["data"]))
        self.frame_num += 1

    async def inject_highlights(self):
        js_code = HIGHLIGHT_JS_TEMPLATE.format(
            color=self.border_color,
            border_width=self.border_width,
        )
        result = await self.js(js_code)
        self._hl_injected = True
        return result

    async def ensure_injected(self):
        if not self._hl_injected:
            await self.inject_highlights()

    # === Action handlers ===

    async def do_static(self, step):
        duration = step.get("duration", 1.0)
        count = int(duration * self.fps)
        for _ in range(count):
            await self.screenshot()
        print(f"  static: {count} frames ({duration}s)")

    async def do_highlight(self, step):
        await self.ensure_injected()
        selector = step["selector"]
        dur_s = step.get("duration", 0.8)
        hold_s = step.get("hold", 0.3)
        color = step.get("color", "")
        dur_ms = int(dur_s * 1000)

        color_arg = f"'{color}'" if color else "null"
        idx = await self.js(
            f"window.__addHighlight(\"{selector}\", {dur_ms}, {color_arg})"
        )
        if idx is None or idx < 0:
            print(f"  WARNING: element not found for selector: {selector}")
            return

        # Animate frame by frame
        total_frames = int(dur_s * self.fps)
        for i in range(total_frames):
            t = (i / total_frames) * dur_ms
            await self.js(f"window.__stepAnimation({idx}, {t})")
            await self.screenshot()
        # Final frame
        await self.js(f"window.__stepAnimation({idx}, {dur_ms})")

        # Hold
        hold_frames = int(hold_s * self.fps)
        for _ in range(hold_frames):
            await self.screenshot()

        print(f"  highlight '{selector}': {total_frames}+{hold_frames} frames ({dur_s}s + {hold_s}s hold)")

    async def do_clear(self, step):
        await self.js("window.__clearHighlights()")
        self._hl_injected = False
        print("  clear highlights")

    async def do_scroll(self, step):
        target = step["to"]
        duration = step.get("duration", 1.5)
        center = step.get("center", False)

        current_y = await self.js("window.scrollY") or 0

        if target == "bottom":
            page_h = await self.js("document.documentElement.scrollHeight")
            to_y = page_h - self.viewport["height"]
        elif target == "top":
            to_y = 0
        elif isinstance(target, str) and target.startswith("selector:"):
            sel = target[len("selector:"):]
            to_y = await self.js(f"""
                (() => {{
                    const el = window.__findElement ? window.__findElement("{sel}") : document.querySelector("{sel}");
                    if (!el) return {current_y};
                    // Detect sticky/fixed headers
                    let headerH = 0;
                    for (const c of document.querySelectorAll('header, nav, [class*="navbar"], [class*="header"]')) {{
                        const s = getComputedStyle(c);
                        if (s.position === 'sticky' || s.position === 'fixed') {{
                            headerH = Math.max(headerH, c.getBoundingClientRect().height);
                        }}
                    }}
                    const rect = el.getBoundingClientRect();
                    const elPageTop = rect.top + window.scrollY;
                    if ({'true' if center else 'false'}) {{
                        // Center element in usable viewport (below header)
                        const usableH = window.innerHeight - headerH;
                        return Math.max(0, elPageTop - headerH - (usableH - rect.height) / 2);
                    }} else {{
                        const offset = Math.max(headerH + 10, 30);
                        return elPageTop - offset;
                    }}
                }})()
            """)
            if to_y is None:
                to_y = current_y
        else:
            to_y = int(target)

        # Clear highlights before scrolling (they're position:fixed so they'd float)
        if self._hl_injected:
            await self.js("window.__clearHighlights()")
            self._hl_injected = False

        # Force instant scroll behavior (overrides CSS scroll-behavior: smooth)
        await self.js("document.documentElement.style.scrollBehavior = 'auto'")

        total_frames = int(duration * self.fps)
        for i in range(total_frames):
            progress = (i + 1) / total_frames  # +1 so we reach 1.0 on last frame
            # ease-in-out
            if progress < 0.5:
                ease = 2 * progress * progress
            else:
                ease = 1 - (-2 * progress + 2) ** 2 / 2
            y = int(current_y + ease * (to_y - current_y))
            await self.js(f"window.scrollTo(0, {y})")
            await self.screenshot()

        # Ensure we're exactly at the target position
        await self.js(f"window.scrollTo(0, {int(to_y)})")

        print(f"  scroll {current_y} -> {to_y}: {total_frames} frames ({duration}s)")

    async def do_click(self, step):
        selector = step["selector"]
        await self.js(f"""
            (() => {{
                const findEl = window.__findElement || function(s) {{ return document.querySelector(s); }};
                const el = findEl("{selector}");
                if (el) {{ el.click(); return 'clicked'; }}
                return 'not found';
            }})()
        """)
        print(f"  click '{selector}'")

    async def do_wait(self, step):
        condition = step["condition"]
        timeout = step.get("timeout", 60)

        for i in range(int(timeout * 2)):
            await asyncio.sleep(0.5)

            if condition.startswith("text:"):
                text = condition[5:]
                found = await self.js(f"document.body.innerText.includes('{text}')")
            elif condition.startswith("selector:"):
                sel = condition[9:]
                found = await self.js(f"!!document.querySelector('{sel}')")
            else:
                found = True

            if found:
                print(f"  wait '{condition}': ready after {i * 0.5}s")
                return

            if i % 4 == 0:
                print(f"  wait '{condition}': {i * 0.5}s...")

        print(f"  wait '{condition}': TIMEOUT after {timeout}s")

    async def do_type(self, step):
        """Type text character by character into an input/textarea, capturing each frame.

        Handles React controlled components via __reactProps.onChange.
        Params:
            selector: CSS selector (supports :has-text)
            text: text to type
            speed: characters per second (default 12)
            hold: seconds to hold after typing completes (default 0.5)
            focus: whether to focus the element first (default True)
        """
        selector = step["selector"]
        text = step["text"]
        speed = step.get("speed", 12)
        hold = step.get("hold", 0.5)
        do_focus = step.get("focus", True)

        frames_per_char = max(1, int(self.fps / speed))
        escaped_sel = selector.replace('"', '\\"')

        # Focus the element first
        if do_focus:
            await self.js(f"""
                (() => {{
                    const findEl = window.__findElement || function(s) {{ return document.querySelector(s); }};
                    const el = findEl("{escaped_sel}");
                    if (el) el.focus();
                }})()
            """)
            # Capture a couple frames with cursor visible
            await self.screenshot()
            await self.screenshot()

        for i in range(len(text)):
            current_text = text[:i + 1]
            escaped_text = current_text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")

            await self.js(f"""
                (() => {{
                    const findEl = window.__findElement || function(s) {{ return document.querySelector(s); }};
                    const el = findEl("{escaped_sel}");
                    if (!el) return 'not found';
                    const propsKey = Object.keys(el).find(k => k.startsWith('__reactProps'));
                    if (propsKey && el[propsKey].onChange) {{
                        el[propsKey].onChange({{target: {{value: '{escaped_text}'}}}});
                    }} else {{
                        const nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        )?.set || Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, 'value'
                        )?.set;
                        if (nativeSetter) nativeSetter.call(el, '{escaped_text}');
                        else el.value = '{escaped_text}';
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                        el.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    return 'ok';
                }})()
            """)

            for _ in range(frames_per_char):
                await self.screenshot()

        # Hold after typing
        hold_frames = int(hold * self.fps)
        for _ in range(hold_frames):
            await self.screenshot()

        total_frames = len(text) * frames_per_char + hold_frames + (2 if do_focus else 0)
        print(f"  type '{selector}': '{text}' ({len(text)} chars, {total_frames} frames, {total_frames / self.fps:.1f}s)")

    async def do_select(self, step):
        """Change a <select> dropdown value, handling React controlled components.

        Params:
            selector: CSS selector for the <select> element
            value: the option value to select (exact match)
            index: alternatively, the option index to select
            hold: seconds to hold after selection (default 0.3)
        """
        selector = step["selector"]
        value = step.get("value")
        index = step.get("index")
        hold = step.get("hold", 0.3)
        escaped_sel = selector.replace('"', '\\"')

        if value is not None:
            escaped_val = str(value).replace("'", "\\'")
            js_val = f"'{escaped_val}'"
        elif index is not None:
            js_val = f"sel.options[{index}].value"
        else:
            print("  WARNING: select needs 'value' or 'index'")
            return

        await self.js(f"""
            (() => {{
                const findEl = window.__findElement || function(s) {{ return document.querySelector(s); }};
                const sel = findEl("{escaped_sel}");
                if (!sel) return 'not found';
                const newVal = {js_val};
                const propsKey = Object.keys(sel).find(k => k.startsWith('__reactProps'));
                if (propsKey && sel[propsKey].onChange) {{
                    sel[propsKey].onChange({{target: {{value: newVal}}}});
                }} else {{
                    sel.value = newVal;
                    sel.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                return 'selected: ' + newVal;
            }})()
        """)

        hold_frames = int(hold * self.fps)
        for _ in range(hold_frames):
            await self.screenshot()

        print(f"  select '{selector}': {hold_frames} frames ({hold}s)")

    async def do_js(self, step):
        expr = step["expression"]
        result = await self.js(expr)
        print(f"  js: {str(result)[:100]}")

    async def run(self, url):
        os.makedirs(self.output_dir, exist_ok=True)

        # Connect to Chrome
        async with httpx.AsyncClient() as client:
            r = await client.get("http://localhost:9222/json")
            tabs = r.json()

        # Find tab with matching URL, or use first tab
        tab = None
        for t in tabs:
            if url in t.get("url", ""):
                tab = t
                break

        if not tab:
            # Navigate the first non-chrome tab
            for t in tabs:
                if not t.get("url", "").startswith("chrome://"):
                    tab = t
                    break

        if not tab:
            print("ERROR: No suitable browser tab found")
            return

        async with websockets.connect(
            tab["webSocketDebuggerUrl"], max_size=20 * 1024 * 1024
        ) as ws:
            self.ws = ws

            # Set viewport — only if not already matching (avoids React re-render)
            current_vp = await self.js(
                "JSON.stringify({w: window.innerWidth, h: window.innerHeight})"
            )
            needs_viewport = True
            if current_vp and isinstance(current_vp, str):
                import json as _json
                try:
                    vp = _json.loads(current_vp)
                    if vp["w"] == self.viewport["width"] and vp["h"] == self.viewport["height"]:
                        needs_viewport = False
                except Exception:
                    pass

            if needs_viewport:
                await self.send("Emulation.setDeviceMetricsOverride", {
                    "width": self.viewport["width"],
                    "height": self.viewport["height"],
                    "deviceScaleFactor": 1,
                    "mobile": False,
                })
                await asyncio.sleep(0.5)

            # Navigate if needed
            if url not in tab.get("url", ""):
                await self.send("Page.navigate", {"url": url})
                await asyncio.sleep(2)

            await asyncio.sleep(0.3)

            # Clean up any stale highlights from previous captures
            await self.js(
                "(() => { const ol = document.getElementById('hl-overlay');"
                " if (ol) ol.remove(); return 'cleaned'; })()"
            )

            # Execute sequence
            sequence = self.config.get("sequence", [])
            for i, step in enumerate(sequence):
                action = step.get("action", "")
                print(f"Step {i + 1}/{len(sequence)}: {action}")

                handler = getattr(self, f"do_{action}", None)
                if handler:
                    await handler(step)
                else:
                    print(f"  WARNING: unknown action '{action}'")

        print(f"\nDone! {self.frame_num} frames at {self.fps}fps = {self.frame_num / self.fps:.1f}s")
        return self.frame_num


def main():
    parser = argparse.ArgumentParser(description="Animated highlight capture tool")
    sub = parser.add_subparsers(dest="command")

    cap = sub.add_parser("capture", help="Capture highlight frames")
    cap.add_argument("--url", required=True, help="Page URL")
    cap.add_argument("--config", required=True, help="Path to config JSON file")
    cap.add_argument("--output", required=True, help="Output directory for frames")
    cap.add_argument("--encode", help="Also encode frames to this MP4 path")
    cap.add_argument("--scale", default="1920:1080", help="Output scale (default 1920:1080)")
    cap.add_argument("--keep-frames", action="store_true", help="Keep frame PNGs after encoding (default: delete them)")

    args = parser.parse_args()

    if args.command == "capture":
        with open(args.config) as f:
            config = json.load(f)

        capture = HighlightCapture(config, args.output)
        frame_count = asyncio.run(capture.run(args.url))

        if args.encode and frame_count:
            import subprocess
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(config.get("fps", 25)),
                "-i", os.path.join(args.output, "frame_%05d.png"),
                "-vf", f"scale={args.scale}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                args.encode,
            ]
            print(f"\nEncoding to {args.encode}...")
            subprocess.run(cmd, check=True)
            print(f"Video saved: {args.encode}")

            # Clean up frame PNGs unless --keep-frames
            if not args.keep_frames:
                import shutil
                shutil.rmtree(args.output)
                print(f"Cleaned up {frame_count} frame PNGs from {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
