from __future__ import annotations
import json
import socket
import threading
from typing import Any, Optional
from talos.embodiment.spec import EntitySpec, StepResult, validate_command


class SocketEmbodiment:
    """Realtime Embodiment over a newline-delimited JSON TCP socket (see doc 04 §6)."""

    def __init__(self, host: str, port: int, connect_timeout: float = 5.0) -> None:
        self._host, self._port = host, port
        self._timeout = connect_timeout
        self._sock: Optional[socket.socket] = None
        self._spec: Optional[EntitySpec] = None
        self._latest = StepResult(obs={}, sim_time=0.0)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._rf: Any = None

    def connect(self) -> None:
        self._sock = socket.create_connection((self._host, self._port), self._timeout)
        self._rf = self._sock.makefile("r", encoding="utf-8")
        manifest = json.loads(self._rf.readline())
        if manifest.get("type") != "manifest":
            raise ValueError("first line must be the manifest")
        self._spec = EntitySpec.from_manifest(manifest)
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        try:
            for line in self._rf:  # blocks per line; ends when socket closes
                if self._stop.is_set():
                    break
                line = line.strip()
                if not line:
                    continue
                msg = json.loads(line)
                if msg.get("type") == "obs" and self._spec is not None:
                    obs = {
                        s.name: msg[s.name] for s in self._spec.sensors if s.name in msg
                    }
                    with self._lock:
                        self._latest = StepResult(
                            obs=obs, sim_time=float(msg["sim_time"])
                        )
        except (OSError, ValueError):
            pass  # socket closed / torn-down mid-read during close()

    def describe(self) -> EntitySpec:
        if self._spec is None:
            raise RuntimeError("call connect() first")
        return self._spec

    def read(self) -> StepResult:
        with self._lock:
            return self._latest

    def command(self, cmd: dict[str, Any]) -> None:
        if self._spec is None or self._sock is None:
            raise RuntimeError("call connect() first")
        validate_command(self._spec, cmd)
        payload = {"type": "cmd", "entity_id": self._spec.entity_id, **cmd}
        self._sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))

    def close(self) -> None:
        self._stop.set()
        if self._sock is not None:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._sock.close()
