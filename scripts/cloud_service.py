import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from iomt_fl_consensus.aggregation import (
    FedAvgAggregator,
    WeightedAggregator,
    RobustAggregator,
    MultiKrumAggregator,
)
from iomt_fl_consensus.runner.experiment import setup_logging


def _http_post(url, data):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _build_aggregator(cfg):
    name = cfg["aggregator"]
    aggregators = {
        "fedavg": FedAvgAggregator(),
        "weighted": WeightedAggregator(),
        "robust": RobustAggregator(),
        "multi_krum": MultiKrumAggregator(
            f=cfg.get("multi_krum_f", 1), m=cfg.get("multi_krum_m")
        ),
    }
    return aggregators[name]


def _load_config():
    return {
        "name": os.environ.get("CONFIG_NAME", "docker_multi_layer"),
        "seed": int(os.environ.get("CONFIG_SEED", "42")),
        "num_clients": int(os.environ.get("CONFIG_NUM_CLIENTS", "10")),
        "rounds": int(os.environ.get("CONFIG_ROUNDS", "15")),
        "client_fraction": float(os.environ.get("CONFIG_CLIENT_FRACTION", "1.0")),
        "aggregator": os.environ.get("CONFIG_AGGREGATOR", "fedavg"),
        "consensus": os.environ.get("CONFIG_CONSENSUS", "threshold"),
        "failure_rate": float(os.environ.get("CONFIG_FAILURE_RATE", "0.0")),
        "noise": float(os.environ.get("CONFIG_NOISE", "0.05")),
        "non_iid": os.environ.get("CONFIG_NON_IID", "false").lower()
        in ("1", "true"),
        "max_deviation": float(os.environ.get("CONFIG_MAX_DEVIATION", "0.6")),
        "edge_url": os.environ.get("EDGE_URL", "http://localhost:8000"),
        "fog_url": os.environ.get("FOG_URL", "http://localhost:8001"),
        "log_level": os.environ.get("CONFIG_LOG_LEVEL", "INFO"),
        "log_format": os.environ.get("CONFIG_LOG_FORMAT", "text"),
        "log_file": os.environ.get("CONFIG_LOG_FILE"),
    }


def main():
    cfg = _load_config()
    setup_logging(cfg)

    edge_url = cfg["edge_url"]
    fog_url = cfg["fog_url"]
    num_clients = cfg["num_clients"]
    rounds = cfg["rounds"]
    fraction = cfg["client_fraction"]
    aggregator = _build_aggregator(cfg)
    global_model = {"w1": 0.0, "w2": 0.0, "bias": 0.0}
    rows = []

    print(f"Cloud orchestrator started: {cfg['name']}")
    print(f"Edge: {edge_url}, Fog: {fog_url}")
    print(f"Clients: {num_clients}, Rounds: {rounds}, Fraction: {fraction}")
    print(f"Aggregator: {cfg['aggregator']}, Consensus: {cfg['consensus']}")

    for r in range(1, rounds + 1):
        k = max(1, int(num_clients * fraction))
        import random
        random.seed(cfg["seed"] + r)
        selected = random.sample(
            [f"client_{i+1}" for i in range(num_clients)], k
        )

        print(f"--- Round {r}/{rounds} ---")
        print(f"Selected {len(selected)} clients: {selected}")

        resp = _http_post(
            f"{edge_url}/train",
            {"global_model": global_model, "client_ids": selected},
        )
        updates_raw = resp["updates"]
        print(f"Collected {len(updates_raw)} updates")

        resp = _http_post(
            f"{fog_url}/validate",
            {"updates": updates_raw, "round_num": r},
        )
        valid_raw = resp["valid"]
        print(f"{len(valid_raw)}/{len(updates_raw)} updates passed consensus")

        if not valid_raw:
            print("No valid updates, skipping round")
            continue

        from iomt_fl_consensus.core.models import ModelUpdate
        valid_updates = [ModelUpdate(**u) for u in valid_raw]
        global_model = aggregator.aggregate(valid_updates)

        participation = len(selected)
        accepted = len(valid_raw)
        proxy_accuracy = min(
            0.5
            + (abs(global_model["w1"]) + abs(global_model["w2"]) + abs(global_model["bias"]))
            / 6.0,
            0.99,
        )
        rows.append(
            {
                "round": r,
                "participation": participation,
                "accepted_updates": accepted,
                "communication_cost": participation * 3,
                "w1": global_model["w1"],
                "w2": global_model["w2"],
                "bias": global_model["bias"],
                "proxy_accuracy": proxy_accuracy,
                "aggregator": cfg["aggregator"],
                "consensus": cfg["consensus"],
            }
        )
        print(
            f"Round {r} completed: participation={participation}, "
            f"accepted={accepted}, proxy_accuracy={proxy_accuracy:.4f}"
        )

    outdir = Path("results")
    outdir.mkdir(exist_ok=True)
    csv_path = outdir / f"{cfg['name']}.csv"
    json_path = outdir / f"{cfg['name']}.json"

    import csv
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"\nExperiment completed: {cfg['name']}")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
