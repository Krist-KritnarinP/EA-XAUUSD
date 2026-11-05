import json, struct
from datetime import datetime

# Load parsed trades and M15 bars
with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_sniper_parsed_trades.json', 'r') as f:
    all_trades = json.load(f)

# The latest run in 20261101.log had 128 trades
p = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log'
with open(p, 'rb') as f:
    text = f.read().decode('utf-8', errors='replace')

lines = text.splitlines()
indices = [i for i, l in enumerate(lines) if 'Gold_POI_Sniper_Tester_v1' in l and 'loaded successfully' in l]
latest_start = indices[-1] if indices else 0
run_lines = lines[latest_start:]

import re
pat_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[ORDER SUCCESS\] Ticket #(\d+) (BUY|SELL) ([\d\.]+) lots @ ([\d\.]+)')
pat_close_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
pat_close_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')
pat_be = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[BE LOCK SUCCESS\] Ticket #(\d+)')
pat_bail = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[STRUCTURAL BAILOUT (BUY|SELL)\] Opposite Rejection Detected on M15\. Closing Ticket #(\d+)')

orders = {}
for l in run_lines:
    m = pat_open.search(l)
    if m:
        t_id = int(m.group(2))
        orders[t_id] = {
            'ticket': t_id,
            'open_time': m.group(1),
            'type': m.group(3),
            'lots': float(m.group(4)),
            'open_price': float(m.group(5)),
            'close_time': None,
            'close_price': None,
            'reason': None,
            'be_locked': False
        }
    m_be = pat_be.search(l)
    if m_be:
        t_id = int(m_be.group(2))
        if t_id in orders: orders[t_id]['be_locked'] = True
    m_tp = pat_close_tp.search(l)
    if m_tp:
        t_id = int(m_tp.group(2))
        if t_id in orders:
            orders[t_id]['close_time'] = m_tp.group(1)
            orders[t_id]['close_price'] = float(m_tp.group(3))
            orders[t_id]['reason'] = 'TP'
    m_sl = pat_close_sl.search(l)
    if m_sl:
        t_id = int(m_sl.group(2))
        if t_id in orders:
            orders[t_id]['close_time'] = m_sl.group(1)
            orders[t_id]['close_price'] = float(m_sl.group(3))
            orders[t_id]['reason'] = 'BE' if orders[t_id]['be_locked'] else 'SL'
    m_b = pat_bail.search(l)
    if m_b:
        t_id = int(m_b.group(3))
        if t_id in orders:
            orders[t_id]['close_time'] = m_b.group(1)
            orders[t_id]['reason'] = 'STRUCTURAL_BAILOUT'

# Filter the 59 losing trades
losses = []
for t_id, o in orders.items():
    if o['reason'] == 'SL':
        losses.append(o)

print(f"Total verified SL losses: {len(losses)}")

# Load M15 bars
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

bar_map = {b['time']: b for b in bars}

# Forensic categorization of losses
loss_categories = {
    'news_spike_fakeout': [],      # Opened between 15:15 - 15:45 (US Open / News spike)
    'double_sweep_expansion': [],  # Swept POI, but then trend expanded through SL without any hesitation
    'profit_reversal_trap': [],    # Went in profit > 1.0R to 1.7R but missed 1.8R BE
    'late_ny_exhaustion': []       # Opened after 19:00 into low volume
}

for l in losses:
    t_open = datetime.strptime(l['open_time'], '%Y.%m.%d %H:%M:%S')
    t_close = datetime.strptime(l['close_time'], '%Y.%m.%d %H:%M:%S') if l['close_time'] else t_open
    trade_bars = [b for b in bars if t_open <= b['time'] <= t_close]
    if not trade_bars: trade_bars = [{'high': l['open_price'], 'low': l['open_price']}]
    
    sl_dist = abs(l['open_price'] - l['close_price'])
    if l['type'] == 'BUY':
        mfe = max(b['high'] for b in trade_bars) - l['open_price']
    else:
        mfe = l['open_price'] - min(b['low'] for b in trade_bars)
        
    mfe_r = mfe / (sl_dist if sl_dist > 0 else 1.0)
    l['mfe_r'] = mfe_r
    l['duration_mins'] = (t_close - t_open).total_seconds() / 60.0
    
    # Check category
    h = t_open.hour
    m = t_open.minute
    if (h == 15 and 15 <= m <= 45) or (h == 16 and m == 0):
        loss_categories['news_spike_fakeout'].append(l)
    elif mfe_r >= 1.0:
        loss_categories['profit_reversal_trap'].append(l)
    elif h >= 19:
        loss_categories['late_ny_exhaustion'].append(l)
    else:
        loss_categories['double_sweep_expansion'].append(l)

print("\n=== LOSS ANATOMY CATEGORIES ===")
print(f"1. Profit Reversal Trap (Went +1.0R to +1.7R then reversed): {len(loss_categories['profit_reversal_trap'])} trades")
print(f"2. US Open News / Data Spike (15:15 - 15:45): {len(loss_categories['news_spike_fakeout'])} trades")
print(f"3. Pure Trend Expansion / Double Sweep: {len(loss_categories['double_sweep_expansion'])} trades")
print(f"4. Late NY Exhaustion (after 19:00): {len(loss_categories['late_ny_exhaustion'])} trades")

# Details of Profit Reversal Trap
avg_mfe = sum(x['mfe_r'] for x in loss_categories['profit_reversal_trap'])/len(loss_categories['profit_reversal_trap']) if loss_categories['profit_reversal_trap'] else 0
print(f"   -> Average profit reached before reversing: +{avg_mfe:.2f}R")

# Save to json for reference
with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\loss_forensics_59.json', 'w') as f:
    json.dump({k: [{'ticket': x['ticket'], 'time': x['open_time'], 'type': x['type'], 'lots': x['lots'], 'mfe_r': round(x['mfe_r'], 2), 'dur_mins': round(x['duration_mins'], 1)} for x in v] for k, v in loss_categories.items()}, f, indent=2)

print("Loss Forensics written.")
