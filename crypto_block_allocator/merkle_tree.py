import hashlib
import time


# --------------------------
# HASH FUNCTION
# --------------------------
def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()


# --------------------------
# BUILD MERKLE TREE
# --------------------------
def build_merkle_tree(transactions):
    leaves = [hash_data(str(tx.tx_id)) for tx in transactions]

    tree = [leaves]

    while len(tree[-1]) > 1:
        level = []
        nodes = tree[-1]

        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else left
            level.append(hash_data(left + right))

        tree.append(level)

    return tree


# --------------------------
# GET MERKLE PROOF
# --------------------------
def get_proof(tree, index):
    proof = []

    for level in tree[:-1]:
        pair_index = index ^ 1

        if pair_index < len(level):
            proof.append(level[pair_index])

        index //= 2

    return proof


# --------------------------
# VERIFY PROOF
# --------------------------
def verify_proof(leaf, proof, root):
    current = hash_data(leaf)

    for p in proof:
        current = hash_data(current + p)

    return current == root


# --------------------------
# MEASURE PROOF TIME
# --------------------------
def generate_proof_with_time(tree, index):
    start = time.time()
    proof = get_proof(tree, index)
    end = time.time()

    return proof, (end - start)


# --------------------------
# STEPS TO BUILD MERKLE TREE
# --------------------------
def build_merkle_tree_steps(transactions):
    leaves = [hash_data(str(tx.tx_id)) for tx in transactions]

    steps = []
    steps.append(leaves)

    current_level = leaves

    while len(current_level) > 1:
        next_level = []

        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left

            combined = hash_data(left + right)
            next_level.append(combined)

        steps.append(next_level)
        current_level = next_level

    return steps