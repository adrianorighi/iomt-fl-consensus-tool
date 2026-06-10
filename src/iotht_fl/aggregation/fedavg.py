import logging

logger = logging.getLogger(__name__)


class FedAvgAggregator:
    name = "fedavg"

    def aggregate(self, updates):
        if not updates:
            logger.warning("FedAvgAggregator received empty updates list")
            return {}
        total = sum(u.num_samples for u in updates)
        keys = updates[0].parameters.keys()
        result = {k: sum(u.parameters[k] * u.num_samples for u in updates) / total for k in keys}
        logger.debug(f"FedAvg aggregated {len(updates)} updates, total samples={total}")
        return result