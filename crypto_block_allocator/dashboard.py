import copy
import time
import streamlit as st
import time

from mempool_generator import generate_mempool
from merkle_cost_model import assign_merkle_proof_cost
from block_builder_dp import build_block_dp
from merkle_tree import build_merkle_tree_steps

# --------------------------
# CONFIG
# --------------------------
NUM_TRANSACTIONS = 50
BLOCK_LIMIT = 1000

# --------------------------
# TITLE
# --------------------------
st.title("Blockchain Block Allocation Dashboard")
st.markdown("Compare transaction selection under different Merkle proof models.")

# --------------------------
# PROOF MODEL SELECTOR
# --------------------------
proof_model = st.selectbox(
    "Select Merkle Proof Model",
    ["standard", "cached", "batch"]
)

# --------------------------
# MODEL EXPLANATION
# --------------------------
if proof_model == "standard":
    st.info("Standard: Each transaction has independent proof cost.")
elif proof_model == "cached":
    st.info("Cached: Repeated state accesses reuse proof nodes, reducing cost.")
elif proof_model == "batch":
    st.info("Batch: Transactions share proof paths, reducing overall proof cost.")

# --------------------------
# INIT SESSION STATE
# --------------------------
if "base_mempool" not in st.session_state:
    st.session_state.base_mempool = generate_mempool(NUM_TRANSACTIONS)

if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = []

if "warning_msg" not in st.session_state:
    st.session_state.warning_msg = ""

if "last_runtime" not in st.session_state:
    st.session_state.last_runtime = None

if "last_algo" not in st.session_state:
    st.session_state.last_algo = "Manual"

if "last_model" not in st.session_state:
    st.session_state.last_model = proof_model

# --------------------------
# KEEP SAME MEMPOOL
# --------------------------
if "mempool" not in st.session_state or st.session_state.last_model != proof_model:
    mempool = copy.deepcopy(st.session_state.base_mempool)
    assign_merkle_proof_cost(mempool, model=proof_model)

    st.session_state.mempool = mempool
    st.session_state.selected_ids = []
    st.session_state.warning_msg = ""
    st.session_state.last_runtime = None
    st.session_state.last_algo = "Manual"
    st.session_state.last_model = proof_model

mempool = st.session_state.mempool

# --------------------------
# GREEDY FUNCTION
# --------------------------
def run_greedy(mempool, block_limit):
    sorted_txs = sorted(
        mempool,
        key=lambda tx: tx.fee / tx.effective_cost,
        reverse=True
    )

    selected = []
    current_cost = 0

    for tx in sorted_txs:
        if current_cost + tx.effective_cost <= block_limit:
            selected.append(tx)
            current_cost += tx.effective_cost

    return selected

# --------------------------
# BUTTONS
# --------------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Run Greedy Selection"):
        start = time.time()
        selected = run_greedy(mempool, BLOCK_LIMIT)
        end = time.time()

        st.session_state.selected_ids = [tx.tx_id for tx in selected]
        st.session_state.last_runtime = end - start
        st.session_state.last_algo = "Greedy"
        st.rerun()

with col2:
    if st.button("Run Optimal (DP)"):
        start = time.time()
        selected = build_block_dp(mempool, BLOCK_LIMIT)
        end = time.time()

        st.session_state.selected_ids = [tx.tx_id for tx in selected]
        st.session_state.last_runtime = end - start
        st.session_state.last_algo = "DP (Optimal)"
        st.rerun()

with col3:
    if st.button("Clear Selection"):
        st.session_state.selected_ids = []
        st.session_state.last_runtime = None
        st.session_state.last_algo = "Manual"
        st.rerun()

# --------------------------
# INFO
# --------------------------
st.info(f"Current algorithm: {st.session_state.last_algo}")

if st.session_state.last_runtime:
    st.write(f"Execution Time: {st.session_state.last_runtime:.6f} sec")

