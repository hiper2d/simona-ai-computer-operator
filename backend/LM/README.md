# Intro

1. Web Service (app.py):

- Loads the model with optional Apple Metal support.
- Checks for GPU availability on Linux (NVIDIA GPUs).
- Provides an API endpoint for completions. 

2. Jupyter Notebook (Control.ipynb):

- Downloads the model.
- Starts the web server with or without Apple Metal support.
- Allows interaction with the model via the API.
- Provides steps to stop the web server.

3. Dockerfile:

- Builds an image with both the web server and Jupyter server.
- Supports GPU acceleration on Linux systems with NVIDIA GPUs.

4. Running the Web Service:

- Locally on macOS: With Apple Metal support.
- In a Docker Container: On a Linux virtual machine with GPU support or CPU-only.

# Setup

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

Use API calls to download and to run a model. Currently, I use this one https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF

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