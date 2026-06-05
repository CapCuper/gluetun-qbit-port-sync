#!/usr/bin/env python3
"""
gluetun-qbit-port-sync
Watches gluetun's forwarded_port.txt and updates qBittorrent's listening port automatically.
"""

import os
import time
import logging
import requests
from pathlib import Path

# ── Config from environment variables ────────────────────────────────────────
PORT_FILE        = os.getenv("PORT_FILE",        "/gluetun/forwarded_port.txt")
QBIT_HOST        = os.getenv("QBIT_HOST",        "http://localhost:8080")
QBIT_USER        = os.getenv("QBIT_USER",        "admin")
QBIT_PASS        = os.getenv("QBIT_PASS",        "adminadmin")
CHECK_INTERVAL   = int(os.getenv("CHECK_INTERVAL", "30"))   # seconds
LOG_LEVEL        = os.getenv("LOG_LEVEL",        "INFO")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def read_port(path: str) -> int | None:
    """Read the forwarded port from gluetun's status file."""
    try:
        text = Path(path).read_text().strip()
        port = int(text)
        if 1 <= port <= 65535:
            return port
        log.warning("Port value out of range: %s", port)
    except FileNotFoundError:
        log.debug("Port file not found yet: %s", path)
    except ValueError:
        log.warning("Could not parse port from file content: %r", text)
    return None


class QBittorrentClient:
    def __init__(self, host: str, username: str, password: str):
        self.host     = host.rstrip("/")
        self.username = username
        self.password = password
        self.session  = requests.Session()
        # qBittorrent 5.x requires these headers to pass CSRF protection
        self.session.headers.update({
            "Referer": self.host,
            "Origin":  self.host,
        })

    def login(self) -> bool:
        try:
            r = self.session.post(
                f"{self.host}/api/v2/auth/login",
                data={"username": self.username, "password": self.password},
                timeout=10,
            )
            response_text = r.text.strip()
            if response_text == "Ok.":
                log.debug("Logged in to qBittorrent.")
                return True
            # "Fails." means wrong credentials; anything else is likely CSRF/network
            if response_text == "Fails.":
                log.error("qBittorrent login failed: wrong username or password.")
            else:
                log.error("qBittorrent login failed (status %s): %r", r.status_code, response_text)
        except requests.RequestException as e:
            log.error("Could not reach qBittorrent: %s", e)
        return False

    def get_listen_port(self) -> int | None:
        try:
            r = self.session.get(
                f"{self.host}/api/v2/app/preferences", timeout=10
            )
            return r.json().get("listen_port")
        except Exception as e:
            log.error("Failed to get qBittorrent preferences: %s", e)
        return None

    def set_listen_port(self, port: int) -> bool:
        try:
            r = self.session.post(
                f"{self.host}/api/v2/app/setPreferences",
                data={"json": f'{{"listen_port":{port}}}'},
                timeout=10,
            )
            return r.status_code == 200
        except Exception as e:
            log.error("Failed to set qBittorrent port: %s", e)
        return False


def main():
    log.info("=== gluetun-qbit-port-sync starting ===")
    log.info("Port file    : %s", PORT_FILE)
    log.info("qBittorrent  : %s", QBIT_HOST)
    log.info("Check interval: %ds", CHECK_INTERVAL)

    client      = QBittorrentClient(QBIT_HOST, QBIT_USER, QBIT_PASS)
    last_port   = None

    while True:
        new_port = read_port(PORT_FILE)

        if new_port is None:
            log.debug("No valid port yet, retrying in %ds…", CHECK_INTERVAL)
            time.sleep(CHECK_INTERVAL)
            continue

        if new_port == last_port:
            log.debug("Port unchanged (%d), nothing to do.", new_port)
            time.sleep(CHECK_INTERVAL)
            continue

        log.info("Port changed: %s → %d", last_port or "?", new_port)

        if not client.login():
            log.warning("Will retry login next cycle.")
            time.sleep(CHECK_INTERVAL)
            continue

        current = client.get_listen_port()
        if current == new_port:
            log.info("qBittorrent already using port %d.", new_port)
            last_port = new_port
            time.sleep(CHECK_INTERVAL)
            continue

        if client.set_listen_port(new_port):
            log.info("✓ qBittorrent listen port updated to %d.", new_port)
            last_port = new_port
        else:
            log.error("Failed to update port in qBittorrent.")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
