# LLaMA FastAPI Web Service

## Introduction

This project provides a FastAPI web service for running LLaMA models locally, with support for GPU acceleration using
NVIDIA GPUs. The web service allows you to:

- Download LLaMA models directly from Hugging Face via API calls.
- Load models into memory for inference.
- Generate text completions through API endpoints.
- Manage models without the need to include them inside the Docker image.

The application can be run locally or inside a Docker container, making it easy to deploy on various systems, including those with NVIDIA GPUs for acceleration.

## Features

1. **Model Management via API**:
  - Download models from Hugging Face repositories.
  - Load and unload models into memory.
  - List available downloaded models.

2. **API Endpoints**:
  - `/download_model`: Download a specific model.
  - `/load_model`: Load a model into memory.
  - `/models`: List all downloaded models.
  - `/completion`: Generate text completions or chat responses using the loaded model.

3. **GPU Acceleration**:
  - Supports NVIDIA GPUs for accelerated inference using `llama-cpp-python` with CUDA support.
  - Compatible with systems that have NVIDIA GPUs and the NVIDIA Container Toolkit installed.

4. **Docker Support**:
  - Run the application inside a Docker container.
  - Mount the `/models` directory from the host to persist models outside the container.
  - Publish the Docker image to Docker Hub for easy deployment on any VM.

5. **Custom Prompt Templates**:
  - Supports special prompt formatting required by instruct and chat models.
  - Easily adjust prompt templates to match the model's expected input format.

# Setup

### Setting Up the `.env` File

Create a `.env` file in the project root directory and add your Hugging Face API token:

```dotenv
HUGGINGFACE_HUB_TOKEN=your_huggingface_api_token_here
```

### Local Run Python

Configure a Python virtual environment

```bash
cd /path/to/your/project
python3 -m venv venv-ai
source venv-ai/bin/activate
```

Start web server

```bash
python server.py --port 8000
```

Use API calls to download and to run a model. Currently, I use this
one https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF

Download the model

```bash
curl -X POST "http://localhost:8000/download_model" \
     -H "Content-Type: application/json" \
     -d '{
           "repo_id": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
           "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
           "model_name": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
         }'
```

Show list of downloaded models

```bash
curl -X GET "http://localhost:8000/models"
```

Load the model to memory

```bash
curl -X POST "http://localhost:8000/load_model" \
     -H "Content-Type: application/json" \
     -d '{
           "model_name": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
         }'
```

Talk to a model (currently loaded)

```bash
curl -X POST "http://localhost:8000/completion" \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "Hi, how are you?",
           "max_tokens": 1024
         }'
```

### Local Run using Docker

Build the Docker image

```bash
docker run --gpus all -d \
  -p 8000:8000 \
  -v /path/to/your/models:/models \
  --name awesome-llm-server \
  your_dockerhub_username/awesome-llm-server:latest
```

To publish an image to Docker Hub, run the following commands:

```bash
docker login
docker push your_dockerhub_username/awesome-llm-server:latest
```