import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("multi_block_results.csv")

# --------------------------
# CUMULATIVE REVENUE
# --------------------------
plt.figure(figsize=(10,6))

for (model, algo), group in df.groupby(["proof_model", "algorithm"]):
    plt.plot(group["block_id"], group["cumulative_fee"], label=f"{model}-{algo}")

plt.title("Cumulative Revenue Over Blocks")
plt.xlabel("Block Number")
plt.ylabel("Total Fee")
plt.legend()
plt.grid(True)
plt.savefig("multi_block_revenue.png")
plt.show()

# --------------------------
# MEMPOOL SIZE
# --------------------------
plt.figure(figsize=(10,6))

for (model, algo), group in df.groupby(["proof_model", "algorithm"]):
    plt.plot(group["block_id"], group["mempool_size_after"], label=f"{model}-{algo}")

plt.title("Mempool Size Over Time")
plt.xlabel("Block Number")
plt.ylabel("Remaining Transactions")
plt.legend()
plt.grid(True)
plt.savefig("multi_block_mempool.png")
plt.show()

# --------------------------
# UTILIZATION
# --------------------------
plt.figure(figsize=(10,6))

for (model, algo), group in df.groupby(["proof_model", "algorithm"]):
    plt.plot(group["block_id"], group["utilization"], label=f"{model}-{algo}")

plt.title("Block Utilization Over Time")
plt.xlabel("Block Number")
plt.ylabel("Utilization (%)")
plt.legend()
plt.grid(True)
plt.savefig("multi_block_utilization.png")
plt.show()