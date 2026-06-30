import json
import logging
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
from iomt_fl_consensus.runner.experiment import setup_logging

logger = logging.getLogger(__name__)


def _load_config():
    return {
        "name": os.environ.get("CONFIG_NAME", "fog_service"),
        "log_level": os.environ.get("CONFIG_LOG_LEVEL", "INFO"),
        "log_format": os.environ.get("CONFIG_LOG_FORMAT", "text"),
        "log_file": os.environ.get("CONFIG_LOG_FILE"),
    }


def _build_consensus():
    name = os.environ.get("CONFIG_CONSENSUS", "threshold")
    logger.info("Building consensus: %s", name)
    if name == "threshold":
        max_deviation = float(os.environ.get("CONFIG_MAX_DEVIATION", "0.6"))
        logger.info("ThresholdConsensus: max_deviation=%s", max_deviation)
        return ThresholdConsensus(max_deviation=max_deviation)
    elif name == "hotstuff":
        f = int(os.environ.get("CONFIG_HOTSTUFF_F", "1"))
        leader = os.environ.get("CONFIG_HOTSTUFF_LEADER", "random")
        phases = os.environ.get("CONFIG_HOTSTUFF_PHASES", "single")
        logger.info("HotStuffConsensus: f=%s, leader=%s, phases=%s", f, leader, phases)
        return HotStuffConsensus(
            f=f,
            leader_selection=leader,
            phases=phases,
        )
    else:
        min_agreement = float(os.environ.get("CONFIG_MIN_AGREEMENT", "0.5"))
        logger.info("VotingConsensus: min_agreement=%s", min_agreement)
        return VotingConsensus(min_agreement=min_agreement)


cfg = _load_config()
setup_logging(cfg)
consensus = _build_consensus()


class FogHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/validate":
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            updates_raw = body.get("updates", [])
            round_num = body.get("round_num", 1)
            updates = [ModelUpdate(**u) for u in updates_raw]
            logger.info(
                "Validation request: round=%s, updates=%s",
                round_num, len(updates),
                extra={"round": round_num, "method": "validate"},
            )
            valid = consensus.validate_updates(updates, round_num=round_num)
            logger.info(
                "Validation result: %s/%s updates accepted",
                len(valid), len(updates),
                extra={"round": round_num, "method": "validate", "accepted": len(valid), "total": len(updates)},
            )
            self._send_json({"valid": [u.to_dict() for u in valid]})
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


port = int(os.environ.get("FOG_PORT", "8001"))
logger.info("Fog service starting on port %s (consensus=%s)", port, consensus.__class__.__name__)
HTTPServer(("0.0.0.0", port), FogHandler).serve_forever()
