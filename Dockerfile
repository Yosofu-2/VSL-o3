FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend files
COPY api_client.py .
COPY i18n.py .
COPY modern_gui.py .
COPY reader_gui.py .

# Create necessary directories
RUN mkdir -p /app/backend/avatars /app/backend/backups /app/data

# Set environment variables
ENV LITMAN_DB_PATH=/app/data/library.db
ENV PYTHONPATH=/app/backend

# Expose backend port
EXPOSE 8000

# Start backend
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
