FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

# Install pg_isready (PostgreSQL client tools)
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy lock/dependency files from the repository root into /app
COPY pyproject.toml requirements.txt /app/

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy the project source folders
COPY core /app/core
COPY api /app/api

EXPOSE 8000

# Ensure the wait_for_db script is executable (assumes it is in the api folder)
RUN chmod +x /app/api/wait_for_db.py

# Use the wait_for_db script to delay startup until the DB is ready,
# then launch uvicorn to run the FastAPI application.
CMD ["python3", "/app/api/wait_for_db.py", "db", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
