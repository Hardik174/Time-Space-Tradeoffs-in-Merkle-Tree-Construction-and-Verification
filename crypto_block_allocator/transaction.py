import random

class Transaction:
    def __init__(self, tx_id: int, gas: int, fee: int):
        self.tx_id: int = tx_id
        self.gas: int = gas
        self.fee: int = fee
        self.region = random.randint(0, 50)   # logical state cluster
        self.depth = 0                        # assigned later
        self.proof_size: int = 0
        self.proof_time: int = 0
        self.effective_cost: int = 0

    def compute_effective_cost(self) -> None:
        self.effective_cost = int(self.gas + self.proof_size)

    def fee_per_cost(self) -> float:
        if self.effective_cost == 0:
            return 0.0
        return self.fee / self.effective_cost