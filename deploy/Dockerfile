# QR Quishing Demo Kit — single image running all five demos on ports 10000-10005.
# Build from the repo root:
#   docker build -f deploy/Dockerfile -t qr-quishing-demos .
# Or just use deploy/docker-compose.yml.

FROM python:3.11-slim

# No byte-code files, unbuffered logs (so `docker logs` is live).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps first for layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole kit.
COPY . .

# Demos: 10000 hub, 10001-10005 = A..E
EXPOSE 10000 10001 10002 10003 10004 10005

# QR assets + PDF are regenerated from env at startup by serve.py.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; \
        urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PORT_HUB','10000')).read()" \
        || exit 1

CMD ["python", "deploy/serve.py"]
