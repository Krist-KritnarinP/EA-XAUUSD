import json

path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_v2_5_detailed_trades.json"
trades = json.load(open(path, "r", encoding="utf-8"))

bailouts = [t for t in trades if t.get("close_reason") == "STRUCTURAL_BAILOUT"]
print(f"Total Trades in BT: {len(trades)}")
print(f"Total Structural Bailouts in BT: {len(bailouts)}")

for b in bailouts:
    print(f"Ticket #{b['ticket']} | {b['open_time']} -> {b['close_time']} | {b['type']} | Lots: {b['lots']} | Open: {b['open_price']} | Close: {b['close_price']} | Profit: ${b['profit_usd']:.2f} | Reason: {b['close_reason']}")