# --------------------------
# MEMPOOL DISPLAY
# --------------------------
st.subheader("Mempool")

current_selected = [
    tx for tx in mempool if tx.tx_id in st.session_state.selected_ids
]

current_cost = sum(tx.effective_cost for tx in current_selected)

for tx in mempool:
    col1, col2 = st.columns([1, 6])

    is_selected = tx.tx_id in st.session_state.selected_ids

    with col1:
        checked = st.checkbox(
        f"select_{tx.tx_id}",
        value=is_selected,
        key=f"tx_{tx.tx_id}",
        label_visibility="collapsed"
    )

    with col2:
        st.write(
            f"TX {tx.tx_id} | Gas: {tx.gas} | Fee: {tx.fee} | "
            # f"Proof: {tx.proof_size} | Cost: {tx.effective_cost}"
            f"Proof: {tx.proof_size:.2f} | Time: {tx.proof_time:.6f} | Cost: {tx.effective_cost}"
        )

    if checked and not is_selected:
        if current_cost + tx.effective_cost > BLOCK_LIMIT:
            st.session_state.warning_msg = "Block limit exceeded."
        else:
            st.session_state.selected_ids.append(tx.tx_id)
            current_cost += tx.effective_cost

    elif not checked and is_selected:
        st.session_state.selected_ids.remove(tx.tx_id)
        current_cost -= tx.effective_cost

# --------------------------
# METRICS
# --------------------------
selected_txs = [
    tx for tx in mempool if tx.tx_id in st.session_state.selected_ids
]

total_fee = sum(tx.fee for tx in selected_txs)
total_cost = sum(tx.effective_cost for tx in selected_txs)
utilization = (total_cost / BLOCK_LIMIT) * 100

st.subheader("Current Block Metrics")
st.write(f"Transactions Selected: {len(selected_txs)}")
st.write(f"Total Fee: {total_fee}")
st.write(f"Block Utilization: {utilization:.2f}%")

# --------------------------
# COMPARISON
# --------------------------
st.subheader("Greedy vs DP Comparison")

greedy_selected = run_greedy(mempool, BLOCK_LIMIT)
dp_selected = build_block_dp(mempool, BLOCK_LIMIT)

greedy_fee = sum(tx.fee for tx in greedy_selected)
dp_fee = sum(tx.fee for tx in dp_selected)

gap = dp_fee - greedy_fee
gap_percent = (gap / dp_fee * 100) if dp_fee > 0 else 0

st.write(f"Greedy Revenue: {greedy_fee}")
st.write(f"DP Revenue: {dp_fee}")
st.write(f"Optimality Gap: {gap_percent:.2f}%")

# --------------------------
# MULTI-BLOCK SIMULATION
# --------------------------
st.subheader("Multi-Block Simulation")

def run_multi_block(proof_model, algo):
    mempool = []
    cumulative_fee = 0
    results = []

    for i in range(10):
        mempool.extend(generate_mempool(100))
        assign_merkle_proof_cost(mempool, model=proof_model)

        if algo == "Greedy":
            selected = run_greedy(mempool, BLOCK_LIMIT)
        else:
            selected = build_block_dp(mempool, BLOCK_LIMIT)

        fee = sum(tx.fee for tx in selected)
        cumulative_fee += fee

        selected_ids = set(tx.tx_id for tx in selected)
        mempool = [tx for tx in mempool if tx.tx_id not in selected_ids]

        results.append((i, fee, cumulative_fee, len(mempool)))

    return results

if st.button("Run Multi-Block Simulation"):
    data = run_multi_block(proof_model, st.session_state.last_algo)

    for d in data:
        st.write(
            f"Block {d[0]} | Fee: {d[1]} | "
            f"Cumulative: {d[2]} | Mempool: {d[3]}"
        )


# --------------------------
# MERKLE TREE VISUALIZATION
# --------------------------
st.subheader("Merkle Tree Visualization")

