# ------------------------------------------------------------------------------
# SignalGate Production Container
# Compatible with Hugging Face Spaces (Port 7860), Render ($PORT), Koyeb & Local Docker
# ------------------------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and prebuilt static frontend
COPY . .

# Set default port
ENV PORT=7860
EXPOSE 7860

# Launch FastAPI server
CMD ["sh", "-c", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
