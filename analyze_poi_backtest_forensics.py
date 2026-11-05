import re, os, json
from datetime import datetime

log_path = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log'

with open(log_path, 'rb') as f:
    text = f.read().decode('utf-8', errors='replace')

lines = text.splitlines()

# Find the start of the Gold_POI_Sniper_Tester_v1 run
start_idx = -1
for idx, l in enumerate(lines):
    if "Gold_POI_Sniper_Tester_v1" in l and "loaded successfully" in l:
        start_idx = idx

print(f"Test run found starting at line: {start_idx}")
if start_idx != -1:
    lines = lines[start_idx:]

trades = {}
# Regex patterns
pat_trigger = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[POI SNIPER (BUY|SELL) TRIGGER\] POI Hit \| (?:Upper|Lower) Wick: ([\d\.]+)% \| Entry: ([\d\.]+) \| SL: ([\d\.]+) \((\d+) pts\) \| TP: ([\d\.]+) \(1:([\d\.]+) RR\)')
pat_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[ORDER OPEN SUCCESS\] Ticket #(\d+) (BUY|SELL) ([\d\.]+) lots @ ([\d\.]+)')
pat_be = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[BE LOCK SUCCESS\] Ticket #(\d+) moved to BE')
pat_close_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
pat_close_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')

last_trigger = None
parsed_trades = []

for l in lines:
    m_trig = pat_trigger.search(l)
    if m_trig:
        last_trigger = {
            'time': m_trig.group(1),
            'type': m_trig.group(2),
            'wick_pct': float(m_trig.group(3)),
            'entry_calc': float(m_trig.group(4)),
            'sl_calc': float(m_trig.group(5)),
            'sl_pts': int(m_trig.group(6)),
            'tp_calc': float(m_trig.group(7)),
            'rr': float(m_trig.group(8))
        }
        continue
    
    m_open = pat_open.search(l)
    if m_open:
        t_id = int(m_open.group(2))
        trades[t_id] = {
            'ticket': t_id,
            'open_time': m_open.group(1),
            'type': m_open.group(3),
            'lots': float(m_open.group(4)),
            'open_price': float(m_open.group(5)),
            'trigger_info': last_trigger,
            'be_locked': False,
            'close_time': None,
            'close_price': None,
            'close_reason': None,
            'pnl': 0.0
        }
        continue

    m_be = pat_be.search(l)
    if m_be:
        t_id = int(m_be.group(2))
        if t_id in trades:
            trades[t_id]['be_locked'] = True
        continue

    m_tp = pat_close_tp.search(l)
    if m_tp:
        t_id = int(m_tp.group(2))
        if t_id in trades:
            t = trades[t_id]
            t['close_time'] = m_tp.group(1)
            t['close_price'] = float(m_tp.group(3))
            t['close_reason'] = 'TP'
            pts = (t['close_price'] - t['open_price']) if t['type'] == 'BUY' else (t['open_price'] - t['close_price'])
            t['pnl'] = round(pts * t['lots'] * 100.0, 2)
            parsed_trades.append(t)
        continue

    m_sl = pat_close_sl.search(l)
    if m_sl:
        t_id = int(m_sl.group(2))
        if t_id in trades:
            t = trades[t_id]
            t['close_time'] = m_sl.group(1)
            t['close_price'] = float(m_sl.group(3))
            t['close_reason'] = 'BE' if t['be_locked'] else 'SL'
            pts = (t['close_price'] - t['open_price']) if t['type'] == 'BUY' else (t['open_price'] - t['close_price'])
            t['pnl'] = round(pts * t['lots'] * 100.0, 2)
            parsed_trades.append(t)
        continue

print(f"Total fully parsed trades: {len(parsed_trades)}")

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_sniper_parsed_trades.json', 'w') as f:
    json.dump(parsed_trades, f, indent=2)

print("Saved parsed trades to JSON successfully.")
