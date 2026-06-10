from pathlib import Path
import csv
import json
import logging
import sys
from ..core import FLServer, IoHTClient, ResourceProfile
from ..aggregation import FedAvgAggregator, WeightedAggregator, RobustAggregator, MultiKrumAggregator
from ..consensus import ThresholdConsensus, VotingConsensus, HotStuffConsensus
from ..data import DataRepository

logger = logging.getLogger(__name__)


def setup_logging(config):
    log_level = config.get("log_level", "INFO").upper()
    log_file = config.get("log_file")
    log_format = config.get("log_format", "text")

    level = getattr(logging, log_level, logging.INFO)

    if log_format == "json":
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                import json
                log_obj = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if hasattr(record, 'round'):
                    log_obj["round"] = record.round
                if hasattr(record, 'client_id'):
                    log_obj["client_id"] = record.client_id
                if hasattr(record, 'method'):
                    log_obj["method"] = record.method
                return json.dumps(log_obj)
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    handlers = []
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    if log_file:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(level)
    for h in handlers:
        root_logger.addHandler(h)


class ExperimentRunner:
    def __init__(self, config):
        self.config = config
        setup_logging(config)
        self.repo = DataRepository(seed=config.get("seed", 42))
        logger.info(f"ExperimentRunner initialized with config: {config.get('name', 'unnamed')}")

    def _build_aggregator(self, name):
        aggregators = {
            "fedavg": FedAvgAggregator(),
            "weighted": WeightedAggregator(),
            "robust": RobustAggregator(),
            "multi_krum": MultiKrumAggregator(f=self.config.get("multi_krum_f", 1), m=self.config.get("multi_krum_m")),
        }
        if name not in aggregators:
            logger.error(f"Unknown aggregator: {name}. Available: {list(aggregators.keys())}")
            raise ValueError(f"Unknown aggregator: {name}. Available: {list(aggregators.keys())}")
        logger.info(f"Using aggregator: {name}")
        return aggregators[name]

    def _build_consensus(self, name):
        if name == "threshold":
            consensus = ThresholdConsensus(max_deviation=self.config.get("max_deviation", 0.6))
        elif name == "hotstuff":
            consensus = HotStuffConsensus(
                f=self.config.get("hotstuff_f", 1),
                leader_selection=self.config.get("hotstuff_leader", "random"),
                phases=self.config.get("hotstuff_phases", "single")
            )
        else:
            consensus = VotingConsensus(min_agreement=self.config.get("min_agreement", 0.5))
        logger.info(f"Using consensus: {name}")
        return consensus

    def run(self):
        logger.info("=" * 60)
        logger.info("Starting experiment")
        logger.info("=" * 60)

        num_clients = self.config["num_clients"]
        samples_per_client = self.config["samples_per_client"]
        rounds = self.config["rounds"]
        fraction = self.config.get("client_fraction", 1.0)
        aggregator = self._build_aggregator(self.config["aggregator"])
        consensus = self._build_consensus(self.config["consensus"])

        logger.info(f"Configuration: {num_clients} clients, {samples_per_client} samples/client, {rounds} rounds, fraction={fraction}")
        logger.info(f"Non-IID: {self.config.get('non_iid', False)}, Failure rate: {self.config.get('failure_rate', 0.0)}, Noise: {self.config.get('noise', 0.05)}")

        clients_data = self.repo.generate_synthetic_data(num_clients, samples_per_client, non_iid=self.config.get("non_iid", False))

        clients = []
        for i, data in enumerate(clients_data):
            profile = ResourceProfile(cpu_limit=1.0, memory_limit=256.0, battery_level=100.0)
            clients.append(IoHTClient(f"client_{i+1}", data, profile, failure_rate=self.config.get("failure_rate", 0.0), noise=self.config.get("noise", 0.05)))

        server = FLServer(clients, aggregator, consensus)
        rows = []

        for r in range(1, rounds + 1):
            logger.info(f"--- Round {r}/{rounds} ---", extra={"round": r, "method": "round_start"})
            selected = server.select_clients(fraction=fraction)
            server.distribute_model(selected)
            updates = server.collect_updates(selected)
            model, valid = server.update_global_model(updates)
            participation = len(selected)
            accepted = len(valid)
            communication_cost = participation * 3
            proxy_accuracy = min(0.5 + (abs(model["w1"]) + abs(model["w2"]) + abs(model["bias"])) / 6.0, 0.99)
            rows.append({
                "round": r,
                "participation": participation,
                "accepted_updates": accepted,
                "communication_cost": communication_cost,
                "w1": model["w1"],
                "w2": model["w2"],
                "bias": model["bias"],
                "proxy_accuracy": proxy_accuracy,
                "aggregator": self.config["aggregator"],
                "consensus": self.config["consensus"]
            })
            logger.info(f"Round {r} completed: participation={participation}, accepted={accepted}, proxy_accuracy={proxy_accuracy:.4f}", extra={"round": r, "method": "round_end", "participation": participation, "accepted": accepted, "proxy_accuracy": proxy_accuracy})

        logger.info("=" * 60)
        logger.info("Experiment completed")
        logger.info("=" * 60)
        return rows

    def export(self, rows, output_prefix):
        outdir = Path("results")
        outdir.mkdir(exist_ok=True)
        csv_path = outdir / f"{output_prefix}.csv"
        json_path = outdir / f"{output_prefix}.json"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)
        logger.info(f"Results exported to {csv_path} and {json_path}")
        return str(csv_path), str(json_path)