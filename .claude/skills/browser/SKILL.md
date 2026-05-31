---
name: browser
description: Browse the web, read pages, click elements, fill forms, and take screenshots using Chrome DevTools Protocol. Use when the user wants to interact with a website, scrape content, or automate browser actions.
argument-hint: [url] [instructions]
allowed-tools: Read, Grep, Glob, Bash(uv run python mcp/browser/cli.py *), Bash(curl *), Bash(bash mcp/browser/start-chrome.sh*), Bash(until curl*)
---

Control Chrome browser via CDP: $ARGUMENTS

## Setup

If Chrome is not running with debugging enabled, start it yourself. Do **not** ask the user to run the script — they only need to be involved if a site requires login.

The script blocks on Chrome's PID (it traps EXIT and kills Chrome on shutdown), so run it as a background Bash task:

```bash
# Start Chrome in background (returns immediately, Chrome stays alive)
bash mcp/browser/start-chrome.sh    # via Bash tool with run_in_background: true

# Then wait for the debug port to come up (also background — fires one notification on success)
until curl -s http://localhost:9222/json/version >/dev/null 2>&1; do sleep 1; done
```

Notes:
- The script uses a **temp profile** that copies cookies from your default Chrome profile, so most sites stay logged in. Some sites (banks, brokerages) bind sessions tightly and will still ask for login — that's the one moment you need the user.
- When you hit a login wall, take a screenshot, tell the user "log in in the Chrome window, then say go," and wait. Don't try to type credentials yourself.
- Chrome dies when the background task ends (session shutdown or user kill). That's intentional — it cleans up the temp profile.

## CLI Tools

All tools are invoked via bash:

```bash
# List open tabs
uv run python mcp/browser/cli.py tabs

# Navigate to a URL
uv run python mcp/browser/cli.py navigate "https://example.com"
uv run python mcp/browser/cli.py navigate "https://example.com" --tab 1

# Get page text content
uv run python mcp/browser/cli.py content
uv run python mcp/browser/cli.py content --selector "article"
uv run python mcp/browser/cli.py content --tab 1 --selector "#main"

# List clickable elements (links, buttons)
uv run python mcp/browser/cli.py clickable

# Click an element by index (from clickable output)
uv run python mcp/browser/cli.py click 3

# Type text into an input field
uv run python mcp/browser/cli.py type "search query" --selector "input[name='q']"

# Scroll the page
uv run python mcp/browser/cli.py scroll --direction down --amount 500
uv run python mcp/browser/cli.py scroll --direction top

# Execute arbitrary JavaScript
uv run python mcp/browser/cli.py js "document.title"

# Set viewport size (REQUIRED before video screenshots — prevents stretching)
uv run python mcp/browser/cli.py viewport 1920x1080 --scale 1

# Send raw CDP command (e.g., full-page screenshot)
uv run python mcp/browser/cli.py cdp "Page.captureScreenshot" '{"format":"png","captureBeyondViewport":true,"clip":{"x":0,"y":0,"width":1920,"height":5000,"scale":1}}'

# Take a screenshot (returns PNG file path — use Read tool to view)
uv run python mcp/browser/cli.py screenshot

# Close a tab
uv run python mcp/browser/cli.py close 1

# Clean up old screenshots
uv run python mcp/browser/cli.py cleanup
uv run python mcp/browser/cli.py cleanup --all
```

## Workflow

1. **`tabs`** — See what tabs are open
2. **`navigate`** — Go to a URL
3. **`content`** — Read the page text (use `--selector` to narrow down)
4. **`clickable`** — Find links and buttons
5. **`click`** — Click by element index
6. **`type`** — Fill in form fields
7. **`scroll`** — Scroll down/up/top/bottom
8. **`js`** — Run arbitrary JavaScript (useful for Shadow DOM, custom extraction)
9. **`screenshot`** — Capture the page as PNG (then use Read tool to view it)
10. **`close`** — Close a tab when done
11. **`cleanup`** — Delete old screenshot files from cache

## Handling $ARGUMENTS