if st.button("Visualize Merkle Tree"):

    if len(mempool) > 0:

        steps = build_merkle_tree_steps(mempool[:8])
        total_levels = len(steps)

        st.write("Building Merkle Tree Step-by-Step...")

        for i, level in enumerate(reversed(steps)):

            actual_level = total_levels - i - 1

            st.write(f"Level {actual_level} → {len(level)} nodes")

            row = "   ".join([node[:10] + "..." for node in level])
            st.code(row)

            time.sleep(1)


# --------------------------
# HASH COMPUTATION DEMO
# --------------------------
st.subheader("Hash Computation Demo")

if st.button("Show How Hashes Are Generated"):

    if len(mempool) >= 2:

        tx1 = mempool[0]
        tx2 = mempool[1]

        from merkle_tree import hash_data

        leaf1 = hash_data(str(tx1.tx_id))
        leaf2 = hash_data(str(tx2.tx_id))

        combined_input = leaf1 + leaf2
        parent_hash = hash_data(combined_input)

        st.write("Step 1: Leaf Hashes")
        st.code(f"H({tx1.tx_id}) = {leaf1}")
        st.code(f"H({tx2.tx_id}) = {leaf2}")

        st.write("Step 2: Combine Hashes")
        st.code(f"{leaf1[:10]}... + {leaf2[:10]}...")

        st.write("Step 3: Parent Hash")
        st.code(f"H(left + right) = {parent_hash}")


# --------------------------
# INSIGHT PANEL
# --------------------------
st.subheader("Key Insight")

st.write(
    "Batch and Cached proof models allow greedy algorithms to achieve near-optimal "
    "performance, reducing the need for expensive dynamic programming in real blockchain systems."
)


#============================================================
#Version 3
# import copy
# import time
# import streamlit as st

# from mempool_generator import generate_mempool
# from merkle_cost_model import assign_merkle_proof_cost
# from block_builder_dp import build_block_dp

# # --------------------------
# # CONFIG
# # --------------------------
# NUM_TRANSACTIONS = 50
# BLOCK_LIMIT = 1000

# # --------------------------
# # TITLE
# # --------------------------
# st.title("Blockchain Block Allocation Dashboard")
# st.markdown("Compare transaction selection under different Merkle proof models.")

# # --------------------------
# # PROOF MODEL SELECTOR
# # --------------------------
# proof_model = st.selectbox(
#     "Select Merkle Proof Model",
#     ["standard", "cached", "batch"]
# )

# # --------------------------
# # INIT SESSION STATE
# # --------------------------
# if "base_mempool" not in st.session_state:
#     st.session_state.base_mempool = generate_mempool(NUM_TRANSACTIONS)

# if "selected_ids" not in st.session_state:
#     st.session_state.selected_ids = []

# if "warning_msg" not in st.session_state:
#     st.session_state.warning_msg = ""

# if "last_runtime" not in st.session_state:
#     st.session_state.last_runtime = None

# if "last_algo" not in st.session_state:
#     st.session_state.last_algo = "Manual"

# if "last_model" not in st.session_state:
#     st.session_state.last_model = proof_model

# # --------------------------
# # KEEP SAME MEMPOOL, CHANGE ONLY PROOF MODEL
# # --------------------------
# if "mempool" not in st.session_state or st.session_state.last_model != proof_model:
#     mempool = copy.deepcopy(st.session_state.base_mempool)
#     assign_merkle_proof_cost(mempool, model=proof_model)
#     st.session_state.mempool = mempool
#     st.session_state.selected_ids = []
#     st.session_state.warning_msg = ""
#     st.session_state.last_runtime = None
#     st.session_state.last_algo = "Manual"
#     st.session_state.last_model = proof_model

# mempool = st.session_state.mempool

# # --------------------------
# # HELPER: GREEDY SELECTION
# # --------------------------
# def run_greedy(mempool, block_limit):
#     sorted_txs = sorted(
#         mempool,
#         key=lambda tx: tx.fee / tx.effective_cost,
#         reverse=True
#     )

