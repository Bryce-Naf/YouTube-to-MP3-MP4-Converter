FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/instance \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser converter ./converter
COPY --chown=appuser:appuser wsgi.py .

USER appuser
EXPOSE 8080

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} wsgi:app"]
