# -*- coding: utf-8 -*-
with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\analyze_latest_run.py", "r") as f:
    code = f.read()

# Let's inspect the Sniper Runner trades in the latest run
import json
with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\forensic_trades.json", "r") as f:
    old_trades = json.load(f)

old_snipers = [t for t in old_trades if t.get("engine") == "SNIPER RUNNER"]
print(f"Old run snipers: {len(old_snipers)}")
old_sniper_sells = [t for t in old_snipers if t["type"] == "SELL"]
old_sniper_buys = [t for t in old_snipers if t["type"] == "BUY"]
print(f"Old sniper SELL: {len(old_sniper_sells)} trades, PnL=${sum(t['pnl'] for t in old_sniper_sells):.2f}")
print(f"Old sniper BUY:  {len(old_sniper_buys)} trades, PnL=${sum(t['pnl'] for t in old_sniper_buys):.2f}")
