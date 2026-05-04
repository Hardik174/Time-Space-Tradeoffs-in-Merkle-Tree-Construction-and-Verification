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
MEMPOOL_SIZES = [50, 100, 200, 500, 1000, 5000, 10000, 100000]
BLOCK_LIMIT = 1000
PROOF_MODELS = ["standard", "cached", "batch"]

OUTPUT_FILE = "experiment_results.csv"


# --------------------------
# RUN ONE CONFIG
# --------------------------
def run_experiment(base_mempool, proof_model, algorithm):
    mempool = copy.deepcopy(base_mempool)

    assign_merkle_proof_cost(mempool, model=proof_model)

    start_time = time.time()

    if algorithm == "greedy":
        selected = build_block_greedy(mempool, BLOCK_LIMIT)
    elif algorithm == "dp":
        selected = build_block_dp(mempool, BLOCK_LIMIT)
    else:
        raise ValueError("Invalid algorithm")

    end_time = time.time()

    stats = compute_metrics(selected)
    total_cost = stats["total_gas"] + stats["total_proof_cost"]
    utilization = (total_cost / BLOCK_LIMIT) * 100

    return {
        "transactions_selected": stats["transactions_selected"],
        "total_fee": stats["total_fee"],
        "total_gas": stats["total_gas"],
        "total_proof_cost": stats["total_proof_cost"],
        "total_proof_time": stats["total_proof_time"],
        "total_cost": total_cost,
        "utilization": round(utilization, 2),
        "runtime_sec": round(end_time - start_time, 6)
    }


# --------------------------
# MAIN RUNNER
# --------------------------
def main():
    all_results = []

    print("Running experiments...\n")

    for mempool_size in MEMPOOL_SIZES:
        print(f"\nGenerating base mempool for size = {mempool_size}")
        base_mempool = generate_mempool(mempool_size)

        for proof_model in PROOF_MODELS:
            print(f"Running: Size={mempool_size}, Model={proof_model}, Algo=greedy")
            greedy_result = run_experiment(base_mempool, proof_model, "greedy")

            print(f"Running: Size={mempool_size}, Model={proof_model}, Algo=dp")
            dp_result = run_experiment(base_mempool, proof_model, "dp")

            # Compute optimality gap
            optimality_gap = (
                (dp_result["total_fee"] - greedy_result["total_fee"]) / dp_result["total_fee"] * 100
                if dp_result["total_fee"] > 0 else 0
            )

            # Save Greedy row
            greedy_row = greedy_result.copy()
            greedy_row["mempool_size"] = mempool_size
            greedy_row["proof_model"] = proof_model
            greedy_row["algorithm"] = "greedy"
            greedy_row["optimality_gap_percent"] = round(optimality_gap, 2)

            # Save DP row
            dp_row = dp_result.copy()
            dp_row["mempool_size"] = mempool_size
            dp_row["proof_model"] = proof_model
            dp_row["algorithm"] = "dp"
            dp_row["optimality_gap_percent"] = 0.0

            all_results.append(greedy_row)
            all_results.append(dp_row)

    # Save CSV
    with open(OUTPUT_FILE, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\nExperiments completed. Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()