- If a URL is provided (starts with http:// or https:// or contains a dot), **navigate** to it first, then describe what you see using `content`.
- If a question or instruction is given after the URL, use the browser tools to answer it.
- If no arguments, just list the open tabs.

## Tips

### CSS Selectors for `content` and `type`
- `"article"` or `"main"` — main content area
- `"#id"` — element by ID
- `".class"` — element by class
- `"input[name='q']"` — input by name attribute
- `"h1, h2, h3"` — all headings

### Shadow DOM limitations
- Many modern sites (Reddit, YouTube) use Shadow DOM. CSS selectors in `content`, `clickable`, and `type` **cannot reach inside shadow roots**.
- When selectors return nothing on these sites, use `js` to traverse shadow DOM manually, or skip selectors entirely and read the full page content.

### Common patterns
- **Search a site**: `navigate` → `type` into search box → `click` on submit → `content`
- **Read an article**: `navigate` → `content --selector "article"`
- **Fill a form**: `navigate` → `type` for each field → `click` on submit button
- **Screenshot for visual inspection**: `navigate` → `screenshot` → Read the PNG file path returned
- **Scroll through a page**: `navigate` → `scroll --direction down` → `content` (repeat to load more)
- **Infinite scroll / lazy loading**: `scroll --direction down` → wait → `scroll` again to trigger more content
- **Jump to top/bottom**: `scroll --direction top` or `scroll --direction bottom`

### Cleanup
- After browsing sessions, run `cleanup` to free disk space.
- Use `cleanup --all` to wipe the entire cache, or leave defaults to only remove files older than 24 hours.

### Error handling
- If you get a connection error to `localhost:9222`, start Chrome yourself (see Setup section). Don't ask the user.
- If a tab index is out of range, call `tabs` first to show available tabs
- If a selector matches nothing, try a broader selector or omit it

## Advanced: rich-text editors, React inputs, file uploads (CDP learnings, 2026-05-30)

Hard-won while publishing to Substack (ProseMirror/TipTap editor). Reusable for any modern web app.

- **Inject long rich content into a ProseMirror/TipTap editor:** dispatch a synthetic paste — focus the `[contenteditable]`, then `ed.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles:true}))` where `dt` is a `DataTransfer` with `dt.setData('text/html', html)`. The editor parses the HTML into headings/code/quotes/links. `<img src="https://...">` with **public** URLs gets auto-ingested and re-hosted by the app. Pass big HTML via base64: `decodeURIComponent(escape(atob("<b64>")))`. Encode in bash: `base64 < file.html | tr -d '\n'`.
- **Gotcha — paste APPENDS image nodes** even when you select-all to replace; text/headings replace fine but images accumulate. For surgical edits to an already-saved doc, **skip the editor**: fetch the app's draft JSON (`/api/v1/drafts/{id}`), mutate the ProseMirror `content` array (e.g. `splice` out dup nodes), and PUT it back. Run async fetches via `cdp "Runtime.evaluate" {expression, awaitPromise:true, returnByValue:true}` (the `js` CLI command does NOT await promises — it returns `{}` for a pending promise).
- **React-controlled inputs** (`<input>`/`<textarea>`): plain `.value=` won't register. Use the native setter then fire `input`: `Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value').set.call(el,val); el.dispatchEvent(new Event('input',{bubbles:true}))`. Custom widgets (color pickers etc.) often have their own "Save"/commit button — click it after setting.
- **CDP `Input.insertText`** works on focused native inputs (faithful, triggers React). **CDP `Input.dispatchKeyEvent` (Backspace, etc.) does NOT reliably reach ProseMirror keymaps** — don't rely on it for editor node deletion.
- **File upload to a hidden `<input type=file>`:** use `DOM.setFileInputFiles` with the input's `objectId`. **objectIds are session-scoped** — they die between separate `cli.py cdp` calls (each reconnects). Do it in ONE connection: write a short script using `mcp/browser/cdp_client.py` (`CDPClient().send(tid, 'Runtime.evaluate', ...)` to get the objectId, then `send(tid, 'DOM.setFileInputFiles', {files:[abs_path], objectId})` on the same client). Pick the target whose `url` matches the page.
- **Verify, don't trust the UI:** "Saved" badges can be stale. Confirm via the app's API (re-fetch with `cache:'no-store'`) or by curling the live public page.
