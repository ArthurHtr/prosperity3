from itertools import product
from tqdm import tqdm

# Define the exchange rates as given in the table.
# Keys: 'Sb' = Snowballs, 'P' = Pizza's, 'N' = Silicon Nuggets, 'S' = SeaShells.
rates = {
    "Sb": {"Sb": 1.00, "P": 1.45, "N": 0.52, "S": 0.72},
    "P":  {"Sb": 0.70, "P": 1.00, "N": 0.31, "S": 0.48},
    "N":  {"Sb": 1.95, "P": 3.10, "N": 1.00, "S": 1.49},
    "S":  {"Sb": 1.34, "P": 1.98, "N": 0.64, "S": 1.00},
}

# Starting capital in SeaShells
starting_capital = 500000

# Allowed currencies
currencies = ["Sb", "P", "N", "S"]

# Function to compute the final value given a trade sequence.
# sequence is a list of currency codes, e.g. ["S", "P", "Sb", "S"]
def compute_value(sequence):
    value = starting_capital
    for i in range(len(sequence) - 1):
        frm = sequence[i]
        to = sequence[i + 1]
        rate = rates[frm][to]
        value *= rate
    return value

# We need sequences that start with "S" and end with "S". 
# Allowed number of trades (conversions) is between 2 and 5.
# That means the sequence length is from 3 to 6 (e.g. [S, X, S] -> 2 trades).
min_trades = 2
max_trades = 5

best_sequence = None
best_value = 0

# Enumerate for each valid sequence length.
# The total number of nodes is trades + 1.
for num_trades in tqdm(range(min_trades, max_trades + 1)):
    seq_length = num_trades + 1
    # The first and last must be "S".
    # For the intermediate positions, choose any currency from the allowed set.
    # We use product to iterate over all possibilities for the intermediate nodes.
    for middle in product(currencies, repeat=seq_length - 2):
        sequence = ["S"] + list(middle) + ["S"]
        final_value = compute_value(sequence)
        if final_value > best_value:
            best_value = final_value
            best_sequence = sequence

# Output the result:
print("Best trading sequence:", " -> ".join(best_sequence))
print("Final amount in SeaShells: {:.2f}".format(best_value))
print("Profit: {:.2f} SeaShells ({:.2f}% return)".format(
    best_value - starting_capital,
    (best_value / starting_capital - 1) * 100
))
