# Browser CDP MCP Server

MCP server for controlling Chrome via the Chrome DevTools Protocol (CDP). Enables Claude Code to navigate, read, click, type, and screenshot web pages — no browser extension required.

## Prerequisites

- Python 3.13+
- Google Chrome
- Shared venv managed by the parent `mcp/` project

## Setup

From the `mcp/` directory:

```bash
uv sync
```

### Start Chrome with Debugging

```bash
bash mcp/browser/start-chrome.sh
```

This launches Chrome with `--remote-debugging-port=9222` using a temporary profile. Cookies are copied from your default Chrome profile so you stay logged in to your accounts.

## Register with Claude Code

Already registered in `.mcp.json` at the project root:

```json
{
  "mcpServers": {
    "browser-cdp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp", "python", "browser/server.py"]
    }
  }
}
```

## Tools

### `list_tabs()`
List all open browser tabs with index, URL, and title.

### `navigate(url, tab_index=0)`
Navigate a tab to a URL. Waits for the page to start loading.

### `get_page_content(tab_index=0, selector="")`
Get text content from a page. Optionally filter with a CSS selector (e.g., `"article"`, `"#main"`, `".post-body"`).

### `list_clickable_elements(tab_index=0)`
List all links and buttons on the page with indices for use with `click_element`.

### `click_element(element_index, tab_index=0)`
Click an element by its index from `list_clickable_elements` output.

### `take_screenshot(tab_index=0)`
Capture a screenshot as PNG. Saved to `~/.cache/browser-cdp/screenshots/`. Returns the file path so Claude can read the image.

### `type_text(text, selector, tab_index=0)`
Type text into an input field. Uses a CSS selector to find the field (e.g., `"input[name='q']"`, `"#search"`).

### `close_tab(tab_index)`
Close a tab by its index.

## `/browser` Skill Usage

```
/browser https://news.ycombinator.com
/browser https://example.com What is the main heading?
/browser
```

- With a URL: navigates and describes the page
- With a URL + question: navigates and answers the question
- Without arguments: lists open tabs

## Architecture

- **`cdp_client.py`** — Thin async CDP client using `websockets` + `httpx`
- **`server.py`** — FastMCP server exposing 8 tools
- **`start-chrome.sh`** — Chrome launcher with debug port

## Cache

Screenshots are stored in `~/.cache/browser-cdp/screenshots/`.
