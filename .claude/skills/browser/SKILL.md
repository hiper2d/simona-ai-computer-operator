---
name: browser
description: Browse the web, read pages, click elements, fill forms, and take screenshots using Chrome DevTools Protocol. Use when the user wants to interact with a website, scrape content, or automate browser actions.
argument-hint: [url] [instructions]
allowed-tools: Read, Grep, Glob, Bash(curl *)
---

Control Chrome browser via CDP: $ARGUMENTS

You have a `browser-cdp` MCP server that controls Chrome through the DevTools Protocol. Use these tools to browse the web, read pages, interact with elements, and take screenshots.

## Setup

If Chrome is not running with debugging enabled, tell the user to run:
```
bash mcp/browser/start-chrome.sh
```

## Workflow

1. **`list_tabs`** — See what tabs are open
2. **`navigate`** — Go to a URL
3. **`get_page_content`** — Read the page text (use `selector` to narrow down)
4. **`list_clickable_elements`** — Find links and buttons
5. **`click_element`** — Click by element index
6. **`type_text`** — Fill in form fields
7. **`scroll_page`** — Scroll down/up/top/bottom (set `direction` and `amount` in pixels)
8. **`execute_js`** — Run arbitrary JavaScript (useful for Shadow DOM, custom extraction)
9. **`take_screenshot`** — Capture the page as PNG (then use Read tool to view it)
10. **`close_tab`** — Close a tab when done
11. **`cleanup_screenshots`** — Delete old screenshot files from cache

## Handling $ARGUMENTS

- If a URL is provided (starts with http:// or https:// or contains a dot), **navigate** to it first, then describe what you see using `get_page_content`.
- If a question or instruction is given after the URL, use the browser tools to answer it.
- If no arguments, just list the open tabs.

## Tips

### CSS Selectors for `get_page_content` and `type_text`
- `"article"` or `"main"` — main content area
- `"#id"` — element by ID
- `".class"` — element by class
- `"input[name='q']"` — input by name attribute
- `"h1, h2, h3"` — all headings

### Shadow DOM limitations
- Many modern sites (Reddit, YouTube) use Shadow DOM. CSS selectors in `get_page_content`, `list_clickable_elements`, and `type_text` **cannot reach inside shadow roots**.
- When selectors return nothing on these sites, use `execute_js` to traverse shadow DOM manually, or skip selectors entirely and read the full page content.

### Common patterns
- **Search a site**: `navigate` → `type_text` into search box → `click_element` on submit → `get_page_content`
- **Read an article**: `navigate` → `get_page_content` with selector `"article"` or `"main"`
- **Fill a form**: `navigate` → `type_text` for each field → `click_element` on submit button
- **Screenshot for visual inspection**: `navigate` → `take_screenshot` → Read the PNG file path returned
- **Scroll through a page**: `navigate` → `scroll_page` direction="down" → `get_page_content` (repeat to load more)
- **Infinite scroll / lazy loading**: `scroll_page` direction="down" → wait → `scroll_page` again to trigger more content
- **Jump to top/bottom**: `scroll_page` direction="top" or `scroll_page` direction="bottom"

### Cleanup
- After browsing sessions, run `cleanup_screenshots` to free disk space.
- Use `cleanup_screenshots` with `delete_all: true` to wipe the entire cache, or leave defaults to only remove files older than 24 hours.

### Error handling
- If you get a connection error, remind the user to start Chrome: `bash mcp/browser/start-chrome.sh`
- If a tab index is out of range, call `list_tabs` first to show available tabs
- If a selector matches nothing, try a broader selector or omit it