#     selected = []
#     current_cost = 0

#     for tx in sorted_txs:
#         if current_cost + tx.effective_cost <= block_limit:
#             selected.append(tx)
#             current_cost += tx.effective_cost

#     return selected

# # --------------------------
# # BUTTONS
# # --------------------------
# col1, col2, col3 = st.columns(3)

# with col1:
#     if st.button("Run Greedy Selection"):
#         start = time.time()
#         selected = run_greedy(mempool, BLOCK_LIMIT)
#         end = time.time()

#         st.session_state.selected_ids = [tx.tx_id for tx in selected]
#         st.session_state.warning_msg = ""
#         st.session_state.last_runtime = end - start
#         st.session_state.last_algo = "Greedy"
#         st.rerun()

# with col2:
#     if st.button("Run Optimal (DP)"):
#         start = time.time()
#         selected = build_block_dp(mempool, BLOCK_LIMIT)
#         end = time.time()

#         st.session_state.selected_ids = [tx.tx_id for tx in selected]
#         st.session_state.warning_msg = ""
#         st.session_state.last_runtime = end - start
#         st.session_state.last_algo = "DP (Optimal)"
#         st.rerun()

# with col3:
#     if st.button("Clear Selection"):
#         st.session_state.selected_ids = []
#         st.session_state.warning_msg = ""
#         st.session_state.last_runtime = None
#         st.session_state.last_algo = "Manual"
#         st.rerun()

# # --------------------------
# # INFO PANEL
# # --------------------------
# st.info(f"Current algorithm: {st.session_state.last_algo}")

# if st.session_state.last_runtime is not None:
#     st.write(f"Execution Time: {st.session_state.last_runtime:.6f} seconds")

# # --------------------------
# # MEMPOOL DISPLAY
# # --------------------------
# st.subheader("Mempool")

# current_selected = [
#     tx for tx in mempool if tx.tx_id in st.session_state.selected_ids
# ]

# current_cost = sum(tx.effective_cost for tx in current_selected)

# for tx in mempool:
#     col1, col2 = st.columns([1, 6])

#     is_selected = tx.tx_id in st.session_state.selected_ids

#     with col1:
#         checked = st.checkbox(
#             "",
#             value=is_selected,
#             key=f"tx_{tx.tx_id}"
#         )

#     with col2:
#         st.write(
#             f"TX {tx.tx_id} | Gas: {tx.gas} | Fee: {tx.fee} | "
#             f"Proof: {tx.proof_size} | Cost: {tx.effective_cost}"
#         )

#     # Selection logic without rerun loop
#     if checked and not is_selected:
#         if current_cost + tx.effective_cost > BLOCK_LIMIT:
#             st.session_state.warning_msg = "Cannot add transaction: Block limit exceeded."
#         else:
#             st.session_state.selected_ids.append(tx.tx_id)
#             current_cost += tx.effective_cost
#             st.session_state.warning_msg = ""

#     elif not checked and is_selected:
#         st.session_state.selected_ids.remove(tx.tx_id)
#         current_cost -= tx.effective_cost
#         st.session_state.warning_msg = ""

# # --------------------------
# # WARNING
# # --------------------------
# if st.session_state.warning_msg:
#     st.warning(st.session_state.warning_msg)

# # --------------------------
# # CURRENT SELECTION METRICS
# # --------------------------
# selected_txs = [
#     tx for tx in mempool if tx.tx_id in st.session_state.selected_ids
# ]

# total_fee = sum(tx.fee for tx in selected_txs)
# total_gas = sum(tx.gas for tx in selected_txs)
# total_proof = sum(tx.proof_size for tx in selected_txs)
# total_cost = total_gas + total_proof
# utilization = (total_cost / BLOCK_LIMIT) * 100

# # Clear warning if current block is valid again
# if total_cost < BLOCK_LIMIT and st.session_state.warning_msg == "Cannot add transaction: Block limit exceeded.":
#     st.session_state.warning_msg = ""

