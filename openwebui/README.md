# OpenWebUI

## Install and configure to use local-remote Ollama

Run OpenWebUI from Docker with local Ollama servicer:
```bash
docker run -d -p 3000:8080 -e WEBUI_AUTH=False -e OLLAMA_BASE_URL=http://127.0.0.1:11434 -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

Run Watchtower for autoupdates:
```bash
docker run --rm --volume /var/run/docker.sock:/var/run/docker.sock containrrr/watchtower --run-once open-webui
```
Access OpenWebUI via URL: http://localhost:3000/

Configure Ollama in OpenWebUI:
- Navigate to `Settings` > `Admin Settings` > `Settings` (tab) > `Connections` > `Manage Ollama API Connections`
- Enter you Remove Ollama server URL: http://<remove_ollama_server_ip>:11434

## Add Claude models

- Add this [Anthropic](https://openwebui.com/f/justinrahb/anthropic) function.
- Navigate to `Settings` > `Admin Settings` > `Functions` (tab)
- Enable Anthropic Function
- Click on `Values` and add your Anthropic API key
- Modify the function to leave only desired models. For example:
    ```python
    def get_anthropic_models(self):
        return [
            {"id": "claude-3-opus-20240229", "name": "claude-3-opus"},
            {"id": "claude-3-5-haiku-latest", "name": "claude-3.5-haiku"},
            {"id": "claude-3-5-sonnet-latest", "name": "claude-3.5-sonnet"},
        ]
    ```

## Add DeepSeek and Gemini models

- [DeepSeek](https://openwebui.com/f/zgccrui/deepseek_r1) function
-


Enable mic in OpenWebUI in Chrome: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
Add: `http://192.168.4.62:3000`

How to enable Ollama network:  set env variable `OLLAMA_HOST=0.0.0.0`
How to download Huggingface model to Ollama: https://huggingface.co/docs/hub/en/ollama
How to configure Windows Firewall to enable network connections to Ollama and OpenWebUI (Win): TBD
How to configure local-remove Ollama connectivity: TBD
How to configure OpenWebUI to connect to Ollama service: TBD