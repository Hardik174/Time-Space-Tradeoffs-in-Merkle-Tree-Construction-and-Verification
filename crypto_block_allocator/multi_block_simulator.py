import copy
import time
import csv

from mempool_generator import generate_mempool
from merkle_cost_model import assign_merkle_proof_cost
from block_builder import build_block_greedy
from block_builder_dp import build_block_dp
from metrics import compute_metrics

# --------------------------
# CONFIG
# --------------------------
BLOCK_LIMIT = 1000
NUM_BLOCKS = 20
TX_ARRIVAL_PER_BLOCK = 200

PROOF_MODELS = ["standard", "cached", "batch"]
ALGORITHMS = ["greedy", "dp"]

OUTPUT_FILE = "multi_block_results.csv"


# --------------------------
# SIMULATION FUNCTION
# --------------------------
def run_simulation(proof_model, algorithm):
    mempool = []
    all_block_data = []

    cumulative_fee = 0

    for block_id in range(NUM_BLOCKS):

        # Step 1: Add new transactions
        new_txs = generate_mempool(TX_ARRIVAL_PER_BLOCK)
        mempool.extend(new_txs)

        # Step 2: Assign proof costs
        assign_merkle_proof_cost(mempool, model=proof_model)

        # Step 3: Select block
        start_time = time.time()

        if algorithm == "greedy":
            selected = build_block_greedy(mempool, BLOCK_LIMIT)
        else:
            selected = build_block_dp(mempool, BLOCK_LIMIT)

        runtime = time.time() - start_time

        # Step 4: Compute metrics
        stats = compute_metrics(selected)

        total_cost = stats["total_gas"] + stats["total_proof_cost"]
        utilization = (total_cost / BLOCK_LIMIT) * 100

        cumulative_fee += stats["total_fee"]

        # Step 5: Remove selected transactions
        selected_ids = set(tx.tx_id for tx in selected)
        mempool = [tx for tx in mempool if tx.tx_id not in selected_ids]

        # Step 6: Store results
        all_block_data.append({
            "block_id": block_id,
            "proof_model": proof_model,
            "algorithm": algorithm,
            "transactions_selected": stats["transactions_selected"],
            "block_fee": stats["total_fee"],
            "cumulative_fee": cumulative_fee,
            "utilization": round(utilization, 2),
            "mempool_size_after": len(mempool),
            "runtime_sec": round(runtime, 6)
        })

        print(f"[{proof_model}-{algorithm}] Block {block_id} | Fee={stats['total_fee']} | Mempool={len(mempool)}")

    return all_block_data


# --------------------------
# MAIN
# --------------------------
def main():
    results = []

    print("Starting multi-block simulation...\n")

    for proof_model in PROOF_MODELS:
        for algorithm in ALGORITHMS:
            print(f"\nRunning: {proof_model} - {algorithm}")
            data = run_simulation(proof_model, algorithm)
            results.extend(data)

    # Save CSV
    with open(OUTPUT_FILE, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSimulation complete. Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()