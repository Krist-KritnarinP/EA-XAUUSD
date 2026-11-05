# -*- coding: utf-8 -*-
import json

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v642_all_trades.json", "r", encoding="utf-8") as f:
    trades = json.load(f)

# Let's inspect the 4 big losers in Oct 2026:
# #127: 2026.10.08 09:15
# #129: 2026.10.21 17:20
# #130: 2026.10.22 08:50
# #134: 2026.10.27 10:15

print("Inspecting 4 big losers:")
for t in trades:
    if t["ticket"] in [127, 129, 130, 134]:
        print(f"Ticket #{t['ticket']} at {t['open_time']}: Lots: {t['lots']}, Open: {t['open_price']}, SL: {t['sl']}, Profit: ${t['profit']}")
