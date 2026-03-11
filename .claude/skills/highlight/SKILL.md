---
name: highlight
description: Capture animated UI highlights on web pages — self-drawing SVG borders around DOM elements with a cursor dot. Use when creating video clips that explain web app interfaces, walk through forms, or demonstrate UI flows.
argument-hint: <config-path or instructions for what to highlight>
allowed-tools: Bash(uv run python mcp/highlight/cli.py *), Read, Write, Glob
---

Capture animated web page highlights: $ARGUMENTS

## What this does

Creates video clips where SVG borders draw themselves around real DOM elements on a web page, with a glowing cursor dot tracing the path. Borders are pixel-perfect because they're positioned using the element's actual bounding rect via Chrome DevTools Protocol.

## Requirements

- Chrome running with `--remote-debugging-port=9222` (run `bash mcp/browser/start-chrome.sh` if not running)
- The target page must be open in Chrome (or the tool will navigate to it)

## CLI Usage

```bash
# Capture frames + encode to MP4
uv run python mcp/highlight/cli.py capture \
  --url "http://localhost:3000/some-page" \
  --config path/to/config.json \
  --output /tmp/frames/ \
  --encode /tmp/output.mp4

# Capture frames only (encode later with ffmpeg)
uv run python mcp/highlight/cli.py capture \
  --url "https://example.com" \
  --config config.json \
  --output /tmp/frames/

# Custom output scale (default 1920:1080)
uv run python mcp/highlight/cli.py capture \
  --url URL --config config.json --output /tmp/frames/ \
  --encode output.mp4 --scale 1920:1080
```

## Config format

```json
{
    "viewport": {"width": 1400, "height": 900},
    "fps": 25,
    "border_color": "#5BA8D9",
    "border_width": 2.5,
    "sequence": [
        {"action": "static", "duration": 0.5},
        {"action": "highlight", "selector": "input.name", "duration": 0.8, "hold": 0.3},
        {"action": "highlight", "selector": "button:has-text('Submit')", "duration": 1.2, "hold": 0.5, "color": "#FFB74D"},
        {"action": "clear"},
        {"action": "scroll", "to": "selector:.results", "duration": 1.5},
        {"action": "scroll", "to": "bottom", "duration": 6.0},
        {"action": "click", "selector": "button:has-text('Submit')"},
        {"action": "wait", "condition": "text:Results loaded", "timeout": 60},
        {"action": "js", "expression": "document.title"},
        {"action": "static", "duration": 1.0}
    ]
}
```

## Actions

| Action | Params | Description |
|--------|--------|-------------|
| `static` | `duration` (seconds) | Capture frames of current state |
| `highlight` | `selector`, `duration` (seconds), `hold` (seconds, default 0.3), `color` (optional override) | Draw an animated SVG border around an element. Highlights accumulate — previous ones stay visible. |
| `clear` | — | Remove all highlights. **Must clear before scrolling** (highlights are position:fixed and would float). |
| `scroll` | `to` (px, "top", "bottom", or "selector:CSS"), `duration` (seconds) | Smooth scroll with ease-in-out. Auto-clears highlights. |
| `click` | `selector` | Click an element |
| `wait` | `condition` ("text:..." or "selector:..."), `timeout` (seconds, default 60) | Wait for content to appear. Use after clicking buttons that trigger async operations. |
| `js` | `expression` | Execute arbitrary JavaScript |

## Selectors

Standard CSS selectors plus:
- **`:has-text('Button Text')`** — matches elements containing specific text (e.g., `button:has-text('Submit')`)
- **`selector:` prefix in scroll `to`** — scroll to an element (e.g., `"to": "selector:h2:has-text('Results')"`)

## Styling

- **Default border**: `#5BA8D9` (soft blue), 2.5px, rounded corners
- **Override per-element**: `"color": "#FFB74D"` (amber) for emphasis
- **Cursor dot**: 12px radial gradient with glow, follows the drawing edge
- **For dark UIs**: use `#5BA8D9` (blue) or `#66CCFF` (lighter blue)
- **For light UIs**: use `#2196F3` (material blue) or `#FF9800` (orange)

## Tips

- **Drawing speed**: 0.6-0.8s for small elements (inputs, buttons), 1.0-1.2s for large areas
- **Hold time**: 0.2-0.3s for quick items, 0.5-0.8s for key elements
- **Always `clear` before `scroll`** — the tool does this automatically for scroll actions
- **Re-inject after clear**: the tool auto-reinjects when the next highlight action runs
- **Combine with video skill**: highlight clips can be concatenated with zoom/scroll clips using ffmpeg
- **Frame count**: ~100ms per frame capture, a 20s clip (500 frames) takes ~50s to capture
