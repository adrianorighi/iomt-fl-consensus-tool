import random
import logging

from .models import ModelUpdate

logger = logging.getLogger(__name__)


class IoHTClient:
    def __init__(self, client_id, local_data, resource_profile, failure_rate=0.0, noise=0.05):
        self.client_id = client_id
        self.local_data = local_data
        self.resource_profile = resource_profile
        self.failure_rate = failure_rate
        self.noise = noise
        self.local_model = {"w1": 0.0, "w2": 0.0, "bias": 0.0}
        logger.info(f"IoHTClient '{client_id}' initialized with {len(local_data)} samples, failure_rate={failure_rate}, noise={noise}")

    def receive_global_model(self, model):
        self.local_model = dict(model)
        logger.info(f"Client '{self.client_id}' received global model", extra={"client_id": self.client_id, "method": "receive_global_model"})

    def simulate_failure(self):
        failed = random.random() < self.failure_rate
        if failed:
            logger.warning(f"Client '{self.client_id}' simulated failure")
        return failed

    def train_local_model(self):
        if self.simulate_failure():
            logger.info(f"Client '{self.client_id}' skipped training due to failure")
            return None
        n = len(self.local_data)
        mean_x1 = sum(x[0] for x, _ in self.local_data) / max(n, 1)
        mean_x2 = sum(x[1] for x, _ in self.local_data) / max(n, 1)
        mean_y = sum(y for _, y in self.local_data) / max(n, 1)
        update = {
            "w1": self.local_model["w1"] + 0.1 * mean_x1 + random.uniform(-self.noise, self.noise),
            "w2": self.local_model["w2"] + 0.1 * mean_x2 + random.uniform(-self.noise, self.noise),
            "bias": self.local_model["bias"] + 0.1 * mean_y + random.uniform(-self.noise, self.noise),
        }
        return ModelUpdate(self.client_id, update, n, {"mean_y": mean_y})