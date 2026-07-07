# Dockerfile for FastAPI Backend
FROM python:3.12-slim

WORKDIR /app

# Install system utilities needed for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

# On startup, verify database seeding & train models, then start uvicorn
CMD ["sh", "-c", "PYTHONPATH=. python3 backend/ml_engine.py && uvicorn backend.main:app --host 0.0.0.0 --port 8001"]