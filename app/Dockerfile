# Stage 1: Build the Vite frontend
FROM node:20-slim AS build-stage

WORKDIR /frontend
COPY frontend/ ./
RUN npm install
RUN npm run build

# Stage 2: Build the Python backend
FROM python:3.12-slim AS production-stage

WORKDIR /app

# Copy backend code
COPY backend/ /app/

# ✅ Copy the built frontend files into backend's static folder
COPY --from=build-stage /frontend/dist /app/static

# Set environment flags
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
RUN python -m pip install -r requirements.txt
RUN python -m pip install gunicorn

# Run using Gunicorn with aiohttp worker
CMD ["gunicorn", "app:create_app", "-b", "0.0.0.0:8000", "--worker-class", "aiohttp.GunicornWebWorker"]
