FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

COPY ["pyproject.toml", "requirements.txt", "/app/"]

RUN ["pip", "install", "--no-cache-dir", "--upgrade", "pip"]
RUN ["pip", "install", "--no-cache-dir", "-r", "/app/requirements.txt"]

COPY ["core", "/app/core"]
COPY ["api", "/app/api"]

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
