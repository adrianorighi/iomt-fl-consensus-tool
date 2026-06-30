import json
import logging
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from iomt_fl_consensus.core import IoHTClient, ResourceProfile
from iomt_fl_consensus.data import DataRepository
from iomt_fl_consensus.runner.experiment import setup_logging

logger = logging.getLogger(__name__)


def _load_config():
    return {
        "seed": int(os.environ.get("CONFIG_SEED", "42")),
        "num_clients": int(os.environ.get("CONFIG_NUM_CLIENTS", "10")),
        "samples_per_client": int(os.environ.get("CONFIG_SAMPLES_PER_CLIENT", "120")),
        "failure_rate": float(os.environ.get("CONFIG_FAILURE_RATE", "0.0")),
        "noise": float(os.environ.get("CONFIG_NOISE", "0.05")),
        "non_iid": os.environ.get("CONFIG_NON_IID", "false").lower() in ("1", "true"),
        "log_level": os.environ.get("CONFIG_LOG_LEVEL", "INFO"),
        "log_format": os.environ.get("CONFIG_LOG_FORMAT", "text"),
        "log_file": os.environ.get("CONFIG_LOG_FILE"),
    }


cfg = _load_config()
setup_logging(cfg)
logger.info("Edge service starting: config=%s", cfg["name"] if "name" in cfg else "default")

repo = DataRepository(seed=cfg["seed"])
clients_data = repo.generate_synthetic_data(
    cfg["num_clients"], cfg["samples_per_client"], non_iid=cfg["non_iid"]
)

clients = []
for i, data in enumerate(clients_data):
    profile = ResourceProfile(cpu_limit=1.0, memory_limit=256.0, battery_level=100.0)
    clients.append(
        IoHTClient(
            f"client_{i+1}",
            data,
            profile,
            failure_rate=cfg["failure_rate"],
            noise=cfg["noise"],
        )
    )

clients_map = {c.client_id: c for c in clients}
logger.info(
    "Edge service started: %d clients, failure_rate=%s, noise=%s",
    len(clients), cfg["failure_rate"], cfg["noise"],
)


class EdgeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/train":
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            global_model = body["global_model"]
            client_ids = body.get("client_ids", list(clients_map.keys()))
            logger.info(
                "Training request: clients_requested=%d",
                len(client_ids),
            )
            updates = []
            for cid in client_ids:
                client = clients_map.get(cid)
                if client is None:
                    logger.warning("Client '%s' not found", cid)
                    continue
                client.receive_global_model(global_model)
                update = client.train_local_model()
                if update is not None:
                    updates.append(update.to_dict())
                else:
                    logger.warning("Client '%s' training failed (simulated failure)", cid)
            logger.info(
                "Training response: updates_returned=%d/%d",
                len(updates), len(client_ids),
            )
            self._send_json({"updates": updates})
        else:
            logger.warning("Unknown path: %s", self.path)
            self.send_response(404)
            self.end_headers()

    def _send_json(self, data):
        payload = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        logger.debug("HTTP: %s", fmt % args)


port = int(os.environ.get("EDGE_PORT", "8000"))
HTTPServer(("0.0.0.0", port), EdgeHandler).serve_forever()
