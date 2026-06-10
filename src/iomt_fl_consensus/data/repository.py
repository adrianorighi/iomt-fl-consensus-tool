import logging
from .generator import SyntheticHealthDataGenerator

logger = logging.getLogger(__name__)


class DataRepository:
    def __init__(self, seed=42):
        self.generator = SyntheticHealthDataGenerator(seed=seed)
        logger.info(f"DataRepository initialized with seed={seed}")

    def generate_synthetic_data(self, num_clients, samples_per_client, non_iid=False):
        clients_data = []
        for i in range(num_clients):
            drift = (i / max(1, num_clients)) * 0.2 if non_iid else 0.0
            client_data = self.generator.generate_patient_records(samples_per_client, drift=drift)
            clients_data.append(client_data)
            logger.debug(f"Client {i}: generated {len(client_data)} samples, drift={drift:.2f}")
        logger.info(f"Generated data for {num_clients} clients, {samples_per_client} samples each, non_iid={non_iid}")
        return clients_data