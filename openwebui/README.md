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

Enable mic in OpenWebUI in Chrome: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
Add: `http://192.168.4.62:3000`

## Configure Ollama in OpenWebUI

- Navigate to `Settings` > `Admin Settings` > `Settings` (tab) > `Connections` > `Manage Ollama API Connections`
- Enter you remote Ollama server URL: http://<remove_ollama_server_ip>:11434

## Add OpenAI models

- Navigate to `Settings` > `Connections` > `Add connection`
- Provide the base URL: https://api.openai.com/v1
- Add you API key
- Add the model id: o3-mini

## Add other external models

- Each provider requires you to import a function
- Then navigate to `Settings` > `Admin Settings` > `Functions` (tab)
- Edit the function if needed
- Click on `Values` and add your Anthropic API key
- Enable the new function

## Add Claude models

- Import the official Anthropic function: https://openwebui.com/f/justinrahb/anthropic
- Modify the function to leave only desired models. For example:
    ```python
    def get_anthropic_models(self):
        return [
            {"id": "claude-3-opus-20240229", "name": "claude-3-opus"},
            {"id": "claude-3-5-haiku-latest", "name": "claude-3.5-haiku"},
            {"id": "claude-3-5-sonnet-latest", "name": "claude-3.5-sonnet"},
        ]
    ```

## Add Google Gemini models:

- Import the function: https://openwebui.com/f/matthewh/google_genai
- Update the `get_google_models` function content to pull-in only the models you need:
  ```python
  if model.name in ["models/gemini-2.0-flash-thinking-exp", "models/gemini-2.0-pro-exp", "models/gemini-2.0-flash", "models/gemini-1.5-pro"]
  ```

## Add DeepSeek and Gemini models

- Import the function: https://openwebui.com/f/zgccrui/deepseek_r1

This will add the R1 reasoning model, no other modifications are needed
