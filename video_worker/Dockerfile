FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg and system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (as root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code (as root)
COPY . .

# Note: Running as root in container is acceptable for development
# For production, create a non-root user:
# RUN useradd -m -u 1000 celery && chown -R celery:celery /app
# USER celery

# Default command
CMD ["python", "worker.py"]

