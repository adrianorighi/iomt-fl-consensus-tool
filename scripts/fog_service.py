import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from iomt_fl_consensus.consensus import (
    ThresholdConsensus,
    VotingConsensus,
    HotStuffConsensus,
)
from iomt_fl_consensus.core.models import ModelUpdate


def _build_consensus():
    name = os.environ.get("CONFIG_CONSENSUS", "threshold")
    if name == "threshold":
        return ThresholdConsensus(
            max_deviation=float(os.environ.get("CONFIG_MAX_DEVIATION", "0.6"))
        )
    elif name == "hotstuff":
        return HotStuffConsensus(
            f=int(os.environ.get("CONFIG_HOTSTUFF_F", "1")),
            leader_selection=os.environ.get("CONFIG_HOTSTUFF_LEADER", "random"),
            phases=os.environ.get("CONFIG_HOTSTUFF_PHASES", "single"),
        )
    else:
        return VotingConsensus(
            min_agreement=float(os.environ.get("CONFIG_MIN_AGREEMENT", "0.5"))
        )


consensus = _build_consensus()


class FogHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/validate":
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            updates_raw = body.get("updates", [])
            round_num = body.get("round_num", 1)
            updates = [ModelUpdate(**u) for u in updates_raw]
            valid = consensus.validate_updates(updates, round_num=round_num)
            self._send_json({"valid": [u.to_dict() for u in valid]})
        else:
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
        pass


port = int(os.environ.get("FOG_PORT", "8001"))
HTTPServer(("0.0.0.0", port), FogHandler).serve_forever()
