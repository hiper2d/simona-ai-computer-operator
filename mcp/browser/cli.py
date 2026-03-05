#!/usr/bin/env python3
"""CLI entry point for Browser CDP tools.

Usage:
    uv run python mcp/browser/cli.py tabs
    uv run python mcp/browser/cli.py navigate URL [--tab N]
    uv run python mcp/browser/cli.py content [--tab N] [--selector CSS]
    uv run python mcp/browser/cli.py clickable [--tab N]
    uv run python mcp/browser/cli.py click INDEX [--tab N]
    uv run python mcp/browser/cli.py type TEXT --selector CSS [--tab N]
    uv run python mcp/browser/cli.py scroll [--direction down|up|top|bottom] [--amount N] [--tab N]
    uv run python mcp/browser/cli.py js EXPRESSION [--tab N]
    uv run python mcp/browser/cli.py screenshot [--tab N]
    uv run python mcp/browser/cli.py close TAB_INDEX
    uv run python mcp/browser/cli.py cleanup [--max-age-hours N] [--all]
"""

import asyncio
import sys
from pathlib import Path

# Ensure the package directory is importable
sys.path.insert(0, str(Path(__file__).parent))
from cdp_client import CDPClient
from tools import (
    list_tabs, navigate, get_page_content, list_clickable_elements,
    click_element, take_screenshot, type_text, scroll_page,
    execute_js, cleanup_screenshots, close_tab,
)


def _usage_and_exit():
    print(__doc__.strip())
    sys.exit(1)


def _parse_flag(args: list[str], flag: str, default: str | None = None) -> str | None:
    for i, a in enumerate(args):
        if a == flag and i + 1 < len(args):
            val = args[i + 1]
            del args[i:i + 2]
            return val
    return default


def _has_flag(args: list[str], flag: str) -> bool:
    if flag in args:
        args.remove(flag)
        return True
    return False


async def main():
    args = sys.argv[1:]
    if not args:
        _usage_and_exit()

    command = args.pop(0)
    client = CDPClient()

    try:
        if command == "tabs":
            print(await list_tabs(client))

        elif command == "navigate":
            if not args:
                print("Error: URL required")
                sys.exit(1)
            url = args.pop(0)
            tab = int(_parse_flag(args, "--tab", "0"))
            print(await navigate(client, url, tab_index=tab))

        elif command == "content":
            tab = int(_parse_flag(args, "--tab", "0"))
            selector = _parse_flag(args, "--selector", "")
            print(await get_page_content(client, tab_index=tab, selector=selector))

        elif command == "clickable":
            tab = int(_parse_flag(args, "--tab", "0"))
            print(await list_clickable_elements(client, tab_index=tab))

        elif command == "click":
            if not args:
                print("Error: element index required")
                sys.exit(1)
            index = int(args.pop(0))
            tab = int(_parse_flag(args, "--tab", "0"))
            print(await click_element(client, index, tab_index=tab))

        elif command == "type":
            if not args:
                print("Error: text required")
                sys.exit(1)
            text = args.pop(0)
            selector = _parse_flag(args, "--selector")
            if not selector:
                print("Error: --selector is required for type")
                sys.exit(1)
            tab = int(_parse_flag(args, "--tab", "0"))
            print(await type_text(client, text, selector, tab_index=tab))

        elif command == "scroll":
            direction = _parse_flag(args, "--direction", "down")
            amount = int(_parse_flag(args, "--amount", "500"))
            tab = int(_parse_flag(args, "--tab", "0"))
            print(await scroll_page(client, direction=direction, amount=amount, tab_index=tab))

        elif command == "js":
            if not args:
                print("Error: JavaScript expression required")
                sys.exit(1)
            expression = args.pop(0)
            tab = int(_parse_flag(args, "--tab", "0"))
            print(await execute_js(client, expression, tab_index=tab))

        elif command == "screenshot":
            tab = int(_parse_flag(args, "--tab", "0"))
            print(await take_screenshot(client, tab_index=tab))

        elif command == "close":
            if not args:
                print("Error: tab index required")
                sys.exit(1)
            tab_index = int(args.pop(0))
            print(await close_tab(client, tab_index))

        elif command == "cleanup":
            max_age = float(_parse_flag(args, "--max-age-hours", "24"))
            delete_all = _has_flag(args, "--all")
            print(await cleanup_screenshots(max_age_hours=max_age, delete_all=delete_all))

        else:
            print(f"Unknown command: {command}")
            _usage_and_exit()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
