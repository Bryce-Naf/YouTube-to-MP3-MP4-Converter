FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/instance/media_jobs \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser converter ./converter
COPY --chown=appuser:appuser wsgi.py .

USER appuser
EXPOSE 8080

CMD ["sh", "-c", "gunicorn --timeout 1860 --bind 0.0.0.0:${PORT} wsgi:app"]
