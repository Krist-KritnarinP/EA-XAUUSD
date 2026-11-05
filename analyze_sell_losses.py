# -*- coding: utf-8 -*-
import json

# Let's inspect all SELL trades in v642 that lost money
with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v642_all_trades.json", "r", encoding="utf-8") as f:
    trades = json.load(f)

losing_sells = [t for t in trades if t["type"] == "SELL" and t["profit"] < 0]
print(f"Total losing SELLs in v6.4.2: {len(losing_sells)} trades, total loss: ${sum(t['profit'] for t in losing_sells):.2f}")

# Group by hour
from collections import defaultdict
hour_losses = defaultdict(lambda: {"count": 0, "loss": 0.0})
for t in losing_sells:
    hr = t["open_time"][11:13]
    hour_losses[hr]["count"] += 1
    hour_losses[hr]["loss"] += t["profit"]

print("\nLosing SELLs by Hour:")
for hr in sorted(hour_losses.keys()):
    st = hour_losses[hr]
    print(f"Hour {hr}: {st['count']} trades, Loss: ${st['loss']:.2f}")

# Check 08:00 - 08:45 trades
pre_open_losses = [t for t in losing_sells if t["open_time"][11:16] < "08:45" and t["open_time"][11:13] == "08"]
print(f"\nPre-08:45 London SELL losses: {len(pre_open_losses)} trades, Loss: ${sum(t['profit'] for t in pre_open_losses):.2f}")
for t in pre_open_losses:
    print(f"  Ticket #{t['ticket']} at {t['open_time']}: ${t['profit']:.2f}")
