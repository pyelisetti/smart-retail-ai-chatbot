FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for OpenBLAS and protobuf
ENV OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 \
    OPENBLAS_MAIN_FREE=1

# Set all possible cache locations to our custom directory
ENV HF_HOME=/app/huggingface_cache \
    TRANSFORMERS_CACHE=/app/huggingface_cache \
    HUGGINGFACE_HUB_CACHE=/app/huggingface_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/huggingface_cache \
    XDG_CACHE_HOME=/app/huggingface_cache \
    HF_DATASETS_CACHE=/app/huggingface_cache \
    HF_METRICS_CACHE=/app/huggingface_cache \
    HF_MODULES_CACHE=/app/huggingface_cache \
    HF_TOKEN_CACHE=/app/huggingface_cache

# Create cache directory with proper permissions
RUN mkdir -p /app/huggingface_cache && \
    chmod -R 777 /app/huggingface_cache

# Install Python dependencies
COPY requirements.txt .

# Install dependencies with specific versions
RUN pip install --no-cache-dir \
    protobuf==3.20.3 \
    sentencepiece==0.1.99 \
    transformers==4.36.0 \
    torch==2.1.0 \
    numpy==1.24.0 \
    fastapi==0.104.0 \
    uvicorn==0.24.0 \
    pydantic==2.4.2 \
    httpx==0.25.0 \
    python-dotenv==1.0.0 \
    accelerate==0.27.2 \
    bitsandbytes==0.42.0 \
    huggingface-hub==0.19.3 \
    sentence-transformers==2.2.2 \
    faiss-cpu==1.7.4 \
    einops==0.7.0

# Copy application code
COPY . .

# Set proper permissions
RUN chown -R 1000:1000 /app

# Switch to non-root user
USER 1000

# Expose port
EXPOSE 8002

# Start the application
CMD ["python", "llm_server.py"] 