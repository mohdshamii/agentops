FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pydantic pydantic-settings requests beautifulsoup4 aiohttp python-dotenv

# Copy backend code
COPY backend/ /app/backend/
COPY .env /app/.env

WORKDIR /app/backend

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
