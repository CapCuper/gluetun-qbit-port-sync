FROM python:3.12-alpine

LABEL org.opencontainers.image.title="gluetun-qbit-port-sync"
LABEL org.opencontainers.image.description="Syncs gluetun forwarded port to qBittorrent automatically"
LABEL org.opencontainers.image.source="https://github.com/YOUR_USER/gluetun-qbit-port-sync"

WORKDIR /app

RUN pip install --no-cache-dir requests

COPY sync_port.py .

ENV PORT_FILE=/gluetun/forwarded_port.txt \
    QBIT_HOST=http://localhost:8080 \
    QBIT_USER=admin \
    QBIT_PASS=adminadmin \
    CHECK_INTERVAL=30 \
    LOG_LEVEL=INFO

CMD ["python", "-u", "sync_port.py"]
