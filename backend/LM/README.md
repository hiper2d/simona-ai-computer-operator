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

New Python env
```bash
cd /path/to/your/project
python3 -m venv venv-ai
source venv-ai/bin/activate
```

Download the model and start the web server
```bash
cd /backend/LM

python download_model.py \
    --repo-id mradermacher/Llama-3-11B-GGUF \
    --local-dir ./models/Llama-3-11B-GGUF \
    --filename Llama-3-11B.Q4_K_M.gguf

python server.py --use-metal \
    --model-path ./models/Llama-3-11B-GGUF/Llama-3-11B.Q4_K_M.gguf
```

Talk to a model
```bash
curl -X POST "http://localhost:8000/completion" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?", "max_tokens": 128}'
```