# st.subheader("Current Block Metrics")
# st.write(f"Transactions Selected: {len(selected_txs)}")
# st.write(f"Total Fee: {total_fee}")
# st.write(f"Total Gas: {total_gas}")
# st.write(f"Total Proof Cost: {total_proof}")
# st.write(f"Block Utilization: {total_cost}/{BLOCK_LIMIT} ({utilization:.2f}%)")

# # --------------------------
# # BLOCK STATUS
# # --------------------------
# if total_cost >= BLOCK_LIMIT:
#     st.error("Block limit reached.")
# else:
#     st.success("Block within limit.")

# # --------------------------
# # COMPARISON PANEL
# # --------------------------
# st.subheader("Greedy vs DP Comparison")

# greedy_start = time.time()
# greedy_selected = run_greedy(mempool, BLOCK_LIMIT)
# greedy_time = time.time() - greedy_start

# dp_start = time.time()
# dp_selected = build_block_dp(mempool, BLOCK_LIMIT)
# dp_time = time.time() - dp_start

# greedy_fee = sum(tx.fee for tx in greedy_selected)
# dp_fee = sum(tx.fee for tx in dp_selected)

# greedy_cost = sum(tx.effective_cost for tx in greedy_selected)
# dp_cost = sum(tx.effective_cost for tx in dp_selected)

# greedy_util = (greedy_cost / BLOCK_LIMIT) * 100
# dp_util = (dp_cost / BLOCK_LIMIT) * 100

# st.write(f"Greedy Revenue: {greedy_fee}")
# st.write(f"DP Revenue: {dp_fee}")
# st.write(f"Revenue Gap: {dp_fee - greedy_fee}")

# st.write(f"Greedy Utilization: {greedy_util:.2f}%")
# st.write(f"DP Utilization: {dp_util:.2f}%")

# st.write(f"Greedy Runtime: {greedy_time:.6f} seconds")
# st.write(f"DP Runtime: {dp_time:.6f} seconds")

# # --------------------------
# # SHOW SELECTED TXs
# # --------------------------
# st.subheader("Selected Transactions (Current Selection)")

# if selected_txs:
#     for tx in selected_txs:
#         st.write(
#             f"TX {tx.tx_id} | Fee: {tx.fee} | Gas: {tx.gas} | "
#             f"Proof: {tx.proof_size} | Cost: {tx.effective_cost}"
#         )
# else:
#     st.write("No transactions selected.")




#============================================================
#Version 2
# import copy
# import time
# import streamlit as st

# from mempool_generator import generate_mempool
# from merkle_cost_model import assign_merkle_proof_cost
# from block_builder_dp import build_block_dp

# # --------------------------
# # CONFIG
# # --------------------------
# NUM_TRANSACTIONS = 50
# BLOCK_LIMIT = 1000

# # --------------------------
# # TITLE
# # --------------------------
# st.title("Blockchain Block Allocation Dashboard")
# st.markdown("Compare transaction selection under different Merkle proof models.")

# # --------------------------
# # PROOF MODEL SELECTOR
# # --------------------------
# proof_model = st.selectbox(
#     "Select Merkle Proof Model",
#     ["standard", "cached", "batch"]
# )

# # --------------------------
# # INIT SESSION STATE
# # --------------------------
# if "base_mempool" not in st.session_state:
#     st.session_state.base_mempool = generate_mempool(NUM_TRANSACTIONS)

# if "selected_ids" not in st.session_state:
#     st.session_state.selected_ids = []

# if "warning_msg" not in st.session_state:
#     st.session_state.warning_msg = ""

# if "last_runtime" not in st.session_state:
#     st.session_state.last_runtime = None

# if "last_algo" not in st.session_state:
#     st.session_state.last_algo = "Manual"

# if "last_model" not in st.session_state:
#     st.session_state.last_model = proof_model

