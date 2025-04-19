# Stage 1: Build the Vite frontend
FROM node:20-slim AS build-stage

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --omit=dev  # More deterministic installs than npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the Python backend
FROM python:3.12-slim AS production-stage

WORKDIR /app

# Install system dependencies (often needed for Python packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for better layer caching
COPY backend/requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend code
COPY backend/ /app/

# Copy built frontend from build stage
COPY --from=build-stage /frontend/dist /app/static

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV RUNNING_IN_PRODUCTION=true

# Create non-root user and switch to it
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE $PORT

# Health check and graceful timeout for Azure
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT", \
     "--worker-class", "aiohttp.GunicornWebWorker", \
     "--workers", "4", "--timeout", "120", "--keep-alive", "5"]