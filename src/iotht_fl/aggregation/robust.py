import statistics
import logging

logger = logging.getLogger(__name__)


class RobustAggregator:
    name = "robust"

    def aggregate(self, updates):
        if not updates:
            logger.warning("RobustAggregator received empty updates list")
            return {}
        keys = updates[0].parameters.keys()
        result = {k: statistics.median([u.parameters[k] for u in updates]) for k in keys}
        logger.debug(f"Robust aggregated {len(updates)} updates using median")
        return result