# # --------------------------
# # KEEP SAME MEMPOOL, CHANGE ONLY PROOF MODEL
# # --------------------------
# if "mempool" not in st.session_state or st.session_state.last_model != proof_model:
#     mempool = copy.deepcopy(st.session_state.base_mempool)
#     assign_merkle_proof_cost(mempool, model=proof_model)
#     st.session_state.mempool = mempool
#     st.session_state.selected_ids = []
#     st.session_state.warning_msg = ""
#     st.session_state.last_runtime = None
#     st.session_state.last_algo = "Manual"
#     st.session_state.last_model = proof_model

# mempool = st.session_state.mempool

# # --------------------------
# # HELPER: GREEDY SELECTION
# # --------------------------
# def run_greedy(mempool, block_limit):
#     sorted_txs = sorted(
#         mempool,
#         key=lambda tx: tx.fee / tx.effective_cost,
#         reverse=True
#     )

#     selected = []
#     current_cost = 0

#     for tx in sorted_txs:
#         if current_cost + tx.effective_cost <= block_limit:
#             selected.append(tx)
#             current_cost += tx.effective_cost

#     return selected

# # --------------------------
# # BUTTONS
# # --------------------------
# col1, col2, col3 = st.columns(3)

# with col1:
#     if st.button("Run Greedy Selection"):
#         start = time.time()
#         selected = run_greedy(mempool, BLOCK_LIMIT)
#         end = time.time()

#         st.session_state.selected_ids = [tx.tx_id for tx in selected]
#         st.session_state.warning_msg = ""
#         st.session_state.last_runtime = end - start
#         st.session_state.last_algo = "Greedy"
#         st.rerun()

# with col2:
#     if st.button("Run Optimal (DP)"):
#         start = time.time()
#         selected = build_block_dp(mempool, BLOCK_LIMIT)
#         end = time.time()

#         st.session_state.selected_ids = [tx.tx_id for tx in selected]
#         st.session_state.warning_msg = ""
#         st.session_state.last_runtime = end - start
#         st.session_state.last_algo = "DP (Optimal)"
#         st.rerun()

# with col3:
#     if st.button("Clear Selection"):
#         st.session_state.selected_ids = []
#         st.session_state.warning_msg = ""
#         st.session_state.last_runtime = None
#         st.session_state.last_algo = "Manual"
#         st.rerun()

# # --------------------------
# # INFO PANEL
# # --------------------------
# st.info(f"Current algorithm: {st.session_state.last_algo}")

# if st.session_state.last_runtime is not None:
#     st.write(f"Execution Time: {st.session_state.last_runtime:.6f} seconds")

# # --------------------------
# # MEMPOOL DISPLAY
# # --------------------------
# st.subheader("Mempool")

# current_selected = [
#     tx for tx in mempool if tx.tx_id in st.session_state.selected_ids
# ]

# current_cost = sum(tx.effective_cost for tx in current_selected)

# for tx in mempool:
#     col1, col2 = st.columns([1, 6])

#     is_selected = tx.tx_id in st.session_state.selected_ids

#     with col1:
#         checked = st.checkbox(
#             "",
#             value=is_selected,
#             key=f"tx_{tx.tx_id}"
#         )

#     with col2:
#         st.write(
#             f"TX {tx.tx_id} | Gas: {tx.gas} | Fee: {tx.fee} | "
#             f"Proof: {tx.proof_size} | Cost: {tx.effective_cost}"
#         )

#     if checked and not is_selected:
#         if current_cost + tx.effective_cost > BLOCK_LIMIT:
#             st.session_state.warning_msg = "Cannot add transaction: Block limit exceeded."
#             st.rerun()
#         else:
#             st.session_state.selected_ids.append(tx.tx_id)
#             current_cost += tx.effective_cost
#             st.session_state.warning_msg = ""

#     elif not checked and is_selected:
#         st.session_state.selected_ids.remove(tx.tx_id)
#         current_cost -= tx.effective_cost
#         st.session_state.warning_msg = ""

