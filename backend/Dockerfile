FROM python:3.12.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy application files explicitly to keep local .env files out of the image.
COPY server.py cards_seed.py restricted_access.py cards_catalog.json ./
RUN useradd --create-home appuser
USER appuser
EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--proxy-headers"]
