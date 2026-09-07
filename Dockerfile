# Use an official lightweight Python runtime as the base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set a working directory inside the container
WORKDIR /app

# Copy dependency file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . .

# Create necessary directories
RUN mkdir -p data uploads/chat/images uploads/chat/audio uploads/chat/videos

# Expose the ports (gateway)
EXPOSE 5000

# Run the gateway service
CMD ["python", "services/gateway_service.py"]