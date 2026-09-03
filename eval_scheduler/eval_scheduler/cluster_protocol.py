from __future__ import annotations

import json
import os
import secrets
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ClusterProtocolError(RuntimeError):
    pass


class ClusterService(Protocol):
    def handle(self, method: str, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]: ...


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.{os.getpid()}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_cluster_token(plan_dir: Path) -> str:
    path = plan_dir / "cluster.token"
    if path.exists():
        token = path.read_text().strip()
        if not token:
            raise ClusterProtocolError(f"empty cluster token: {path}")
        return token
    plan_dir.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(48)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(token + "\n")
    return token


def read_cluster_token(path: Path) -> str:
    token = path.read_text().strip()
    if not token:
        raise ClusterProtocolError(f"empty cluster token: {path}")
    return token


def make_handler(service: ClusterService, token: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "HRMEvalCoordinator/1"

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _reply(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _dispatch(self) -> None:
            if self.headers.get("Authorization") != f"Bearer {token}":
                self._reply(401, {"error": "unauthorized"})
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise TypeError("request body must be an object")
                status, response = service.handle(self.command, self.path, payload)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                self._reply(400, {"error": str(exc)})
                return
            except Exception as exc:  # noqa: BLE001 - isolate coordinator handler failures
                self._reply(500, {"error": f"{type(exc).__name__}: {exc}"})
                return
            self._reply(status, response)

        do_GET = _dispatch
        do_POST = _dispatch

    return Handler


def start_cluster_server(
    service: ClusterService,
    *,
    host: str,
    port: int,
    token: str,
) -> tuple[ThreadingHTTPServer, Thread]:
    server = ThreadingHTTPServer((host, port), make_handler(service, token))
    thread = Thread(target=server.serve_forever, name="eval-coordinator-http", daemon=True)
    thread.start()
    return server, thread


class ClusterClient:
    def __init__(self, base_url: str, token: str, *, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(payload or {}, separators=(",", ":")).encode()
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                value = json.loads(response.read())
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise ClusterProtocolError(f"coordinator returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise ClusterProtocolError(f"coordinator request failed: {exc}") from exc
        if not isinstance(value, dict):
            raise ClusterProtocolError("coordinator returned a non-object response")
        if "error" in value:
            raise ClusterProtocolError(str(value["error"]))
        return value
