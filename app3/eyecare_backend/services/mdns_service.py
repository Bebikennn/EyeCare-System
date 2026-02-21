"""mDNS/Zeroconf service advertisement for the EyeCare backend.

This allows the Flutter app to discover the backend automatically on the LAN
without hardcoding IP addresses.

Service type advertised: `_eyecare._tcp.local.`
"""

from __future__ import annotations

import atexit
import socket
import threading
from typing import Any

from zeroconf import ServiceInfo, Zeroconf


_SERVICE_TYPE = "_eyecare._tcp.local."

_lock = threading.Lock()
_zc: Zeroconf | None = None
_info: ServiceInfo | None = None


def _get_best_local_ipv4() -> str:
    """Best-effort local IPv4 used for outbound traffic."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def start_mdns(*, port: int, name: str = "eyecare-backend", properties: dict[str, Any] | None = None) -> None:
    """Start advertising the backend on the local network.

    Safe to call multiple times.
    """

    global _zc, _info

    with _lock:
        if _zc is not None:
            return

        ip = _get_best_local_ipv4()
        props: dict[bytes, bytes] = {}
        if properties:
            for k, v in properties.items():
                props[str(k).encode("utf-8")] = str(v).encode("utf-8")

        # Zeroconf requires a fully-qualified service instance name.
        instance_name = f"{name}.{_SERVICE_TYPE}"

        # Some platforms require a *.local. server name.
        server = f"{socket.gethostname()}.local."

        _info = ServiceInfo(
            type_=_SERVICE_TYPE,
            name=instance_name,
            addresses=[socket.inet_aton(ip)],
            port=int(port),
            properties=props,
            server=server,
        )

        _zc = Zeroconf()
        _zc.register_service(_info)

        # Ensure we clean up on exit.
        atexit.register(stop_mdns)


def stop_mdns() -> None:
    """Stop advertising."""

    global _zc, _info

    with _lock:
        if _zc is None:
            return
        try:
            if _info is not None:
                _zc.unregister_service(_info)
        finally:
            try:
                _zc.close()
            finally:
                _zc = None
                _info = None
