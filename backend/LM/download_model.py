import os
import argparse
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv


def download_model(repo_id, local_dir, filename, revision=None, token=None):
    # Ensure the local directory exists
    os.makedirs(local_dir, exist_ok=True)

    # Download the specific file
    file_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=local_dir,
        local_dir_use_symlinks=False,
        revision=revision,
        token=token,
    )
    print(f"Model file downloaded to: {file_path}")


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(description="Download a specific quantized model file from Hugging Face Hub")
    parser.add_argument('--repo-id', type=str, required=True, help='Hugging Face model repository ID (e.g., TheBloke/Llama-2-7B-Chat-GGUF)')
    parser.add_argument('--local-dir', type=str, required=True, help='Local directory to save the model file')
    parser.add_argument('--filename', type=str, required=True, help='Name of the quantized model file to download (e.g., llama-2-7b-chat.Q4_K_M.gguf)')
    parser.add_argument('--revision', type=str, default=None, help='Specific model version to download')

    args = parser.parse_args()

    # Get the token from environment variables
    hf_token = os.getenv('HUGGINGFACE_HUB_TOKEN')

    if hf_token is None:
        print("Error: HUGGINGFACE_HUB_TOKEN is not set in the .env file.")
        exit(1)

    download_model(args.repo_id, args.local_dir, args.filename, revision=args.revision, token=hf_token)
