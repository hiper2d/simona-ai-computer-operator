# Introduction

Since I have a PC with an AMD GPU, I decided to use Ollama to run Large Language Models (LLMs) locally. It supports the LLaMA 3.2 with Vision which is basically what I need for Simona.

So the plan is to run the client app with a minimal backend on My MacBook, while the core LLM is on the PC with GPU. WebUI is just for testing the model and having a locally running LLM. It is not needed for the client app.

## Setup Components

- **Ollama**: Local LLM server
- **Ollama WebUI**: Web-based interface for interacting with Ollama
- **Docker**: To run the WebUI
- **Hardware**: Windows system with AMD GPU (Nvidea should work as well)

## Installation & Running

1. First, ensure Ollama is installed and running on your Windows system
2. Launch Ollama WebUI using Docker with the following command:

```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/olama_webui_data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

This command:
- Maps port 3000 on your host to port 8080 in the container
- Enables communication between the container and host machine
- Creates a persistent volume for WebUI data
- Sets the container to automatically restart
- Uses the latest Open WebUI image

## Accessing the Interface

Once running, you can access the Ollama WebUI at:

```
http://localhost:3000
```

## To send API calls in PowerShell

```powershell
(Invoke-WebRequest -method POST -Body '{"model":"llama3.2-vision:11b", "prompt":"Why is the sky blue?", "stream": false}' -uri http://localhost:11434/api/generate ).Content | ConvertFrom-json
```

# The current model I use:

- `llama3.2-vision:11b`
