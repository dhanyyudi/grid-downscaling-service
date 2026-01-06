FROM python:3.11-slim

WORKDIR /app

# System deps for rtree (spatial indexing) + git for pip install from GitHub
RUN apt-get update && apt-get install -y \
    libspatialindex-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install geosquare-grid from GitHub
RUN pip install --no-cache-dir git+https://github.com/geosquareai/geosquare-grid.git

# Copy application code
COPY config.py .
COPY models.py .
COPY main.py .
COPY routes ./routes
COPY services ./services

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
