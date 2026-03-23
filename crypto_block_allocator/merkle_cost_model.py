import math

def assign_merkle_proof_cost(mempool):

    n = len(mempool)

    proof_size = int(math.log2(n)) + 1

    for tx in mempool:
        tx.proof_size = proof_size
        tx.compute_effective_cost()

def remove_proof_cost(mempool):
    for tx in mempool:
        tx.proof_size = 0
        tx.compute_effective_cost()