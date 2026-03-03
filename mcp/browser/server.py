"""Browser CDP MCP Server.

Controls Chrome via Chrome DevTools Protocol (CDP) over WebSocket.
Requires Chrome running with --remote-debugging-port=9222.
"""

import asyncio
import base64
import json
import time
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from cdp_client import CDPClient, CDPError

SCREENSHOT_DIR = Path.home() / ".cache" / "browser-cdp" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

mcp_server = FastMCP(
    name="browser-cdp",
    timeout=120,
)

# Shared client instance
_client = CDPClient()


async def _get_page_target_id(tab_index: int = 0) -> str:
    """Get the target ID for a page by its index.

    If no page targets exist (e.g. Chrome started with about:blank that isn't
    listed), automatically creates a new tab so callers never get a
    'no tabs found' error when Chrome is actually running.
    """
    pages = await _client.get_pages()
    if not pages:
        # Chrome is running but has no page targets — create one
        await _client.new_tab("about:blank")
        await asyncio.sleep(0.5)
        pages = await _client.get_pages()
        if not pages:
            raise CDPError(
                "No browser tabs found. Is Chrome running with --remote-debugging-port=9222?\n"
                "Start it with: bash mcp/browser/start-chrome.sh"
            )
    if tab_index < 0 or tab_index >= len(pages):
        tab_list = "\n".join(
            f"  [{i}] {p.get('title', 'Untitled')} — {p.get('url', '')}"
            for i, p in enumerate(pages)
        )
        raise CDPError(
            f"Tab index {tab_index} out of range. Available tabs ({len(pages)}):\n{tab_list}"
        )
    return pages[tab_index]["id"]


@mcp_server.tool()
async def list_tabs() -> str:
    """List all open browser tabs with their index, URL, and title.

    Returns:
        JSON array of tab objects with index, url, and title.
    """
    try:
        pages = await _client.get_pages()
        tabs = [
            {"index": i, "url": p.get("url", ""), "title": p.get("title", "Untitled")}
            for i, p in enumerate(pages)
        ]
        return json.dumps(tabs, indent=2)
    except CDPError as e:
        return json.dumps({"error": str(e)})


@mcp_server.tool()
async def navigate(url: str, tab_index: int = 0) -> str:
    """Navigate a browser tab to a URL.

    Args:
        url: The URL to navigate to.
        tab_index: Index of the tab to navigate (default: 0, the first tab).

    Returns:
        JSON with navigation result including final URL and any errors.
    """
    try:
        target_id = await _get_page_target_id(tab_index)
        result = await _client.send(target_id, "Page.navigate", {"url": url})

        # Wait for page to finish loading
        await _client.send(target_id, "Page.enable")
        try:
            # Give the page time to load
            await asyncio.sleep(2)
        except Exception:
            pass

        return json.dumps({
            "navigated": True,
            "url": url,
            "frameId": result.get("frameId", ""),
        })
    except CDPError as e:
        return json.dumps({"navigated": False, "error": str(e)})


@mcp_server.tool()
async def get_page_content(tab_index: int = 0, selector: str = "") -> str:
    """Get text content from a browser tab.

    If a CSS selector is provided, returns only the text content of matching elements.
    Otherwise returns the full page text content.

    Args:
        tab_index: Index of the tab to read (default: 0).
        selector: Optional CSS selector to filter content (e.g., "article", "#main", ".post-body").

    Returns:
        The text content of the page or selected elements.
    """
    try:
        target_id = await _get_page_target_id(tab_index)
        await _client.send(target_id, "Runtime.enable")

        if selector:
            js = f"""
            (() => {{
                const els = document.querySelectorAll({json.dumps(selector)});
                if (els.length === 0) return 'No elements found matching selector: {selector}';
                return Array.from(els).map(el => el.innerText).join('\\n\\n');
            }})()
            """
        else:
            js = """
            (() => {
                // Try to get the main content, fallback to body
                const main = document.querySelector('main') || document.querySelector('article') || document.body;
                return main ? main.innerText : document.body.innerText;
            })()
            """

        result = await _client.send(
            target_id,
            "Runtime.evaluate",
            {"expression": js, "returnByValue": True},
        )
        value = result.get("result", {}).get("value", "")
        if not value:
            exception = result.get("exceptionDetails", {})
            if exception:
                return json.dumps({"error": exception.get("text", "Unknown JS error")})
            return "(empty page)"
        return value
    except CDPError as e:
        return json.dumps({"error": str(e)})


