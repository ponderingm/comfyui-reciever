# Multi-arch Python base (supports arm/v7 and arm64)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

# Create non-root user
RUN useradd -ms /bin/bash appuser && mkdir -p /data && chown -R appuser:appuser /data /app
USER appuser

ENV SAVE_DIR=/data

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
