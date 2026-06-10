import statistics
import logging
import math
from typing import List, Dict

logger = logging.getLogger(__name__)


class MultiKrumAggregator:
    name = "multi_krum"

    def __init__(self, f=1, m=None):
        self.f = f
        self.m = m
        logger.info(f"MultiKrumAggregator initialized with f={f}, m={m}")

    def _flatten_params(self, params: Dict[str, float]) -> List[float]:
        return [params[k] for k in sorted(params.keys())]

    def _unflatten_params(self, keys: List[str], values: List[float]) -> Dict[str, float]:
        return {k: v for k, v in zip(keys, values)}

    def _euclidean_distance(self, v1: List[float], v2: List[float]) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

    def _compute_scores(self, vectors: List[List[float]], n: int, f: int) -> List[float]:
        scores = []
        for i in range(n):
            distances = []
            for j in range(n):
                if i != j:
                    dist = self._euclidean_distance(vectors[i], vectors[j])
                    distances.append(dist)
            distances.sort()
            k_neighbors = n - f - 2
            if k_neighbors > 0:
                score = sum(d ** 2 for d in distances[:k_neighbors])
            else:
                score = sum(d ** 2 for d in distances)
            scores.append(score)
        return scores

    def aggregate(self, updates):
        if not updates:
            logger.warning("MultiKrumAggregator received empty updates list")
            return {}

        n = len(updates)
        f = min(self.f, max(0, (n - 3) // 2))
        m = self.m if self.m is not None else n - f
        m = min(m, n - f)

        if n < 3:
            logger.warning(f"MultiKrum: insufficient updates ({n}), falling back to median")
            keys = updates[0].parameters.keys()
            result = {k: statistics.median([u.parameters[k] for u in updates]) for k in keys}
            logger.debug(f"MultiKrum fallback: median of {n} updates")
            return result

        keys = sorted(updates[0].parameters.keys())
        vectors = [self._flatten_params(u.parameters) for u in updates]

        scores = self._compute_scores(vectors, n, f)

        sorted_indices = sorted(range(n), key=lambda i: scores[i])
        selected_indices = sorted_indices[:m]

        selected_vectors = [vectors[i] for i in selected_indices]
        selected_scores = [scores[i] for i in selected_indices]

        weights = [1.0 / (s + 1e-8) for s in selected_scores]
        weight_sum = sum(weights)
        weights = [w / weight_sum for w in weights]

        result_vector = [0.0] * len(keys)
        for vec, w in zip(selected_vectors, weights):
            for i, val in enumerate(vec):
                result_vector[i] += val * w

        result = self._unflatten_params(keys, result_vector)

        logger.debug(f"MultiKrum aggregated {n} updates, f={f}, m={m}, selected={selected_indices}, scores={selected_scores}")
        return result