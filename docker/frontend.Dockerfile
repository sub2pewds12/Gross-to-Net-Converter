FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
# Add /app to Python's import path
ENV PYTHONPATH=/app

WORKDIR /app

COPY ["pyproject.toml", "requirements.txt", "/app/"]

RUN ["pip", "install", "--no-cache-dir", "--upgrade", "pip"]
RUN ["pip", "install", "--no-cache-dir", "-r", "/app/requirements.txt"]

COPY ["core", "/app/core"]
COPY ["frontend", "/app/frontend"]

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
