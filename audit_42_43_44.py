import json

path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_v2_5_detailed_trades.json"
trades = json.load(open(path, "r", encoding="utf-8"))

total_trades = len(trades)
tp_hits = [t for t in trades if t.get("close_reason") == "TAKE_PROFIT"]
be_hits = [t for t in trades if t.get("close_reason") == "STOP_LOSS" and len(t.get("modifications", [])) > 0]
direct_sl_hits = [t for t in trades if t.get("close_reason") == "STOP_LOSS" and len(t.get("modifications", [])) == 0]
bailout_hits = [t for t in trades if t.get("close_reason") == "STRUCTURAL_BAILOUT"]
be_triggered_total = [t for t in trades if len(t.get("modifications", [])) > 0]

print(f"Total Trades: {total_trades}")
print(f"1) 4.2 Hit Full TP (1:3.5 RR): {len(tp_hits)} trades (Total Profit: ${sum(t['profit_usd'] for t in tp_hits):,.2f})")
print(f"2) 4.3 Breakeven Triggered (+1.8R): {len(be_triggered_total)} trades")
print(f"   - Of which reached Full TP (3.5R): {len([t for t in be_triggered_total if t['close_reason'] == 'TAKE_PROFIT'])} trades")
print(f"   - Of which returned to BE (+30 pts buffer locked): {len(be_hits)} trades (Total Profit: ${sum(t['profit_usd'] for t in be_hits):,.2f})")
print(f"3) 4.4 Structural Bailout Cut: {len(bailout_hits)} trades (Total Profit: ${sum(t['profit_usd'] for t in bailout_hits):,.2f})")
print(f"4) Direct Full SL: {len(direct_sl_hits)} trades (Total Loss: ${sum(t['profit_usd'] for t in direct_sl_hits):,.2f})")
