from typing import List
from transaction import Transaction

def build_block_greedy(mempool: List[Transaction], block_limit: int) -> List[Transaction]:

    mempool.sort(key=lambda tx: tx.fee_per_cost(), reverse=True)

    selected: List[Transaction] = []

    current_cost: int = 0   # <-- explicitly typed

    for tx in mempool:

        if current_cost + tx.effective_cost <= block_limit:
            selected.append(tx)
            current_cost += tx.effective_cost

    return selected