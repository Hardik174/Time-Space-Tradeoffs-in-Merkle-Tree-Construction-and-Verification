import streamlit as st
from mempool_generator import generate_mempool
from merkle_cost_model import assign_merkle_proof_cost

# --------------------------
# CONFIG
# --------------------------
NUM_TRANSACTIONS = 50
BLOCK_LIMIT = 1000

# --------------------------
# INIT STATE
# --------------------------
if "mempool" not in st.session_state:
    mempool = generate_mempool(NUM_TRANSACTIONS)
    assign_merkle_proof_cost(mempool)
    st.session_state.mempool = mempool

if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = []

if "warning_msg" not in st.session_state:
    st.session_state.warning_msg = ""

mempool = st.session_state.mempool

# --------------------------
# TITLE
# --------------------------
st.title("Blockchain Block Allocation Dashboard")

st.markdown("Select transactions to include in block")

# --------------------------
# BUTTONS
# --------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("Run Greedy Selection"):
        sorted_txs = sorted(
            mempool,
            key=lambda tx: tx.fee / tx.effective_cost,
            reverse=True
        )

        selected_ids = []
        current_cost = 0

        for tx in sorted_txs:
            if current_cost + tx.effective_cost <= BLOCK_LIMIT:
                selected_ids.append(tx.tx_id)
                current_cost += tx.effective_cost

        st.session_state.selected_ids = selected_ids
        st.session_state.warning_msg = ""
        st.rerun()

with col2:
    if st.button("Clear Selection"):
        st.session_state.selected_ids = []
        st.session_state.warning_msg = ""
        st.rerun()

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
            "",
            value=is_selected,
            key=f"tx_{tx.tx_id}"
        )

    with col2:
        st.write(
            f"TX {tx.tx_id} | Gas: {tx.gas} | Fee: {tx.fee} | "
            f"Proof: {tx.proof_size} | Cost: {tx.effective_cost}"
        )

    # --------------------------
    # SELECTION LOGIC
    # --------------------------
    if checked and not is_selected:
        # Try adding transaction
        if current_cost + tx.effective_cost > BLOCK_LIMIT:
            st.session_state.warning_msg = "⚠️ Cannot add transaction: Block limit exceeded!"
        else:
            st.session_state.selected_ids.append(tx.tx_id)
            current_cost += tx.effective_cost
            st.session_state.warning_msg = ""

    elif not checked and is_selected:
        st.session_state.selected_ids.remove(tx.tx_id)
        current_cost -= tx.effective_cost
        st.session_state.warning_msg = ""

# --------------------------
# WARNING MESSAGE
# --------------------------
if st.session_state.warning_msg:
    st.warning(st.session_state.warning_msg)

# --------------------------
# SELECTED TXs
# --------------------------
selected_txs = [
    tx for tx in mempool if tx.tx_id in st.session_state.selected_ids
]

# --------------------------
# METRICS
# --------------------------
total_fee = sum(tx.fee for tx in selected_txs)
total_gas = sum(tx.gas for tx in selected_txs)
total_proof = sum(tx.proof_size for tx in selected_txs)
total_cost = total_gas + total_proof

utilization = (total_cost / BLOCK_LIMIT) * 100

# --------------------------
# DISPLAY METRICS
# --------------------------
st.subheader("Block Metrics")

st.write(f"Transactions Selected: {len(selected_txs)}")
st.write(f"Total Fee: {total_fee}")
st.write(f"Total Gas: {total_gas}")
st.write(f"Total Proof Cost: {total_proof}")
st.write(f"Block Utilization: {total_cost}/{BLOCK_LIMIT} ({utilization:.2f}%)")

# --------------------------
# STATUS
# --------------------------
if total_cost > BLOCK_LIMIT:
    st.error("⚠️ Block limit exceeded!")
else:
    st.success("Block within limit")