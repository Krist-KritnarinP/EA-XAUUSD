import json

path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_v2_5_detailed_trades.json"
trades = json.load(open(path, "r", encoding="utf-8"))

# Check all trades:
# 4.2 Full TP:
full_tp = [t for t in trades if t['close_reason'] == 'TAKE_PROFIT']

# 4.3 Breakeven hit (SL was moved to open_price + 30 pts):
# For BUY: close_price == open_price + 0.30 and close_reason == STOP_LOSS
# For SELL: close_price == open_price - 0.30 and close_reason == STOP_LOSS
be_hits = []
for t in trades:
    if t['close_reason'] == 'STOP_LOSS':
        if t['type'] == 'BUY' and abs(t['close_price'] - (t['open_price'] + 0.30)) < 0.05:
            be_hits.append(t)
        elif t['type'] == 'SELL' and abs(t['close_price'] - (t['open_price'] - 0.30)) < 0.05:
            be_hits.append(t)

# 4.4 Structural Bailout:
bailouts = [t for t in trades if t['close_reason'] == 'STRUCTURAL_BAILOUT']

# Direct full SL losses:
direct_losses = [t for t in trades if t['close_reason'] == 'STOP_LOSS' and t['profit_usd'] < 0]

print(f"Total Trades: {len(trades)}")
print(f"4.2 Full TP Hits (1:3.5 RR): {len(full_tp)} trades | Total Profit: ${sum(t['profit_usd'] for t in full_tp):,.2f}")
print(f"4.3 Breakeven Hits (+30 pts buffer lock): {len(be_hits)} trades | Total Profit: ${sum(t['profit_usd'] for t in be_hits):,.2f}")
print(f"4.4 Structural Bailout Exits: {len(bailouts)} trades | Total Profit: ${sum(t['profit_usd'] for t in bailouts):,.2f}")
print(f"Direct Full SL: {len(direct_losses)} trades | Total Loss: ${sum(t['profit_usd'] for t in direct_losses):,.2f}")
print("--- Sample Breakeven trades ---")
for b in be_hits[:5]:
    print(f"  Ticket #{b['ticket']} {b['type']} Open: {b['open_price']} Close: {b['close_price']} (diff: {b['close_price']-b['open_price']:+.2f}) Profit: ${b['profit_usd']:.2f}")
