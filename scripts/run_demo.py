import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from iomt_fl_consensus.runner import ExperimentRunner

TYPE_MAP = {
    "name": str, "seed": int, "num_clients": int, "samples_per_client": int,
    "rounds": int, "client_fraction": float, "aggregator": str, "consensus": str,
    "max_deviation": float, "failure_rate": float, "noise": float,
    "non_iid": bool, "min_agreement": float, "multi_krum_f": int,
    "multi_krum_m": int, "hotstuff_f": int, "hotstuff_leader": str,
    "hotstuff_phases": str, "log_level": str, "log_file": str, "log_format": str,
}


def _parse_bool(v: str) -> bool:
    return v.lower() in ("1", "true", "yes")


def _cast(value: str, typ: type):
    if typ is bool:
        return _parse_bool(value)
    return typ(value)


def _config_from_env() -> dict:
    cfg = {}
    prefix = "CONFIG_"
    for key, typ in TYPE_MAP.items():
        env_key = prefix + key.upper()
        val = os.environ.get(env_key)
        if val is not None:
            cfg[key] = _cast(val, typ)
    return cfg


parser = argparse.ArgumentParser()
parser.add_argument("--config", default=None)
args = parser.parse_args()

if args.config:
    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)
else:
    config = _config_from_env()
    if not config:
        parser.error("provide --config <file> or set CONFIG_* environment variables")

runner = ExperimentRunner(config)
rows = runner.run()
prefix = config.get("name", "experiment")
csv_path, json_path = runner.export(rows, prefix)
print(f"Experimento concluído: {prefix}")
print(f"CSV: {csv_path}")
print(f"JSON: {json_path}")
print(f"Última rodada: {rows[-1]}")
