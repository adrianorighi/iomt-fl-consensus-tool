import logging

logger = logging.getLogger(__name__)


class WeightedAggregator:
    name = "weighted"

    def aggregate(self, updates):
        if not updates:
            logger.warning("WeightedAggregator received empty updates list")
            return {}
        total = sum((u.num_samples * (1 + u.metadata.get("mean_y", 0.0))) for u in updates)
        keys = updates[0].parameters.keys()
        result = {k: sum(u.parameters[k] * (u.num_samples * (1 + u.metadata.get("mean_y", 0.0))) for u in updates) / total for k in keys}
        logger.debug(f"Weighted aggregated {len(updates)} updates, weighted total={total:.2f}")
        return result