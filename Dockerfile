# --- Stage 1: Build Stage ---
FROM python:3.9-slim AS builder

WORKDIR /build

# Install compiler tools needed to build certain Python packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    gcc \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .
# Install dependencies into a local folder (wheels)
RUN pip install --no-cache-dir -r requirements.txt --target=/build/deps

# --- Stage 2: Final Runtime Stage ---
FROM python:3.9-slim

WORKDIR /app

# ✅ Only here
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Copy only the installed Python packages from the builder stage
COPY --from=builder /build/deps /app/deps
# Copy your application files
COPY app.py .
COPY global-bundle.pem .
# Ensure your index.html is copied if your app.py references it externally
# COPY index.html .

# Ensure Python can find installed libraries
ENV PYTHONPATH=/app/deps

EXPOSE 80

CMD ["python", "app.py"]
