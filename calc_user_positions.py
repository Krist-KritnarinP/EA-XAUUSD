# Calculate user's exact positions, floating drawdown, average entry, and probabilities
current_price = 3875.61

positions = [
    {"ticket": 63533196, "type": "BUY", "lots": 0.02, "entry": 3964.94, "tp": None, "sl": None},
    {"ticket": 63518512, "type": "BUY", "lots": 0.01, "entry": 4014.26, "tp": 4020.0, "sl": None},
    {"ticket": 63517157, "type": "BUY", "lots": 0.01, "entry": 4027.31, "tp": 4035.0, "sl": None},
    {"ticket": 63540001, "type": "BUY", "lots": 0.01, "entry": 4143.94, "tp": 4150.0, "sl": None},
]

total_lots = sum(p["lots"] for p in positions)
total_cost = sum(p["lots"] * p["entry"] for p in positions)
avg_entry = total_cost / total_lots

floating_pnl = sum((current_price - p["entry"]) * p["lots"] * 100 for p in positions) # Gold contract size is 100 oz
# Note: For XM, 1 lot = 100 oz. 0.01 lot = 1 oz. So $1 move = $1 profit per 0.01 lot.
# Let's verify XM tick value: 0.01 lot * $1.00 = $1.00 USD.
# So floating PnL = sum((current_price - entry) * (lots * 100))

print(f"Total Buy Lots: {total_lots:.2f} lots")
print(f"Volume-Weighted Average Entry (BE Price): ${avg_entry:.2f}")
print(f"Current Price: ${current_price:.2f}")
print(f"Distance to Average Entry: ${avg_entry - current_price:.2f} ({ (avg_entry - current_price)*100:.0f} pts)")
print(f"Total Floating Loss: ${floating_pnl:.2f}")

print("\nDetail per position:")
for p in positions:
    dist = p["entry"] - current_price
    pnl = (current_price - p["entry"]) * (p["lots"] * 100)
    print(f"Ticket #{p['ticket']} | BUY {p['lots']} lots @ ${p['entry']:.2f} | Dist: -${dist:.2f} | Float: ${pnl:.2f}")

# Pending order
print("\nPending Orders:")
print("Ticket #63346005 | SELL LIMIT 0.02 lots @ $4,190.00 | TP: $4,150.00")
