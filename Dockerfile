# BentoML service image. Build after `python -m hotelprice.export_artifacts` (see README).
FROM python:3.12-slim

# Dependencies first so code or artifact changes do not invalidate this layer.
WORKDIR /app
COPY requirements-serving.txt .
RUN pip install --no-cache-dir -r requirements-serving.txt

# Non-root user (BentoML writes to its home directory at startup).
RUN useradd --create-home --uid 1000 app

# Service code, the config it imports, and the exported champion snapshot.
COPY src/hotelprice/__init__.py src/hotelprice/config.py src/hotelprice/service.py hotelprice/
COPY serving_artifacts/ serving_artifacts/

ENV MODEL_ARTIFACT_DIR=/app/serving_artifacts \
    PYTHONUNBUFFERED=1
USER app
EXPOSE 3000

# python is used for the check because the slim image has no curl.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/livez', timeout=3)"

CMD ["bentoml", "serve", "hotelprice.service:HotelPriceService", "--port", "3000"]
