import random
import logging

logger = logging.getLogger(__name__)


class SyntheticHealthDataGenerator:
    def __init__(self, seed=42):
        random.seed(seed)
        logger.info(f"SyntheticHealthDataGenerator initialized with seed={seed}")

    def generate_patient_records(self, n=1000, drift=0.0):
        data = []
        for _ in range(n):
            x1 = random.uniform(60, 120) / 120.0 + drift
            x2 = random.uniform(35, 40) / 40.0 + drift
            risk = 1 if (x1 + x2 + random.uniform(-0.1, 0.1)) > 1.7 else 0
            data.append(((x1, x2), risk))
        logger.debug(f"Generated {n} patient records with drift={drift:.2f}")
        return data