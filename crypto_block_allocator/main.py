from mempool_generator import generate_mempool
from merkle_cost_model import assign_merkle_proof_cost
from block_builder import build_block_greedy
from block_builder_dp import build_block_dp
from metrics import compute_metrics


def print_results(label, selected, block_limit):
    stats = compute_metrics(selected)

    print(f"\n===== {label} =====")
    print("Transactions Selected:", stats["transactions_selected"])
    print("Total Fee:", stats["total_fee"])
    print("Total Gas Used:", stats["total_gas"])
    print("Total Proof Cost:", stats["total_proof_cost"])

    total_cost = stats["total_gas"] + stats["total_proof_cost"]
    utilization = (total_cost / block_limit) * 100
    print(f"Block Utilization: {total_cost}/{block_limit} ({utilization:.2f}%)")

    return stats


def main():
    NUM_TRANSACTIONS = 100
    BLOCK_LIMIT = 1000

    print("Generating mempool...")
    mempool = generate_mempool(NUM_TRANSACTIONS)

    print("Assigning STANDARD Merkle proof costs...")
    assign_merkle_proof_cost(mempool, model="standard")

    greedy_selected = build_block_greedy(mempool[:], BLOCK_LIMIT)
    dp_selected = build_block_dp(mempool[:], BLOCK_LIMIT)

    greedy_stats = print_results("GREEDY", greedy_selected, BLOCK_LIMIT)
    dp_stats = print_results("DYNAMIC PROGRAMMING (OPTIMAL)", dp_selected, BLOCK_LIMIT)

    print("\n===== COMPARISON =====")
    print("Greedy Fee:", greedy_stats["total_fee"])
    print("Optimal Fee:", dp_stats["total_fee"])
    print("Revenue Gap:", dp_stats["total_fee"] - greedy_stats["total_fee"])


if __name__ == "__main__":
    main()

#===================================================================
#Version 2 with comparison between with and without proof cost
# from mempool_generator import generate_mempool
# from merkle_cost_model import assign_merkle_proof_cost, remove_proof_cost
# from block_builder import build_block_greedy
# from metrics import compute_metrics


# def run_simulation(mempool, block_limit, label):

#     print(f"\n===== {label} =====")

#     selected = build_block_greedy(mempool, block_limit)
#     stats = compute_metrics(selected)

#     # Print selected transactions
#     print("\nSelected Transactions:\n")
#     for tx in selected:
#         print(
#             f"TX {tx.tx_id} | Gas: {tx.gas} | Fee: {tx.fee} | "
#             f"Proof: {tx.proof_size} | Cost: {tx.effective_cost} | "
#             f"Efficiency: {tx.fee_per_cost():.2f}"
#         )

#     # Compute rejected transactions
#     rejected = [tx for tx in mempool if tx not in selected]
#     rejected.sort(key=lambda tx: tx.fee_per_cost(), reverse=True)

#     print("\nTop 10 Rejected Transactions:\n")
#     for tx in rejected[:10]:
#         print(
#             f"TX {tx.tx_id} | Gas: {tx.gas} | Fee: {tx.fee} | "
#             f"Cost: {tx.effective_cost} | Efficiency: {tx.fee_per_cost():.2f}"
#         )

#     # Print metrics
#     print("\n===== BLOCK METRICS =====")
#     print("Transactions Selected:", stats["transactions_selected"])
#     print("Total Fee:", stats["total_fee"])
#     print("Total Gas Used:", stats["total_gas"])
#     print("Total Proof Cost:", stats["total_proof_cost"])

#     # Block utilization
#     block_used = stats["total_gas"] + stats["total_proof_cost"]
#     utilization = (block_used / block_limit) * 100

#     print(f"Block Utilization: {block_used}/{block_limit} ({utilization:.2f}%)")

#     return stats


# def main():

#     NUM_TRANSACTIONS = 200
#     BLOCK_LIMIT = 1000

#     print("Generating mempool...")
#     mempool = generate_mempool(NUM_TRANSACTIONS)

#     # CASE 1 — WITH MERKLE PROOF COST
#     print("\nAssigning Merkle proof costs...")
#     assign_merkle_proof_cost(mempool)

#     stats_with_proof = run_simulation(
#         mempool, BLOCK_LIMIT, "WITH PROOF COST"
#     )

#     # CASE 2 — WITHOUT MERKLE PROOF COST
#     print("\nRemoving Merkle proof costs...")
#     remove_proof_cost(mempool)

#     stats_without_proof = run_simulation(
#         mempool, BLOCK_LIMIT, "WITHOUT PROOF COST"
#     )

#     # FINAL COMPARISON
#     print("\n===== COMPARISON =====")
#     print(f"With Proof Cost  → Total Fee: {stats_with_proof['total_fee']}")
#     print(f"Without Proof Cost → Total Fee: {stats_without_proof['total_fee']}")

#     diff = stats_without_proof["total_fee"] - stats_with_proof["total_fee"]

#     print(f"Revenue Loss due to Proof Cost: {diff}")


# if __name__ == "__main__":
#     main()




#===================================================================
# Version 1 — basic block builder with proof cost consideration
# from mempool_generator import generate_mempool
# from merkle_cost_model import assign_merkle_proof_cost
# from block_builder import build_block_greedy
# from metrics import compute_metrics


# def main():

#     NUM_TRANSACTIONS = 200
#     BLOCK_LIMIT = 1000

#     print("Generating mempool...")
#     mempool = generate_mempool(NUM_TRANSACTIONS)

#     print("Assigning Merkle proof costs...")
#     assign_merkle_proof_cost(mempool)

#     print("Building block...")
#     selected = build_block_greedy(mempool, BLOCK_LIMIT)

#     stats = compute_metrics(selected)

#     print("\nSelected Transactions:\n")

#     for tx in selected:
#         print(
#             f"TX {tx.tx_id} | "
#             f"Gas: {tx.gas} | "
#             f"Fee: {tx.fee} | "
#             f"Proof: {tx.proof_size} | "
#             f"Cost: {tx.effective_cost} | "
#             f"Efficiency: {tx.fee_per_cost():.2f}"
#         )
    
#     print("\n===== BLOCK METRICS =====")
#     print("Transactions Selected:", stats["transactions_selected"])
#     print("Total Fee:", stats["total_fee"])
#     print("Total Gas Used:", stats["total_gas"])
#     print("Total Proof Cost:", stats["total_proof_cost"])


# if __name__ == "__main__":
#     main()