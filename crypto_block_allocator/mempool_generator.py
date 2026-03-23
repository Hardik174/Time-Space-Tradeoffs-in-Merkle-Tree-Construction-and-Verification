import random
from transaction import Transaction


def generate_mempool(num_transactions):
    mempool = []

    for i in range(num_transactions):
        gas = random.randint(20, 120)
        fee = random.randint(50, 300)

        tx = Transaction(i, gas, fee)
        mempool.append(tx)

    return mempool