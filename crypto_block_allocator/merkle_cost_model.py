import math
from collections import defaultdict
from merkle_tree import build_merkle_tree, generate_proof_with_time

def standard_proof_cost(tx, state_size):
    depth = math.log2(state_size)
    noise = 0.8 + 0.4 * (tx.region % 5) / 5   # small variation
    return int(depth * noise)


def cached_proof_cost(tx, state_size, region_cache):
    depth = math.log2(state_size)

    if tx.region in region_cache:
        return int(depth * 0.3)   # reuse cached nodes
    else:
        region_cache.add(tx.region)
        return int(depth)


def batch_proof_cost(tx, batch_map, state_size):
    depth = math.log2(state_size)

    group_size = batch_map[tx.region]

    if group_size > 1:
        return int(depth / group_size + 2)
    else:
        return int(depth)


# def assign_merkle_proof_cost(mempool, model="standard"):
#     state_size = len(mempool) * 10

#     if model == "standard":
#         for tx in mempool:
#             tx.proof_size = standard_proof_cost(tx, state_size)
#             tx.compute_effective_cost()

#     elif model == "cached":
#         region_cache = set()

#         for tx in mempool:
#             tx.proof_size = cached_proof_cost(tx, state_size, region_cache)
#             tx.compute_effective_cost()

#     elif model == "batch":
#         batch_map = defaultdict(int)

#         for tx in mempool:
#             batch_map[tx.region] += 1

#         for tx in mempool:
#             tx.proof_size = batch_proof_cost(tx, batch_map, state_size)
#             tx.compute_effective_cost()

#     else:
#         raise ValueError("Invalid model")

def assign_merkle_proof_cost(mempool, model="standard"):

    # Build actual Merkle tree
    tree = build_merkle_tree(mempool)

    # --------------------------
    # STANDARD MODEL
    # --------------------------
    if model == "standard":
        for i, tx in enumerate(mempool):
            proof, p_time = generate_proof_with_time(tree, i)

            tx.proof_size = len(proof)
            tx.proof_time = p_time

            tx.compute_effective_cost()

    # --------------------------
    # CACHED MODEL
    # --------------------------
    elif model == "cached":
        region_cache = {}

        for i, tx in enumerate(mempool):
            if tx.region in region_cache:
                # reuse proof
                tx.proof_size = region_cache[tx.region]["size"] * 0.5
                tx.proof_time = region_cache[tx.region]["time"] * 0.5
            else:
                proof, p_time = generate_proof_with_time(tree, i)

                tx.proof_size = len(proof)
                tx.proof_time = p_time

                region_cache[tx.region] = {
                    "size": tx.proof_size,
                    "time": tx.proof_time
                }

            tx.compute_effective_cost()

    # --------------------------
    # BATCH MODEL
    # --------------------------
    elif model == "batch":
        region_groups = {}

        for i, tx in enumerate(mempool):
            region_groups.setdefault(tx.region, []).append(i)

        for region, indices in region_groups.items():
            # Generate one proof for group
            proof, p_time = generate_proof_with_time(tree, indices[0])

            shared_size = len(proof) / len(indices)
            shared_time = p_time / len(indices)

            for idx in indices:
                tx = mempool[idx]
                tx.proof_size = shared_size
                tx.proof_time = shared_time
                tx.compute_effective_cost()

    else:
        raise ValueError("Invalid model")


# import math
# import random


# def assign_merkle_proof_cost(mempool, model="standard"):
#     n = len(mempool)
#     base_proof = int(math.log2(n)) + 1

#     if model == "standard":
#         for tx in mempool:
#             tx.proof_size = base_proof
#             tx.compute_effective_cost()

#     elif model == "cached":
#         for tx in mempool:
#             # Slight reduction due to shared cached paths
#             tx.proof_size = max(1, base_proof - random.randint(1, 3))
#             tx.compute_effective_cost()

#     elif model == "batch":
#         for tx in mempool:
#             # Simulate aggregated proof compression
#             tx.proof_size = max(1, int(base_proof * 0.5) + random.randint(0, 2))
#             tx.compute_effective_cost()

#     else:
#         raise ValueError("Invalid proof model")


# def remove_proof_cost(mempool):
#     for tx in mempool:
#         tx.proof_size = 0
#         tx.compute_effective_cost()