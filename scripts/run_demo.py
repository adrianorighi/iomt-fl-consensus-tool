import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from iotht_fl.runner import ExperimentRunner

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
args = parser.parse_args()

with open(args.config, "r", encoding="utf-8") as f:
    config = json.load(f)

runner = ExperimentRunner(config)
rows = runner.run()
prefix = config.get("name", "experiment")
csv_path, json_path = runner.export(rows, prefix)
print(f"Experimento concluído: {prefix}")
print(f"CSV: {csv_path}")
print(f"JSON: {json_path}")
print(f"Última rodada: {rows[-1]}")
