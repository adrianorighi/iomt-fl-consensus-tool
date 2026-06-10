from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ResourceProfile:
    cpu_limit: float
    memory_limit: float
    battery_level: float


@dataclass
class ModelUpdate:
    client_id: str
    parameters: Dict[str, float]
    num_samples: int
    metadata: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "client_id": self.client_id,
            "parameters": self.parameters,
            "num_samples": self.num_samples,
            "metadata": self.metadata,
        }