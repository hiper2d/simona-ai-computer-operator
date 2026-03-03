"""Thin async Chrome DevTools Protocol client.

Uses httpx for HTTP endpoints and websockets for CDP commands.
Connects to Chrome's remote debugging port (default 9222).
"""

import asyncio
import json

import httpx
import websockets


class CDPError(Exception):
    """Error from Chrome DevTools Protocol."""


class CDPClient:
    """Async CDP client for controlling Chrome via DevTools Protocol."""

    def __init__(self, host: str = "localhost", port: int = 9222):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._ws_connections: dict[str, websockets.ClientConnection] = {}
        self._message_id = 0

    def _next_id(self) -> int:
        self._message_id += 1
        return self._message_id

    async def _check_chrome(self) -> None:
        """Verify Chrome is reachable on the debug port."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/json/version")
                resp.raise_for_status()
        except (httpx.ConnectError, httpx.HTTPError) as e:
            raise CDPError(
                f"Cannot connect to Chrome on {self.base_url}. "
                f"Start Chrome with: bash mcp/browser/start-chrome.sh\n"
                f"Error: {e}"
            ) from e

    async def list_targets(self) -> list[dict]:
        """List all debugging targets (tabs, extensions, etc)."""
        await self._check_chrome()
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/json/list")
            resp.raise_for_status()
            return resp.json()

    async def get_pages(self) -> list[dict]:
        """List only page-type targets (actual browser tabs)."""
        targets = await self.list_targets()
        return [t for t in targets if t.get("type") == "page"]

    async def new_tab(self, url: str = "about:blank") -> dict:
        """Open a new tab and return its target info."""
        await self._check_chrome()
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.put(
                f"{self.base_url}/json/new",
                params={"url": url} if url != "about:blank" else None,
            )
            resp.raise_for_status()
            return resp.json()

    async def close_target(self, target_id: str) -> bool:
        """Close a target by its ID."""
        # Disconnect websocket first if connected
        if target_id in self._ws_connections:
            await self._ws_connections[target_id].close()
            del self._ws_connections[target_id]

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{self.base_url}/json/close/{target_id}"
            )
            return resp.text.strip() == "Target is closing"

    async def connect(self, target_id: str) -> websockets.ClientConnection:
        """Connect to a target's WebSocket debugger URL."""
        if target_id in self._ws_connections:
            return self._ws_connections[target_id]

        pages = await self.get_pages()
        target = None
        for page in pages:
            if page["id"] == target_id:
                target = page
                break

        if not target:
            raise CDPError(f"Target {target_id} not found")

        ws_url = target.get("webSocketDebuggerUrl")
        if not ws_url:
            raise CDPError(f"Target {target_id} has no WebSocket debugger URL")

        ws = await websockets.connect(ws_url, max_size=50 * 1024 * 1024)
        self._ws_connections[target_id] = ws
        return ws

    async def send(
        self,
        target_id: str,
        method: str,
        params: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Send a CDP command and wait for the response."""
        ws = await self.connect(target_id)
        msg_id = self._next_id()

        message = {"id": msg_id, "method": method}
        if params:
            message["params"] = params

        await ws.send(json.dumps(message))

        # Wait for the matching response
        deadline = asyncio.get_event_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                raise CDPError(f"Timeout waiting for response to {method}")

            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                data = json.loads(raw)

                if data.get("id") == msg_id:
                    if "error" in data:
                        err = data["error"]
                        raise CDPError(
                            f"CDP error ({err.get('code')}): {err.get('message')}"
                        )
                    return data.get("result", {})
            except asyncio.TimeoutError:
                raise CDPError(f"Timeout waiting for response to {method}")

    async def close(self) -> None:
        """Close all WebSocket connections."""
        for ws in self._ws_connections.values():
            try:
                await ws.close()
            except Exception:
                pass
        self._ws_connections.clear()
