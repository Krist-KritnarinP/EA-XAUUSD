import json

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_sniper_parsed_trades.json', 'r') as f:
    trades = json.load(f)

print(f"Total POI v0 trades (Full Day 08:00-20:30): {len(trades)}")

# Simulate starting with $2,000, 2.0% risk compounding, Max Lot 1.50, on all 327 trades
bal = 2000.0
peak = bal
max_dd = 0.0
max_dd_pct = 0.0
monthly_gains = {}

for t in trades:
    sl_pts = t['trigger_info']['sl_pts'] if t['trigger_info'] else 300
    if sl_pts <= 100: sl_pts = 250
    
    risk_amt = bal * 0.02
    lot = risk_amt / (sl_pts * 1.0)
    if lot > 1.50: lot = 1.50
    if lot < 0.01: lot = 0.01
    
    pts = t['pnl'] / (t['lots'] * 100.0)
    pnl = pts * lot * 100.0
    
    bal += pnl
    if bal > peak: peak = bal
    dd = peak - bal
    dd_pct = (dd / peak) * 100.0
    if dd > max_dd: max_dd = dd
    if dd_pct > max_dd_pct: max_dd_pct = dd_pct
    
    m = t['open_time'][:7]
    if m not in monthly_gains: monthly_gains[m] = 0.0
    monthly_gains[m] += pnl

net = bal - 2000.0
print(f"Initial Balance: USD 2,000.00")
print(f"End Balance: USD {bal:.2f}")
print(f"Total Net Profit: USD {net:.2f}")
print(f"Average Monthly Profit: USD {net/12.0:.2f}")
print(f"Max Drawdown: USD {max_dd:.2f} ({max_dd_pct:.1f}%)")
print("\nMonthly PnL breakdown:")
for m, p in sorted(monthly_gains.items()):
    print(f"  {m}: USD {p:.2f}")
