# Use an appropriate base image
FROM python:3.10-slim

# Install necessary system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    cmake \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install llama.cpp
RUN git clone https://github.com/ggerganov/llama.cpp.git /opt/llama.cpp
WORKDIR /opt/llama.cpp
# Build with GPU support if CUDA is available
RUN if [ -d "/usr/local/cuda" ]; then \
        LLAMA_CUBLAS=1 make; \
    else \
        make; \
    fi

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY server.py /app/app.py

# Expose ports
EXPOSE 8000 8888

# Set the working directory
WORKDIR /app

# Start Jupyter Notebook server on container start
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
