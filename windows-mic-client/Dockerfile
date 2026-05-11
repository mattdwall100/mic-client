FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y --no-install-recommends libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .


CMD ["python", "-m", "windows_mic_client.main"]
