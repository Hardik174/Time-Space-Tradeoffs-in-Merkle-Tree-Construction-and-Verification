from typing import List
from transaction import Transaction


def build_block_dp(mempool: List[Transaction], block_limit: int) -> List[Transaction]:
    n = len(mempool)

    dp = [[0 for _ in range(block_limit + 1)] for _ in range(n + 1)]

    # Fill DP table
    for i in range(1, n + 1):
        tx = mempool[i - 1]
        cost = tx.effective_cost
        fee = tx.fee

        for w in range(block_limit + 1):
            if cost <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - cost] + fee)
            else:
                dp[i][w] = dp[i - 1][w]

    # Backtrack to find selected transactions
    selected = []
    w = block_limit

    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            tx = mempool[i - 1]
            selected.append(tx)
            w -= tx.effective_cost

    selected.reverse()
    return selected