import random
import logging

logger = logging.getLogger(__name__)


class FLServer:
    def __init__(self, clients, aggregator, consensus_module):
        self.clients = clients
        self.aggregator = aggregator
        self.consensus_module = consensus_module
        self.global_model = {"w1": 0.0, "w2": 0.0, "bias": 0.0}
        self.current_round = 0
        logger.info(f"FLServer initialized with {len(clients)} clients, aggregator={aggregator.__class__.__name__}, consensus={consensus_module.__class__.__name__}")

    def select_clients(self, fraction=1.0):
        k = max(1, int(len(self.clients) * fraction))
        k = min(k, len(self.clients))
        selected = random.sample(self.clients, k)
        client_ids = [c.client_id for c in selected]
        logger.info(f"Selected {k} clients for training (fraction={fraction})")
        logger.debug(f"Selected client IDs: {client_ids}", extra={"method": "select_clients", "client_ids": client_ids})
        return selected

    def distribute_model(self, selected_clients):
        client_ids = [c.client_id for c in selected_clients]
        for client in selected_clients:
            client.receive_global_model(self.global_model)
        logger.info(f"Distributed global model to {len(selected_clients)} clients: {client_ids}", extra={"method": "distribute_model", "client_ids": client_ids})

    def collect_updates(self, selected_clients):
        updates = []
        for client in selected_clients:
            update = client.train_local_model()
            if update is not None:
                updates.append(update)
        logger.info(f"Collected {len(updates)} updates from {len(selected_clients)} clients")
        return updates

    def update_global_model(self, updates):
        self.current_round += 1
        logger.debug(f"Validating {len(updates)} updates with consensus")
        valid = self.consensus_module.validate_updates(updates, round_num=self.current_round)
        if not valid:
            logger.warn("No updates passed consensus validation")
            return self.global_model, []
        logger.info(f"{len(valid)}/{len(updates)} updates passed consensus")
        self.global_model = self.aggregator.aggregate(valid)
        logger.info(f"Global model updated: w1={self.global_model['w1']:.4f}, w2={self.global_model['w2']:.4f}, bias={self.global_model['bias']:.4f}")
        return self.global_model, valid