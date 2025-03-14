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

## Add Kokoro (realistic local voice model)

We need [Kokoro FastAPI](https://github.com/remsky/Kokoro-FastAPI?tab=readme-ov-file).
Read the documentation of Kokoro FastAPI in OpenWebUI [here](https://docs.openwebui.com/tutorials/text-to-speech/Kokoro-FastAPI-integration).

Run it from Docker:
```bash
docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:v0.2.2 # CPU
```

Add it to OpenWebUI:
1. Navigate to `Settings` > `Admin Settings` > `Settings` (tab) > `Audio` > `TTS Settings`
   - Choose "OpenAI"
   - Text-to-Speech Engine: `http://host.docker.internal:8880/v1`
   - API key: "not-needed" (type this text literally)
   - TTS Model: kokoro
   - TTS Voice: af_sky (or pick any other voice from the [docs](https://docs.openwebui.com/tutorials/text-to-speech/Kokoro-FastAPI-integration#voices))

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

### Add Anthropic Claude models

There is a nice Anthropic function in this Github repo: https://github.com/carlosaln/open-webui-functions

Follow the instructions and copy the anthropic.py function code. It will add the following models:
- Claude 3.7 Sonnet (latest)
- Claude 3.7 Sonnet (latest) with Extended Reasoning
- Claude 3.5 Sonnet (latest)

### Add Google Gemini models

- Import the function: https://openwebui.com/f/matthewh/google_genai
- Update the `get_google_models` function content to pull-in only the models you need:
  ```python
  def get_google_models(self):
      models = []
      available_models = [
          "models/gemini-2.0-flash-thinking-exp",
          "models/gemini-2.0-pro-exp",
          "models/gemini-2.0-flash",
          "models/gemini-1.5-pro"
      ]
      for model in self.models:
          if model.name in available_models:
              models.append(model)
      return models
  ```

Find model names here: https://ai.google.dev/gemini-api/docs/models/gemini
Also, get yourself familiar with limits: https://ai.google.dev/gemini-api/docs/rate-limits#paid-tier-1

### Add DeepSeek R1 model

- Import the function: https://openwebui.com/f/zgccrui/deepseek_r1

This will add the R1 reasoning model, no other modifications are needed
