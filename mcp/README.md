# MCP Server

This is web service which provides MCP services to OpenWebUI via an OpenAI compatible API

The server is created the [FastMCP](https://github.com/jlowin/fastmcp) lib by this [video example](https://www.youtube.com/watch?v=v_NSfjNszU0&t=1185s&ab_channel=NeuralNine) ([code](https://github.com/NeuralNine/youtube-tutorials/tree/main/MCP%20Tutorial/my-mcp-server)). This [example](https://www.youtube.com/watch?v=wa_A0qY0anA&t=294s&ab_channel=MatthewBerman) ([code](https://gist.github.com/mberman84/2faeddf57113826d7440bfadbe5ce6e5)) is almost the same but it shows that FastMCP also can run on a custom port.

### Run MCP server via MCPo proxy server and connect to it in OpenWebUI

To configure this, do the following:
1. Run the `mcp-server-time` MCP server and `mcpo` proxy server:
```bash
uvx mcpo --port 8040 --api-key "snuffy" -- fastmcp run mcp/server.py
```
2. This creates a REST service on the 8040 port with dedicated endpoints to all MCP servers it knows about. Check that the Swagger schema is available at http://localhost:8040/docs
3. In OpenWebUI, go to `Settings` > `Admin Settings` > `Tools` > `Add Connection`. Add the `http://localhost:8040/` base URL and save.
4. This is it. Now, each new chat should show that you have some amount of tools available.

### Connect OpenWebUI



## Memory Tool

This is an MCP with a LightRAG database.

## Credits

- LightRAG [repo](https://github.com/HKUDS/LightRAG)
- [Light RAG MCP Complete, MCP A Day (or Week) Dr. Pat](https://www.youtube.com/watch?v=Jgw2LxjJVvE&ab_channel=PatRuff) Youtube tutorial