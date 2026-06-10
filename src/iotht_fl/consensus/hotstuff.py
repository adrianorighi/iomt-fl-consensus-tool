import hashlib
import random
import logging
from typing import List

logger = logging.getLogger(__name__)


class HotStuffConsensus:
    name = "hotstuff"

    def __init__(self, f=1, leader_selection="random", phases="single"):
        self.f = f
        self.leader_selection = leader_selection
        self.phases = phases
        self.committee_size = 3 * f + 1
        self.quorum_size = 2 * f + 1
        logger.info(f"HotStuffConsensus initialized with f={f}, committee_size={self.committee_size}, quorum={self.quorum_size}, leader={leader_selection}, phases={phases}")

    def _select_committee(self, client_ids: List[str], round_num: int) -> List[str]:
        if len(client_ids) < self.committee_size:
            logger.warning(f"HotStuff: insufficient clients ({len(client_ids)}) for committee size {self.committee_size}, using all clients")
            return client_ids

        seed = f"hotstuff_committee_round_{round_num}"
        rng = random.Random(hashlib.sha256(seed.encode()).hexdigest())
        committee = rng.sample(client_ids, self.committee_size)
        logger.debug(f"HotStuff round {round_num}: selected committee {committee}")
        return committee

    def _select_leader(self, committee: List[str], round_num: int) -> str:
        if self.leader_selection == "round_robin":
            leader_idx = round_num % len(committee)
            return committee[leader_idx]
        elif self.leader_selection == "first":
            return committee[0]
        else:
            seed = f"hotstuff_leader_round_{round_num}"
            rng = random.Random(hashlib.sha256(seed.encode()).hexdigest())
            return rng.choice(committee)

    def _validate_update_locally(self, update) -> bool:
        score = sum(abs(v) for v in update.parameters.values())
        return score <= 10.0

    def validate_updates(self, updates, round_num=1):
        if not updates:
            logger.warning("HotStuffConsensus received empty updates list")
            return []

        client_ids = [u.client_id for u in updates]
        committee = self._select_committee(client_ids, round_num)
        leader = self._select_leader(committee, round_num)

        logger.info(f"HotStuff round {round_num}: committee={len(committee)}, leader={leader}, quorum={self.quorum_size}")

        leader_proposal = []
        for u in updates:
            if u.client_id in committee:
                if self._validate_update_locally(u):
                    leader_proposal.append(u)

        logger.debug(f"HotStuff leader {leader} proposes {len(leader_proposal)} updates")

        yes_votes = 0
        for member in committee:
            if member == leader:
                yes_votes += 1
                continue
            member_updates = [u for u in updates if u.client_id == member]
            member_valid = all(self._validate_update_locally(u) for u in member_updates) if member_updates else True
            if member_valid:
                yes_votes += 1

        logger.debug(f"HotStuff round {round_num}: {yes_votes}/{len(committee)} validators voted yes")

        if yes_votes >= self.quorum_size:
            logger.info(f"HotStuffConsensus round {round_num}: proposal committed with {yes_votes}/{self.quorum_size} votes")
            return leader_proposal
        else:
            logger.warning(f"HotStuffConsensus round {round_num}: proposal rejected ({yes_votes}/{self.quorum_size} votes)")
            return []