@mcp_server.tool()
async def list_clickable_elements(tab_index: int = 0) -> str:
    """List all clickable elements (links and buttons) on the page.

    Returns elements with an index that can be used with click_element.

    Args:
        tab_index: Index of the tab to scan (default: 0).

    Returns:
        JSON array of clickable elements with index, tag, text, and href.
    """
    try:
        target_id = await _get_page_target_id(tab_index)
        await _client.send(target_id, "Runtime.enable")

        js = """
        (() => {
            const elements = [];
            const clickable = document.querySelectorAll(
                'a[href], button, input[type="submit"], input[type="button"], [role="button"], [onclick]'
            );
            clickable.forEach((el, i) => {
                const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().substring(0, 100);
                if (!text) return;
                elements.push({
                    index: elements.length,
                    tag: el.tagName.toLowerCase(),
                    text: text,
                    href: el.href || '',
                    type: el.type || '',
                });
            });
            return JSON.stringify(elements);
        })()
        """

        result = await _client.send(
            target_id,
            "Runtime.evaluate",
            {"expression": js, "returnByValue": True},
        )
        value = result.get("result", {}).get("value", "[]")
        return value
    except CDPError as e:
        return json.dumps({"error": str(e)})


@mcp_server.tool()
async def click_element(element_index: int, tab_index: int = 0) -> str:
    """Click a clickable element by its index from list_clickable_elements.

    Args:
        element_index: The index of the element to click (from list_clickable_elements output).
        tab_index: Index of the tab (default: 0).

    Returns:
        JSON with click result.
    """
    try:
        target_id = await _get_page_target_id(tab_index)
        await _client.send(target_id, "Runtime.enable")

        js = f"""
        (() => {{
            const clickable = document.querySelectorAll(
                'a[href], button, input[type="submit"], input[type="button"], [role="button"], [onclick]'
            );
            // Filter to only elements with text (matching list_clickable_elements)
            const withText = Array.from(clickable).filter(el => {{
                const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim();
                return text.length > 0;
            }});
            if ({element_index} >= withText.length) {{
                return JSON.stringify({{clicked: false, error: 'Element index {element_index} out of range (max: ' + (withText.length - 1) + ')'}});
            }}
            const el = withText[{element_index}];
            el.click();
            return JSON.stringify({{
                clicked: true,
                tag: el.tagName.toLowerCase(),
                text: (el.innerText || el.value || '').trim().substring(0, 100),
            }});
        }})()
        """

        result = await _client.send(
            target_id,
            "Runtime.evaluate",
            {"expression": js, "returnByValue": True},
        )
        value = result.get("result", {}).get("value", "{}")

        # Give the page a moment to react
        await asyncio.sleep(1)

        return value
    except CDPError as e:
        return json.dumps({"clicked": False, "error": str(e)})


