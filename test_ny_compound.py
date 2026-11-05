import json

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_sniper_parsed_trades.json', 'r') as f:
    trades = json.load(f)

# Filter for New York Session trades (15:00 - 20:30 server time)
ny_trades = []
for t in trades:
    h = int(t['open_time'][11:13])
    m = int(t['open_time'][14:16])
    if 15 <= h < 20 or (h == 20 and m <= 30):
        t['month_str'] = t['open_time'][:7]
        ny_trades.append(t)

print(f"Total New York Trades: {len(ny_trades)}")

# Simulate starting with $2,000 and 2.0% risk compounding
bal = 2000.0
peak = bal
max_dd = 0.0
max_dd_pct = 0.0
monthly_gains = {}

for t in ny_trades:
    sl_pts = t['trigger_info']['sl_pts'] if t['trigger_info'] else 300
    if sl_pts <= 100: sl_pts = 250
    
    # 2.0% risk per trade
    risk_amt = bal * 0.02
    lot = risk_amt / (sl_pts * 1.0)
    if lot > 2.0: lot = 2.0
    if lot < 0.01: lot = 0.01
    
    pts = t['pnl'] / (t['lots'] * 100.0)
    pnl = pts * lot * 100.0
    
    bal += pnl
    if bal > peak: peak = bal
    dd = peak - bal
    dd_pct = (dd / peak) * 100.0
    if dd > max_dd: max_dd = dd
    if dd_pct > max_dd_pct: max_dd_pct = dd_pct
    
    m = t['month_str']
    if m not in monthly_gains: monthly_gains[m] = 0.0
    monthly_gains[m] += pnl

net = bal - 2000.0
print(f"Initial: USD 2,000.00")
print(f"End Balance: USD {bal:.2f}")
print(f"Total Net Profit: USD {net:.2f}")
print(f"Average Monthly Profit: USD {net/12.0:.2f}")
print(f"Max Drawdown: USD {max_dd:.2f} ({max_dd_pct:.1f}%)")
print("\nMonthly PnL breakdown:")
for m, p in sorted(monthly_gains.items()):
    print(f"  {m}: USD {p:.2f}")
