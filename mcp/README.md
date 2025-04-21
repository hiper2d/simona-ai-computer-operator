# MCP Server

This is web service which provides MCP services to OpenWebUI via an OpenAI compatible API

The MCP server is created using the [FastMCP](https://github.com/jlowin/fastmcp) lib.

### Run MCP server via MCPo proxy server and connect to it in OpenWebUI

To configure this, do the following:
1. Run the MCP server via `mcpo` proxy server:
```bash
uvx mcpo --port 8040 --api-key "snuffy" -- fastmcp run mcp/server.py
```
2. This creates a REST service on the 8040 port with dedicated endpoints to all MCP servers it knows about. Check that the Swagger schema is available at http://localhost:8040/docs
3. In OpenWebUI, go to `Settings` > `Admin Settings` > `Tools` > `Add Connection`. Add the `http://localhost:8040/` base URL and save.
4. This is it. Now, each new chat should show that you have some amount of tools available.

## Memory Tool

This is an MCP with a LightRAG database.

## Credits

- LightRAG [repo](https://github.com/HKUDS/LightRAG)
- [Light RAG MCP Complete, MCP A Day (or Week) Dr. Pat](https://www.youtube.com/watch?v=Jgw2LxjJVvE&ab_channel=PatRuff) Youtube tutorial