# # --------------------------
# # WARNING
# # --------------------------
# if st.session_state.warning_msg:
#     st.warning(st.session_state.warning_msg)

# # --------------------------
# # CURRENT SELECTION METRICS
# # --------------------------
# selected_txs = [
#     tx for tx in mempool if tx.tx_id in st.session_state.selected_ids
# ]

# total_fee = sum(tx.fee for tx in selected_txs)
# total_gas = sum(tx.gas for tx in selected_txs)
# total_proof = sum(tx.proof_size for tx in selected_txs)
# total_cost = total_gas + total_proof
# utilization = (total_cost / BLOCK_LIMIT) * 100

# st.subheader("Current Block Metrics")
# st.write(f"Transactions Selected: {len(selected_txs)}")
# st.write(f"Total Fee: {total_fee}")
# st.write(f"Total Gas: {total_gas}")
# st.write(f"Total Proof Cost: {total_proof}")
# st.write(f"Block Utilization: {total_cost}/{BLOCK_LIMIT} ({utilization:.2f}%)")

# if total_cost > BLOCK_LIMIT:
#     status_type = "error"
#     status_msg = "Cannot add transaction: Block limit exceeded."
# else:
#     status_type = "success"
#     status_msg = "Block within limit."

# if status_type == "error":
#     st.error(status_msg)
# else:
#     st.success(status_msg)

# # --------------------------
# # COMPARISON PANEL
# # --------------------------
# st.subheader("Greedy vs DP Comparison")

# greedy_start = time.time()
# greedy_selected = run_greedy(mempool, BLOCK_LIMIT)
# greedy_time = time.time() - greedy_start

# dp_start = time.time()
# dp_selected = build_block_dp(mempool, BLOCK_LIMIT)
# dp_time = time.time() - dp_start

# greedy_fee = sum(tx.fee for tx in greedy_selected)
# dp_fee = sum(tx.fee for tx in dp_selected)

# greedy_cost = sum(tx.effective_cost for tx in greedy_selected)
# dp_cost = sum(tx.effective_cost for tx in dp_selected)

# greedy_util = (greedy_cost / BLOCK_LIMIT) * 100
# dp_util = (dp_cost / BLOCK_LIMIT) * 100

# st.write(f"Greedy Revenue: {greedy_fee}")
# st.write(f"DP Revenue: {dp_fee}")
# st.write(f"Revenue Gap: {dp_fee - greedy_fee}")

# st.write(f"Greedy Utilization: {greedy_util:.2f}%")
# st.write(f"DP Utilization: {dp_util:.2f}%")

# st.write(f"Greedy Runtime: {greedy_time:.6f} seconds")
# st.write(f"DP Runtime: {dp_time:.6f} seconds")

# # --------------------------
# # SHOW SELECTED TXs
# # --------------------------
# st.subheader("Selected Transactions (Current Selection)")

# if selected_txs:
#     for tx in selected_txs:
#         st.write(
#             f"TX {tx.tx_id} | Fee: {tx.fee} | Gas: {tx.gas} | "
#             f"Proof: {tx.proof_size} | Cost: {tx.effective_cost}"
#         )
# else:
#     st.write("No transactions selected.")




#============================================================
#Version 1
# import streamlit as st
# from mempool_generator import generate_mempool
# from merkle_cost_model import assign_merkle_proof_cost

# # --------------------------
# # CONFIG
# # --------------------------
# NUM_TRANSACTIONS = 50
# BLOCK_LIMIT = 1000

# # --------------------------
# # INIT STATE
# # --------------------------
# if "mempool" not in st.session_state:
#     mempool = generate_mempool(NUM_TRANSACTIONS)
#     assign_merkle_proof_cost(mempool)
#     st.session_state.mempool = mempool

# if "selected_ids" not in st.session_state:
#     st.session_state.selected_ids = []

# if "warning_msg" not in st.session_state:
#     st.session_state.warning_msg = ""

