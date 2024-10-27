# Use the official Python image as base
FROM python:3.9-slim-buster

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    ca-certificates \
    libopenblas-dev \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install CUDA libraries (CUDA 11.8 in this example)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libcudnn8=8.6.0.163-1+cuda11.8 \
    libcudnn8-dev=8.6.0.163-1+cuda11.8 && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for CUDA
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Create a working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI app
COPY server.py .
COPY .env .env

# Expose the port
EXPOSE 8000

# Set the entrypoint to run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
