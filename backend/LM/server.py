import os
import sys
import argparse
import platform
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define request and response models
class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 128

class CompletionResponse(BaseModel):
    completion: str

class DownloadModelRequest(BaseModel):
    repo_id: str
    filename: str
    model_name: str  # Name to save the model locally
    revision: str = None  # Optional

class ModelListResponse(BaseModel):
    models: List[str]

class LoadModelRequest(BaseModel):
    model_name: str

app = FastAPI()

def is_metal_supported():
    return platform.system() == "Darwin"

def is_nvidia_gpu_available():
    return os.path.exists('/dev/nvidia0')

def parse_args():
    parser = argparse.ArgumentParser(description="LLaMA Web Service")
    parser.add_argument('--use-metal', action='store_true', help='Use Apple Metal acceleration (macOS only)')
    parser.add_argument('--port', type=int, default=8000, help='Port for the web server')
    args = parser.parse_args()
    return args

# Parse command-line arguments
args = parse_args()

USE_METAL = args.use_metal
PORT = args.port

# Determine hardware acceleration
n_gpu_layers = 0
n_threads = 8  # Adjust based on your CPU cores

if USE_METAL and is_metal_supported():
    print("Using Apple Metal for GPU acceleration.")
    n_gpu_layers = 50  # Adjust based on your GPU memory
elif is_nvidia_gpu_available():
    print("NVIDIA GPU detected. Using GPU acceleration.")
    n_gpu_layers = 50  # Adjust based on GPU memory
else:
    print("No GPU detected or Metal support not enabled. Using CPU.")

# Initialize the model
llm = None  # Will be set after model is loaded

# Directory to store models
MODEL_DIR = "./models"

# Ensure the model directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

# Function to download a model
def download_model(repo_id, filename, model_name, revision=None, token=None):
    local_model_path = os.path.join(MODEL_DIR, model_name)
    os.makedirs(local_model_path, exist_ok=True)
    # Download the specific file
    file_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=local_model_path,
        local_dir_use_symlinks=False,
        revision=revision,
        token=token,
    )
    return file_path

# Endpoint to download a model
@app.post("/download_model")
def api_download_model(request: DownloadModelRequest):
    hf_token = os.getenv('HUGGINGFACE_HUB_TOKEN')
    if hf_token is None:
        raise HTTPException(status_code=500, detail="Hugging Face token not set.")

    try:
        file_path = download_model(
            repo_id=request.repo_id,
            filename=request.filename,
            model_name=request.model_name,
            revision=request.revision,
            token=hf_token,
        )
        return {"message": f"Model downloaded to {file_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to list available models
@app.get("/models", response_model=ModelListResponse)
def list_models():
    models = [name for name in os.listdir(MODEL_DIR) if os.path.isdir(os.path.join(MODEL_DIR, name))]
    return ModelListResponse(models=models)

# Endpoint to load a model
@app.post("/load_model")
def load_model(request: LoadModelRequest):
    global llm
    model_path = os.path.join(MODEL_DIR, request.model_name)
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model not found.")

    # Find the model file (assumes only one model file per directory)
    files = [f for f in os.listdir(model_path) if f.endswith(('.gguf', '.ggml', '.bin'))]
    if not files:
        raise HTTPException(status_code=404, detail="No model file found in the specified directory.")
    model_file = os.path.join(model_path, files[0])

    try:
        # Unload the previous model if it exists
        if llm is not None:
            print("Unloading the previous model...")
            del llm
            llm = None

        print(f"Loading the model from {model_file}...")
        llm = Llama(
            model_path=model_file,
            n_gpu_layers=n_gpu_layers,
            n_threads=n_threads,
            use_mlock=True,
        )
        print("Model loaded.")
        return {"message": f"Model {request.model_name} loaded successfully."}
    except Exception as e:
        # Ensure llm is set to None if an error occurs
        llm = None
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to generate completion
@app.post("/completion", response_model=CompletionResponse)
def generate_completion(request: CompletionRequest):
    global llm
    if llm is None:
        raise HTTPException(status_code=500, detail="Model is not loaded. Please load a model first.")

    output = llm(
        request.prompt,
        max_tokens=request.max_tokens,
        stop=["</s>"],
        echo=False,
    )
    return CompletionResponse(completion=output['choices'][0]['text'])

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
