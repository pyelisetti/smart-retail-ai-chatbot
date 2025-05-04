# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and source
COPY requirements.txt .
COPY main.py .
COPY product_ratings.csv .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8003

# Command to run the rating API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"] 