@mcp_server.tool()
async def take_screenshot(tab_index: int = 0) -> str:
    """Take a screenshot of a browser tab and save it as a PNG file.

    The screenshot is saved to ~/.cache/browser-cdp/screenshots/ and the
    absolute file path is returned so Claude can read the image.

    Args:
        tab_index: Index of the tab to screenshot (default: 0).

    Returns:
        JSON with the file path to the saved screenshot PNG.
    """
    try:
        target_id = await _get_page_target_id(tab_index)
        result = await _client.send(
            target_id,
            "Page.captureScreenshot",
            {"format": "png", "quality": 80},
            timeout=15.0,
        )

        img_data = base64.b64decode(result["data"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = SCREENSHOT_DIR / f"screenshot_{timestamp}.png"
        filepath.write_bytes(img_data)

        return json.dumps({
            "path": str(filepath),
            "size_kb": round(len(img_data) / 1024, 1),
        })
    except CDPError as e:
        return json.dumps({"error": str(e)})


@mcp_server.tool()
async def type_text(text: str, selector: str, tab_index: int = 0) -> str:
    """Type text into an input field identified by a CSS selector.

    Args:
        text: The text to type into the field.
        selector: CSS selector for the input field (e.g., "#search", "input[name='q']").
        tab_index: Index of the tab (default: 0).

    Returns:
        JSON with the result.
    """
    try:
        target_id = await _get_page_target_id(tab_index)
        await _client.send(target_id, "Runtime.enable")

        # Focus the element and set its value
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return JSON.stringify({{typed: false, error: 'No element found for selector: {selector}'}});
            el.focus();
            el.value = {json.dumps(text)};
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return JSON.stringify({{
                typed: true,
                selector: {json.dumps(selector)},
                text: {json.dumps(text)},
            }});
        }})()
        """

        result = await _client.send(
            target_id,
            "Runtime.evaluate",
            {"expression": js, "returnByValue": True},
        )
        return result.get("result", {}).get("value", '{"typed": false, "error": "Unknown error"}')
    except CDPError as e:
        return json.dumps({"typed": False, "error": str(e)})


@mcp_server.tool()
async def scroll_page(direction: str = "down", amount: int = 500, tab_index: int = 0) -> str:
    """Scroll a browser tab in the given direction.

    Args:
        direction: Scroll direction — "down", "up", "top", or "bottom".
        amount: Pixels to scroll for "up"/"down" (default 500, ignored for "top"/"bottom").
        tab_index: Index of the tab (default: 0).

    Returns:
        JSON with current scroll position (scrollX, scrollY) and page dimensions.
    """
    try:
        target_id = await _get_page_target_id(tab_index)
        await _client.send(target_id, "Runtime.enable")

        if direction == "top":
            scroll_expr = "window.scrollTo(0, 0)"
        elif direction == "bottom":
            scroll_expr = "window.scrollTo(0, document.body.scrollHeight)"
        elif direction == "up":
            scroll_expr = f"window.scrollBy(0, -{amount})"
        else:  # down
            scroll_expr = f"window.scrollBy(0, {amount})"

        js = f"""
        (() => {{
            {scroll_expr};
            return JSON.stringify({{
                scrollX: Math.round(window.scrollX),
                scrollY: Math.round(window.scrollY),
                pageHeight: document.body.scrollHeight,
                viewportHeight: window.innerHeight,
            }});
        }})()
        """

        result = await _client.send(
            target_id,
            "Runtime.evaluate",
            {"expression": js, "returnByValue": True},
        )
        return result.get("result", {}).get("value", "{}")
    except CDPError as e:
        return json.dumps({"error": str(e)})


@mcp_server.tool()
async def execute_js(expression: str, tab_index: int = 0) -> str:
    """Execute arbitrary JavaScript in a browser tab.

    Useful for advanced DOM manipulation, extracting data from Shadow DOM,
    or performing interactions not covered by other tools.

    Args:
        expression: JavaScript expression or statement to evaluate.
        tab_index: Index of the tab (default: 0).

    Returns:
        JSON with the result value or error details.
    """
    try:
        target_id = await _get_page_target_id(tab_index)
        await _client.send(target_id, "Runtime.enable")

        result = await _client.send(
            target_id,
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
        )

        exc = result.get("exceptionDetails")
        if exc:
            return json.dumps({
                "error": exc.get("text", "JS error"),
                "description": exc.get("exception", {}).get("description", ""),
            })

        value = result.get("result", {}).get("value")
        return json.dumps({"result": value})
    except CDPError as e:
        return json.dumps({"error": str(e)})


@mcp_server.tool()
async def cleanup_screenshots(max_age_hours: float = 24, delete_all: bool = False) -> str:
    """Delete old screenshot files from the cache directory.

    Args:
        max_age_hours: Delete files older than this many hours (default 24).
        delete_all: If true, delete everything regardless of age.

    Returns:
        JSON with count of deleted files and freed space.
    """
    deleted = 0
    freed_bytes = 0
    now = time.time()
    cutoff = now - (max_age_hours * 3600)

    for filepath in SCREENSHOT_DIR.glob("*.png"):
        try:
            if delete_all or filepath.stat().st_mtime < cutoff:
                size = filepath.stat().st_size
                filepath.unlink()
                deleted += 1
                freed_bytes += size
        except OSError:
            pass

    return json.dumps({
        "deleted": deleted,
        "freed_kb": round(freed_bytes / 1024, 1),
        "directory": str(SCREENSHOT_DIR),
    })


@mcp_server.tool()
async def close_tab(tab_index: int) -> str:
    """Close a browser tab by its index.

    Args:
        tab_index: Index of the tab to close (from list_tabs output).

    Returns:
        JSON with the result.
    """
    try:
        pages = await _client.get_pages()
        if tab_index < 0 or tab_index >= len(pages):
            return json.dumps({
                "closed": False,
                "error": f"Tab index {tab_index} out of range (have {len(pages)} tabs)",
            })

        target_id = pages[tab_index]["id"]
        success = await _client.close_target(target_id)
        return json.dumps({
            "closed": success,
            "tab_index": tab_index,
            "url": pages[tab_index].get("url", ""),
        })
    except CDPError as e:
        return json.dumps({"closed": False, "error": str(e)})


if __name__ == "__main__":
    mcp_server.run(transport="stdio")