# mempool = st.session_state.mempool

# # --------------------------
# # TITLE
# # --------------------------
# st.title("Blockchain Block Allocation Dashboard")

# st.markdown("Select transactions to include in block")

# # --------------------------
# # BUTTONS
# # --------------------------
# col1, col2 = st.columns(2)

# with col1:
#     if st.button("Run Greedy Selection"):
#         sorted_txs = sorted(
#             mempool,
#             key=lambda tx: tx.fee / tx.effective_cost,
#             reverse=True
#         )

#         selected_ids = []
#         current_cost = 0

#         for tx in sorted_txs:
#             if current_cost + tx.effective_cost <= BLOCK_LIMIT:
#                 selected_ids.append(tx.tx_id)
#                 current_cost += tx.effective_cost

#         st.session_state.selected_ids = selected_ids
#         st.session_state.warning_msg = ""
#         st.rerun()

# with col2:
#     if st.button("Clear Selection"):
#         st.session_state.selected_ids = []
#         st.session_state.warning_msg = ""
#         st.rerun()

# # --------------------------
# # MEMPOOL DISPLAY
# # --------------------------
# st.subheader("Mempool")

# current_selected = [
#     tx for tx in mempool if tx.tx_id in st.session_state.selected_ids
# ]

# current_cost = sum(tx.effective_cost for tx in current_selected)

# for tx in mempool:
#     col1, col2 = st.columns([1, 6])

#     is_selected = tx.tx_id in st.session_state.selected_ids

#     with col1:
#         checked = st.checkbox(
#             "",
#             value=is_selected,
#             key=f"tx_{tx.tx_id}"
#         )

#     with col2:
#         st.write(
#             f"TX {tx.tx_id} | Gas: {tx.gas} | Fee: {tx.fee} | "
#             f"Proof: {tx.proof_size} | Cost: {tx.effective_cost}"
#         )

#     # --------------------------
#     # SELECTION LOGIC
#     # --------------------------
#     if checked and not is_selected:
#         # Try adding transaction
#         if current_cost + tx.effective_cost > BLOCK_LIMIT:
#             st.session_state.warning_msg = "⚠️ Cannot add transaction: Block limit exceeded!"
#         else:
#             st.session_state.selected_ids.append(tx.tx_id)
#             current_cost += tx.effective_cost
#             st.session_state.warning_msg = ""

#     elif not checked and is_selected:
#         st.session_state.selected_ids.remove(tx.tx_id)
#         current_cost -= tx.effective_cost
#         st.session_state.warning_msg = ""

# # --------------------------
# # WARNING MESSAGE
# # --------------------------
# if st.session_state.warning_msg:
#     st.warning(st.session_state.warning_msg)

# # --------------------------
# # SELECTED TXs
# # --------------------------
# selected_txs = [
#     tx for tx in mempool if tx.tx_id in st.session_state.selected_ids
# ]

# # --------------------------
# # METRICS
# # --------------------------
# total_fee = sum(tx.fee for tx in selected_txs)
# total_gas = sum(tx.gas for tx in selected_txs)
# total_proof = sum(tx.proof_size for tx in selected_txs)
# total_cost = total_gas + total_proof

# utilization = (total_cost / BLOCK_LIMIT) * 100

# # --------------------------
# # DISPLAY METRICS
# # --------------------------
# st.subheader("Block Metrics")

# st.write(f"Transactions Selected: {len(selected_txs)}")
# st.write(f"Total Fee: {total_fee}")
# st.write(f"Total Gas: {total_gas}")
# st.write(f"Total Proof Cost: {total_proof}")
# st.write(f"Block Utilization: {total_cost}/{BLOCK_LIMIT} ({utilization:.2f}%)")

# # --------------------------
# # STATUS
# # --------------------------
# if total_cost > BLOCK_LIMIT:
#     st.error("⚠️ Block limit exceeded!")
# else:
#     st.success("Block within limit")