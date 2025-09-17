# ---------- Stage 1: Build ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements and install into a temp directory
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir "numpy<2" && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# ---------- Stage 2: Final Slim Image ----------
FROM python:3.11-slim

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --from=builder /app /app

# Expose Flask port
EXPOSE 5000

# Run Gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
