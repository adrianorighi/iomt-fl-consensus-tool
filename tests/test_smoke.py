from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from iomt_fl_consensus.runner import ExperimentRunner

cfg = {
    "name": "test_run",
    "seed": 1,
    "num_clients": 4,
    "samples_per_client": 10,
    "rounds": 3,
    "client_fraction": 1.0,
    "aggregator": "fedavg",
    "consensus": "threshold"
}
rows = ExperimentRunner(cfg).run()
assert len(rows) == 3
assert "proxy_accuracy" in rows[0]
print("smoke test ok")
