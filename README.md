# gluetun-qbit-port-sync

Lightweight Python service that watches [gluetun](https://github.com/qdm12/gluetun)'s forwarded port file and automatically updates [qBittorrent](https://www.qbittorrent.org/)'s listening port via its Web API.

## How it works

1. Polls `/gluetun/forwarded_port.txt` every N seconds (default: 30).
2. When the port changes, logs into qBittorrent's Web API and updates `listen_port`.
3. Logs every action so you can follow along with `docker logs`.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `PORT_FILE` | `/gluetun/forwarded_port.txt` | Path to gluetun's port file |
| `QBIT_HOST` | `http://localhost:8080` | qBittorrent Web UI URL |
| `QBIT_USER` | `admin` | qBittorrent username |
| `QBIT_PASS` | `adminadmin` | qBittorrent password |
| `CHECK_INTERVAL` | `30` | Polling interval in seconds |
| `LOG_LEVEL` | `INFO` | Python log level (DEBUG, INFO, WARNING…) |

## Usage with Docker Compose

See the full `docker-compose.yml` example in this repo.  
Key points:

- The container must share `network_mode: "container:gluetun"` so it can reach qBittorrent (which also lives inside gluetun's network namespace).
- Mount gluetun's config volume read-only so the port file is accessible.

```yaml
  port-sync:
    image: ghcr.io/YOUR_USER/gluetun-qbit-port-sync:latest
    container_name: port-sync
    network_mode: "container:gluetun"
    environment:
      - QBIT_HOST=http://localhost:8080
      - QBIT_USER=admin
      - QBIT_PASS=your_password
      - CHECK_INTERVAL=30
    volumes:
      - /volume2/docker/gluetun:/gluetun:ro
    depends_on:
      - gluetun
      - qbittorrent
    restart: always
```

## Build locally

```bash
docker build -t gluetun-qbit-port-sync .
```

## GitHub Actions – auto-publish to GHCR

The included workflow (`.github/workflows/docker-publish.yml`) builds and pushes the image to GitHub Container Registry on every push to `main`.

Replace `YOUR_USER` with your GitHub username.
