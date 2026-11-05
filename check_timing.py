# -*- coding: utf-8 -*-
import json

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\forensic_trades.json", "r") as f:
    trades = json.load(f)

# Look at London Sniper trades by hour & minute
snipers = [t for t in trades if t.get("engine") == "SNIPER RUNNER"]
print(f"Total snipers: {len(snipers)}")

before_0900_buys = [t for t in snipers if t["type"] == "BUY" and int(t["open_time"][11:13]) == 8 and int(t["open_time"][14:16]) < 45]
after_0900_buys = [t for t in snipers if t["type"] == "BUY" and (int(t["open_time"][11:13]) > 8 or int(t["open_time"][14:16]) >= 45)]

print(f"London BUYs before 08:45: {len(before_0900_buys)} trades")
print(f"  Wins: {len([t for t in before_0900_buys if t['pnl'] > 0])}, Losses: {len([t for t in before_0900_buys if t['pnl'] <= 0])}")
print(f"  PnL: ${sum(t['pnl'] for t in before_0900_buys):.2f}")

print(f"\nLondon BUYs at/after 08:45: {len(after_0900_buys)} trades")
print(f"  Wins: {len([t for t in after_0900_buys if t['pnl'] > 0])}, Losses: {len([t for t in after_0900_buys if t['pnl'] <= 0])}")
print(f"  PnL: ${sum(t['pnl'] for t in after_0900_buys):.2f}")

before_0900_sells = [t for t in snipers if t["type"] == "SELL" and int(t["open_time"][11:13]) == 8 and int(t["open_time"][14:16]) < 45]
after_0900_sells = [t for t in snipers if t["type"] == "SELL" and (int(t["open_time"][11:13]) > 8 or int(t["open_time"][14:16]) >= 45)]

print(f"\nLondon SELLs before 08:45: {len(before_0900_sells)} trades")
print(f"  Wins: {len([t for t in before_0900_sells if t['pnl'] > 0])}, Losses: {len([t for t in before_0900_sells if t['pnl'] <= 0])}")
print(f"  PnL: ${sum(t['pnl'] for t in before_0900_sells):.2f}")

print(f"\nLondon SELLs at/after 08:45: {len(after_0900_sells)} trades")
print(f"  Wins: {len([t for t in after_0900_sells if t['pnl'] > 0])}, Losses: {len([t for t in after_0900_sells if t['pnl'] <= 0])}")
print(f"  PnL: ${sum(t['pnl'] for t in after_0900_sells):.2f}")
