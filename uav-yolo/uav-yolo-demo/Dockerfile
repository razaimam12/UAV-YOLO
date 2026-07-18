# Slim, reproducible image for the UAV detection API.
FROM python:3.11-slim

# System libs required by OpenCV / Ultralytics
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/

# Run as non-root user (good practice; keeps parity with hardened deployments)
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Warm the model weights at build-friendly runtime, then serve
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
