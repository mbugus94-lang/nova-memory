# Multi-stage build for Nova Memory
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS production

WORKDIR /app

RUN groupadd -r nova && useradd -r -g nova nova

COPY --from=builder /root/.local /home/nova/.local
COPY --chown=nova:nova . .

ENV PATH=/home/nova/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

USER nova

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["sh", "-c", "uvicorn api.server:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --workers ${API_WORKERS:-1}"]
