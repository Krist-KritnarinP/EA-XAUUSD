import json

with open("v632_parsed_trades.json", "r") as f:
    data = json.load(f)

trades = data["trades"]

print("="*75)
print("LOT CAP IMPACT SIMULATION (Gold Sniper v6.3.2 Backtest Trades)")
print("="*75)

for cap in [None, 0.20, 0.15, 0.12, 0.10, 0.08]:
    bal = 1000.0
    max_bal = bal
    max_dd_usd = 0.0
    max_dd_pct = 0.0
    
    for t in trades:
        lots = t["lots"]
        if cap is not None and lots > cap:
            lots = cap
            
        diff = t["diff_usd"]
        pnl = diff * lots * 100.0
        bal += pnl
        if bal > max_bal:
            max_bal = bal
        dd_u = max_bal - bal
        dd_p = (dd_u / max_bal) * 100.0 if max_bal > 0 else 0.0
        if dd_u > max_dd_usd:
            max_dd_usd = dd_u
        if dd_p > max_dd_pct:
            max_dd_pct = dd_p
        
    cap_str = f"Cap: {cap} lots" if cap else "Uncapped (Dynamic)"
    roi = ((bal - 1000.0) / 1000.0) * 100.0
    print(f"{cap_str:22s} | Final: ${bal:8.2f} | Net: ${bal-1000:+8.2f} ({roi:6.1f}%) | Max DD: ${max_dd_usd:7.2f} ({max_dd_pct:5.2f}%)")

print("="*75)

# Detailed analysis of trades that exceeded 0.15 lots:
print("\nTRADES THAT EXCEEDED 0.15 LOTS IN THE TEST:")
over_trades = [t for t in trades if t["lots"] > 0.15]
print(f"Total trades with lots > 0.15: {len(over_trades)}")
for t in over_trades:
    print(f"Ticket #{t['ticket']:2d} | Time: {t['open_time']} | Engine: {t['engine']:20s} | Lots: {t['lots']:.2f} | PnL: ${t['pnl']:+8.2f} | Reason: {t.get('close_reason')}")
