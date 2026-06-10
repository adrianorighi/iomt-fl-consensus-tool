import statistics
import logging

logger = logging.getLogger(__name__)


class VotingConsensus:
    name = "voting"

    def __init__(self, min_agreement=0.5):
        self.min_agreement = min_agreement
        logger.info(f"VotingConsensus initialized with min_agreement={min_agreement}")

    def validate_updates(self, updates, round_num=1):
        if not updates:
            logger.warning("VotingConsensus received empty updates list")
            return []
        keys = list(updates[0].parameters.keys())
        medians = {k: statistics.median([u.parameters[k] for u in updates]) for k in keys}
        logger.debug(f"VotingConsensus: median values = {medians}")
        valid = []
        for u in updates:
            agreements = 0
            for k in keys:
                if abs(u.parameters[k] - medians[k]) < 0.5:
                    agreements += 1
            if agreements / len(keys) >= self.min_agreement:
                valid.append(u)
            else:
                logger.debug(f"Update from {u.client_id} rejected: agreement={agreements/len(keys):.2f} < min={self.min_agreement}")
        logger.info(f"VotingConsensus: {len(valid)}/{len(updates)} updates accepted")
        return valid