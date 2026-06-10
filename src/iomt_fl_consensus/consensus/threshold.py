import logging

logger = logging.getLogger(__name__)


class ThresholdConsensus:
    name = "threshold"

    def __init__(self, max_deviation=0.6):
        self.max_deviation = max_deviation
        logger.info(f"ThresholdConsensus initialized with max_deviation={max_deviation}")

    def validate_updates(self, updates, round_num=1):
        if not updates:
            logger.warning("ThresholdConsensus received empty updates list")
            return []
        valid = []
        for u in updates:
            score = sum(abs(v) for v in u.parameters.values())
            if score <= self.max_deviation * 10:
                valid.append(u)
            else:
                logger.debug(f"Update from {u.client_id} rejected: score={score:.2f} > threshold={self.max_deviation * 10}")
        logger.info(f"ThresholdConsensus: {len(valid)}/{len(updates)} updates accepted")
        return valid