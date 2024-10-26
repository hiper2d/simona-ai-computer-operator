import os
import sys
import argparse
import platform

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from llama_cpp import Llama


# Load environment variables from .env file
load_dotenv()


# Define request and response models
class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 128


class CompletionResponse(BaseModel):
    completion: str


app = FastAPI()


def is_metal_supported():
    return platform.system() == "Darwin"


def is_nvidia_gpu_available():
    return os.path.exists('/dev/nvidia0')


def parse_args():
    parser = argparse.ArgumentParser(description="LLaMA Web Service")
    parser.add_argument('--model-path', type=str, default="/models/model.gguf", help='Path to the model file')
    parser.add_argument('--use-metal', action='store_true', help='Use Apple Metal acceleration (macOS only)')
    parser.add_argument('--port', type=int, default=8000, help='Port for the web server')
    args = parser.parse_args()
    return args


# Parse command-line arguments
args = parse_args()

MODEL_PATH = args.model_path
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
print("Loading the model...")
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=n_gpu_layers,
    n_threads=n_threads,
    use_mlock=True,
)
print("Model loaded.")


@app.post("/completion", response_model=CompletionResponse)
def generate_completion(request: CompletionRequest):
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
