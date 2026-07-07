import json
import socket
import threading
import time
from talos.embodiment.socket_embodiment import SocketEmbodiment

MANIFEST_LINE = (
    json.dumps(
        {
            "type": "manifest",
            "entity_id": "creature-0",
            "kind": "sim",
            "world_frame": "3d",
            "clock": "realtime",
            "sensors": [
                {
                    "name": "odom",
                    "dtype": "float32",
                    "shape": [6],
                    "units": "m,m/s,rad,rad/s",
                    "frame": "world",
                    "rate_hz": 20,
                    "tier": "core",
                }
            ],
            "actuators": [
                {
                    "name": "cmd_vel",
                    "dtype": "float32",
                    "shape": [2],
                    "low": [0.0, -1.5],
                    "high": [2.0, 1.5],
                    "units": "m/s,rad/s",
                    "frame": "body",
                    "tier": "core",
                }
            ],
        }
    )
    + "\n"
)


class FakeSim:
    """Minimal Unity stand-in: sends manifest + one obs, records received cmds."""

    def __init__(self):
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(1)
        self.port = self.srv.getsockname()[1]
        self.received: list[dict] = []
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self):
        conn, _ = self.srv.accept()
        conn.sendall(MANIFEST_LINE.encode())
        conn.sendall(
            (
                json.dumps(
                    {
                        "type": "obs",
                        "entity_id": "creature-0",
                        "sim_time": 1.0,
                        "odom": [0, 0, 0, 0.5, 0.2, 0.0],
                    }
                )
                + "\n"
            ).encode()
        )
        buf = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if line.strip():
                    self.received.append(json.loads(line))


def test_describe_and_read():
    sim = FakeSim()
    emb = SocketEmbodiment("127.0.0.1", sim.port)
    emb.connect()
    try:
        spec = emb.describe()
        assert spec.entity_id == "creature-0"
        assert spec.actuator("cmd_vel").space.shape == (2,)
        deadline = time.time() + 2.0
        while emb.read().sim_time == 0.0 and time.time() < deadline:
            time.sleep(0.01)
        res = emb.read()
        assert res.sim_time == 1.0
        assert res.obs["odom"][3] == 0.5
        assert "entity_id" not in res.obs
    finally:
        emb.close()
        sim.srv.close()


def test_command_validates_then_sends():
    sim = FakeSim()
    emb = SocketEmbodiment("127.0.0.1", sim.port)
    emb.connect()
    try:
        emb.command({"cmd_vel": [1.0, 0.3]})
        deadline = time.time() + 2.0
        while not sim.received and time.time() < deadline:
            time.sleep(0.01)
        assert sim.received[0] == {
            "type": "cmd",
            "entity_id": "creature-0",
            "cmd_vel": [1.0, 0.3],
        }
        try:
            emb.command({"cmd_vel": [9.0, 0.0]})
            assert False, "expected ValueError"
        except ValueError:
            pass
    finally:
        emb.close()
        sim.srv.close()


def test_obs_line_split_across_packets():
    """A JSON obs message split across two TCP sends must still parse as one line."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    obs_line = json.dumps(
        {
            "type": "obs",
            "entity_id": "creature-0",
            "sim_time": 1.0,
            "odom": [0, 0, 0, 0.5, 0.2, 0.0],
        }
    )

    def _serve():
        conn, _ = srv.accept()
        conn.sendall(MANIFEST_LINE.encode())
        split = len(obs_line) // 2
        conn.sendall(obs_line[:split].encode())
        time.sleep(0.05)
        conn.sendall((obs_line[split:] + "\n").encode())
        while conn.recv(4096):
            pass
        conn.close()

    threading.Thread(target=_serve, daemon=True).start()

    emb = SocketEmbodiment("127.0.0.1", port)
    emb.connect()
    try:
        deadline = time.time() + 2.0
        while emb.read().sim_time == 0.0 and time.time() < deadline:
            time.sleep(0.01)
        assert emb.read().sim_time == 1.0
    finally:
        emb.close()
        srv.close()
