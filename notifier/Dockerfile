FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY notifier notifier
RUN useradd --system --uid 10001 --create-home appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

USER appuser
ENV ALERT_CONFIG_FILE=/data/notifier_data.sqlite3 \
    HTTP_HOST=0.0.0.0 \
    HTTP_PORT=8082

EXPOSE 8082
CMD ["gunicorn", "--bind", "0.0.0.0:8082", "--workers", "1", "--threads", "8", "notifier.app:http_app"]
