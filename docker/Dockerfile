# docker/Dockerfile
# Base image — Python 3.11 slim (smaller size, faster build)
FROM python:3.11-slim

# Install system dependencies
# libpq-dev        — PostgreSQL driver
# libgl1           — OpenCV (renamed from libgl1-mesa-glx in newer Debian)
# libglib2.0-0     — OpenCV
# build-essential  — C++ compiler required by insightface (not available on Windows)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy requirements first — Docker caches this layer
# If requirements don't change, Docker skips reinstalling packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Start the API server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]