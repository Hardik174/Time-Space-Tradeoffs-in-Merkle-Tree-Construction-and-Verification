import pandas as pd
import matplotlib.pyplot as plt

# --------------------------
# LOAD DATA
# --------------------------
df = pd.read_csv("experiment_results.csv")

# --------------------------
# GRAPH 1: Revenue vs Mempool Size
# --------------------------
plt.figure(figsize=(10, 6))

for (proof_model, algorithm), group in df.groupby(["proof_model", "algorithm"]):
    label = f"{proof_model}-{algorithm}"
    plt.plot(group["mempool_size"], group["total_fee"], marker="o", label=label)

plt.title("Revenue vs Mempool Size")
plt.xlabel("Mempool Size")
plt.ylabel("Total Fee")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("new_revenue_vs_mempool.png")
plt.show()

# --------------------------
# GRAPH 2: Runtime vs Mempool Size
# --------------------------
plt.figure(figsize=(10, 6))

for (proof_model, algorithm), group in df.groupby(["proof_model", "algorithm"]):
    label = f"{proof_model}-{algorithm}"
    plt.plot(group["mempool_size"], group["runtime_sec"], marker="o", label=label)

plt.title("Runtime vs Mempool Size")
plt.xlabel("Mempool Size")
plt.ylabel("Runtime (seconds)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("new_runtime_vs_mempool.png")
plt.show()

# --------------------------
# GRAPH 3: Utilization vs Mempool Size
# --------------------------
plt.figure(figsize=(10, 6))

for (proof_model, algorithm), group in df.groupby(["proof_model", "algorithm"]):
    label = f"{proof_model}-{algorithm}"
    plt.plot(group["mempool_size"], group["utilization"], marker="o", label=label)

plt.title("Block Utilization vs Mempool Size")
plt.xlabel("Mempool Size")
plt.ylabel("Utilization (%)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("new_utilization_vs_mempool.png")
plt.show()

# --------------------------
# GRAPH 4: Transactions Selected vs Mempool Size
# --------------------------
plt.figure(figsize=(10, 6))

for (proof_model, algorithm), group in df.groupby(["proof_model", "algorithm"]):
    label = f"{proof_model}-{algorithm}"
    plt.plot(group["mempool_size"], group["transactions_selected"], marker="o", label=label)

plt.title("Transactions Selected vs Mempool Size")
plt.xlabel("Mempool Size")
plt.ylabel("Transactions Selected")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("new_transactions_selected_vs_mempool.png")
plt.show()

# --------------------------
# GRAPH 5: Optimality Gap vs Mempool Size
# (Greedy only)
# --------------------------
greedy_df = df[df["algorithm"] == "greedy"]

plt.figure(figsize=(10, 6))

for proof_model, group in greedy_df.groupby("proof_model"):
    label = f"{proof_model}-greedy"
    plt.plot(group["mempool_size"], group["optimality_gap_percent"], marker="o", label=label)

plt.title("Optimality Gap vs Mempool Size")
plt.xlabel("Mempool Size")
plt.ylabel("Optimality Gap (%)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("new_optimality_gap_vs_mempool.png")
plt.show()


# --------------------------
# Graph 6: Proof Time vs Mempool Size
# --------------------------
plt.figure(figsize=(10, 6))

for (proof_model, algorithm), group in df.groupby(["proof_model", "algorithm"]):
    label = f"{proof_model}-{algorithm}"
    plt.plot(group["mempool_size"], group["total_proof_time"], marker="o", label=label)

plt.title("Total Proof Time vs Mempool Size")
plt.xlabel("Mempool Size")
plt.ylabel("Proof Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("proof_time_vs_mempool.png")
plt.show()