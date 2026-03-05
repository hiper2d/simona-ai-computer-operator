"""Browser CDP tools — controls Chrome via DevTools Protocol.

Pure library — no MCP dependency. Called by cli.py.
Requires Chrome running with --remote-debugging-port=9222.
"""

import asyncio
import base64
import json
import time
from datetime import datetime
from pathlib import Path

from cdp_client import CDPClient, CDPError

SCREENSHOT_DIR = Path.home() / ".cache" / "browser-cdp" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def _get_page_target_id(client: CDPClient, tab_index: int = 0) -> str:
    """Get the target ID for a page by its index."""
    pages = await client.get_pages()
    if not pages:
        await client.new_tab("about:blank")
        await asyncio.sleep(0.5)
        pages = await client.get_pages()
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


async def list_tabs(client: CDPClient) -> str:
    """List all open browser tabs with their index, URL, and title."""
    try:
        pages = await client.get_pages()
        tabs = [
            {"index": i, "url": p.get("url", ""), "title": p.get("title", "Untitled")}
            for i, p in enumerate(pages)
        ]
        return json.dumps(tabs, indent=2)
    except CDPError as e:
        return json.dumps({"error": str(e)})


async def navigate(client: CDPClient, url: str, tab_index: int = 0) -> str:
    """Navigate a browser tab to a URL."""
    try:
        target_id = await _get_page_target_id(client, tab_index)
        result = await client.send(target_id, "Page.navigate", {"url": url})
        await client.send(target_id, "Page.enable")
        try:
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


async def get_page_content(client: CDPClient, tab_index: int = 0, selector: str = "") -> str:
    """Get text content from a browser tab."""
    try:
        target_id = await _get_page_target_id(client, tab_index)
        await client.send(target_id, "Runtime.enable")

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
                const main = document.querySelector('main') || document.querySelector('article') || document.body;
                return main ? main.innerText : document.body.innerText;
            })()
            """

        result = await client.send(
            target_id, "Runtime.evaluate",
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


async def list_clickable_elements(client: CDPClient, tab_index: int = 0) -> str:
    """List all clickable elements (links and buttons) on the page."""
    try:
        target_id = await _get_page_target_id(client, tab_index)
        await client.send(target_id, "Runtime.enable")

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

        result = await client.send(
            target_id, "Runtime.evaluate",
            {"expression": js, "returnByValue": True},
        )
        return result.get("result", {}).get("value", "[]")
    except CDPError as e:
        return json.dumps({"error": str(e)})


async def click_element(client: CDPClient, element_index: int, tab_index: int = 0) -> str:
    """Click a clickable element by its index from list_clickable_elements."""
    try:
        target_id = await _get_page_target_id(client, tab_index)
        await client.send(target_id, "Runtime.enable")

        js = f"""
        (() => {{
            const clickable = document.querySelectorAll(
                'a[href], button, input[type="submit"], input[type="button"], [role="button"], [onclick]'
            );
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

        result = await client.send(
            target_id, "Runtime.evaluate",
            {"expression": js, "returnByValue": True},
        )
        value = result.get("result", {}).get("value", "{}")
        await asyncio.sleep(1)
        return value
    except CDPError as e:
        return json.dumps({"clicked": False, "error": str(e)})


async def take_screenshot(client: CDPClient, tab_index: int = 0) -> str:
    """Take a screenshot of a browser tab and save it as a PNG file."""
    try:
        target_id = await _get_page_target_id(client, tab_index)
        result = await client.send(
            target_id, "Page.captureScreenshot",
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


async def type_text(client: CDPClient, text: str, selector: str, tab_index: int = 0) -> str:
    """Type text into an input field identified by a CSS selector."""
    try:
        target_id = await _get_page_target_id(client, tab_index)
        await client.send(target_id, "Runtime.enable")

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

        result = await client.send(
            target_id, "Runtime.evaluate",
            {"expression": js, "returnByValue": True},
        )
        return result.get("result", {}).get("value", '{"typed": false, "error": "Unknown error"}')
    except CDPError as e:
        return json.dumps({"typed": False, "error": str(e)})


async def scroll_page(client: CDPClient, direction: str = "down", amount: int = 500, tab_index: int = 0) -> str:
    """Scroll a browser tab in the given direction."""
    try:
        target_id = await _get_page_target_id(client, tab_index)
        await client.send(target_id, "Runtime.enable")

        if direction == "top":
            scroll_expr = "window.scrollTo(0, 0)"
        elif direction == "bottom":
            scroll_expr = "window.scrollTo(0, document.body.scrollHeight)"
        elif direction == "up":
            scroll_expr = f"window.scrollBy(0, -{amount})"
        else:
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

        result = await client.send(
            target_id, "Runtime.evaluate",
            {"expression": js, "returnByValue": True},
        )
        return result.get("result", {}).get("value", "{}")
    except CDPError as e:
        return json.dumps({"error": str(e)})


async def execute_js(client: CDPClient, expression: str, tab_index: int = 0) -> str:
    """Execute arbitrary JavaScript in a browser tab."""
    try:
        target_id = await _get_page_target_id(client, tab_index)
        await client.send(target_id, "Runtime.enable")

        result = await client.send(
            target_id, "Runtime.evaluate",
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


async def cleanup_screenshots(max_age_hours: float = 24, delete_all: bool = False) -> str:
    """Delete old screenshot files from the cache directory."""
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


async def close_tab(client: CDPClient, tab_index: int) -> str:
    """Close a browser tab by its index."""
    try:
        pages = await client.get_pages()
        if tab_index < 0 or tab_index >= len(pages):
            return json.dumps({
                "closed": False,
                "error": f"Tab index {tab_index} out of range (have {len(pages)} tabs)",
            })

        target_id = pages[tab_index]["id"]
        success = await client.close_target(target_id)
        return json.dumps({
            "closed": success,
            "tab_index": tab_index,
            "url": pages[tab_index].get("url", ""),
        })
    except CDPError as e:
        return json.dumps({"closed": False, "error": str(e)})
