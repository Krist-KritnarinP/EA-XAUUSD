import json

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v623x3_official_forensic.json', 'r', encoding='utf-8') as f:
    trades = json.load(f)

monthly = {}
for t in trades:
    m = t['open_time'][:7]
    if m not in monthly:
        monthly[m] = {'count': 0, 'wins': 0, 'profit_usd': 0.0, 'points': 0.0, 'lots': []}
    monthly[m]['count'] += 1
    if t['profit'] > 0:
        monthly[m]['wins'] += 1
    monthly[m]['profit_usd'] += t['profit']
    monthly[m]['lots'].append(t['lots'])
    
    # Points
    pts = (t['close_price'] - t['open_price']) if t['type'].upper() == 'BUY' else (t['open_price'] - t['close_price'])
    monthly[m]['points'] += pts

print("Month    | Trades | WR%    | Profit USD    | Points (USD/oz) | Avg Lot | Max Lot")
print("-" * 75)
for m, data in sorted(monthly.items()):
    wr = (data['wins'] / data['count'] * 100) if data['count'] > 0 else 0
    avg_lot = sum(data['lots']) / len(data['lots'])
    max_lot = max(data['lots'])
    print(f"{m}  | {data['count']:6d} | {wr:5.1f}% | {data['profit_usd']:12.2f} | {data['points']:14.2f} | {avg_lot:7.2f} | {max_lot:7.2f}")

# Also simulate Fixed Lot 0.10
print("\n--- SIMULATION: Fixed Lot 0.10 (No Compounding Distortion) ---")
print("Month    | Trades | Fixed 0.10 Profit ($) | Cumulative ($)")
cum = 0.0
for m, data in sorted(monthly.items()):
    m_fixed = 0.0
    for t in trades:
        if t['open_time'][:7] == m:
            pts = (t['close_price'] - t['open_price']) if t['type'].upper() == 'BUY' else (t['open_price'] - t['close_price'])
            # 0.10 lot on gold: 1 point = $10.00
            m_fixed += pts * 10.0
    cum += m_fixed
    print(f"{m}  | {data['count']:6d} | {m_fixed:18.2f} | {cum:14.2f}")
