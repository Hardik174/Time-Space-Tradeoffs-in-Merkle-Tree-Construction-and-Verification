def compute_metrics(selected_transactions):

    total_fee = sum(tx.fee for tx in selected_transactions)
    total_gas = sum(tx.gas for tx in selected_transactions)
    total_proof = sum(tx.proof_size for tx in selected_transactions)

    return {
        "transactions_selected": len(selected_transactions),
        "total_fee": total_fee,
        "total_gas": total_gas,
        "total_proof_cost": total_proof
    }