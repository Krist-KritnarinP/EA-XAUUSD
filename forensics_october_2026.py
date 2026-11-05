import struct, json
from datetime import datetime

# 1. Load M15 bars
hst_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst'
bars = []
with open(hst_file, 'rb') as f:
    f.read(148)
    while True:
        data = f.read(60)
        if len(data) < 60: break
        unp = struct.unpack('<QddddQiq', data)
        bars.append({
            'time': datetime.fromtimestamp(unp[0]),
            'open': unp[1],
            'high': unp[2],
            'low': unp[3],
            'close': unp[4]
        })

# Filter October 2026 bars vs October 2025 bars
bars_oct25 = [b for b in bars if b['time'].year == 2025 and b['time'].month == 10]
bars_oct26 = [b for b in bars if b['time'].year == 2026 and b['time'].month == 10]

# Compute ATR and candle ranges
def analyze_month(m_bars, name):
    prices = [b['close'] for b in m_bars]
    ranges = [b['high'] - b['low'] for b in m_bars]
    avg_price = sum(prices) / len(prices) if prices else 0
    avg_m15_range = sum(ranges) / len(ranges) if ranges else 0
    max_m15_range = max(ranges) if ranges else 0
    
    # Daily ranges
    daily_high = {}
    daily_low = {}
    for b in m_bars:
        d = b['time'].date()
        if d not in daily_high or b['high'] > daily_high[d]: daily_high[d] = b['high']
        if d not in daily_low or b['low'] < daily_low[d]: daily_low[d] = b['low']
    daily_ranges = [daily_high[d] - daily_low[d] for d in daily_high]
    avg_d1_range = sum(daily_ranges) / len(daily_ranges) if daily_ranges else 0
    
    print(f"=== {name} FORENSICS ===")
    print(f"Average Gold Price: ${avg_price:.2f}")
    print(f"Average Daily Range (D1 ATR): ${avg_d1_range:.2f}")
    print(f"Average M15 Candle Range: ${avg_m15_range:.2f}")
    print(f"Max Single M15 Candle Range: ${max_m15_range:.2f}")

analyze_month(bars_oct25, "OCTOBER 2025 (Golden Month: +$1,902 to +$2,268)")
print()
analyze_month(bars_oct26, "OCTOBER 2026 (The Bleeding Month: -$942)")

# Now parse the exact 12 trades in October 2026 from 20261101.log
p = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log'
with open(p, 'rb') as f:
    text = f.read().decode('utf-8', errors='replace')

lines = text.splitlines()
indices = [i for i, l in enumerate(lines) if 'Gold_POI_Sniper_Tester_v3' in l and 'loaded successfully' in l]
latest_start = indices[-1] if indices else 0
run_lines = lines[latest_start:]

import re
pat_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v3 GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
pat_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
pat_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')

orders = {}
for l in run_lines:
    m = pat_open.search(l)
    if m:
        t_id = int(m.group(2))
        orders[t_id] = {
            'ticket': t_id,
            'time': m.group(1),
            'type': m.group(3).upper(),
            'lots': float(m.group(4)),
            'open': float(m.group(5)),
            'sl': float(m.group(6)),
            'tp': float(m.group(7)),
            'res': 'OPEN'
        }
    m_tp = pat_tp.search(l)
    if m_tp:
        t_id = int(m_tp.group(2))
        if t_id in orders: orders[t_id]['res'] = 'WIN_TP'
    m_sl = pat_sl.search(l)
    if m_sl:
        t_id = int(m_sl.group(2))
        if t_id in orders: orders[t_id]['res'] = 'LOSS_SL'

oct26_trades = [o for o in orders.values() if o['time'].startswith('2026.10')]
print(f"\nTotal October 2026 Trades Found: {len(oct26_trades)}")
for o in oct26_trades:
    sl_dist = abs(o['open'] - o['sl'])
    print(f"Ticket #{o['ticket']:3d} | {o['time']} | {o['type']:4s} @ {o['open']:.2f} | SL: {o['sl']:.2f} (Dist: ${sl_dist:.2f}) | {o['res']}")
