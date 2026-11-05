import re, json, struct
from datetime import datetime
from collections import defaultdict

# 1. Read MT4 tester log for latest run
p = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log'
with open(p, 'rb') as f:
    text = f.read().decode('utf-8', errors='replace')

lines = text.splitlines()
indices = [i for i, l in enumerate(lines) if 'Gold_POI_Sniper_Tester_v1' in l and 'loaded successfully' in l]
latest_start = indices[-1] if indices else 0
run_lines = lines[latest_start:]

# Regex patterns
pat_trigger = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[POI APEX (BUY|SELL)\] Entry: ([\d\.]+) \| SL: ([\d\.]+) \((\d+) pts\) \| TP: ([\d\.]+) \(1:([\d\.]+) RR\) \| Lots: ([\d\.]+)')
pat_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[ORDER SUCCESS\] Ticket #(\d+) (BUY|SELL) ([\d\.]+) lots @ ([\d\.]+)')
pat_be = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[BE LOCK SUCCESS\] Ticket #(\d+) moved to BE')
pat_bailout = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v1 GOLD,M15: \[STRUCTURAL BAILOUT (BUY|SELL)\] Opposite Rejection Detected on M15\. Closing Ticket #(\d+)')
pat_close_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
pat_close_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')
pat_close_order = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: order #(\d+) is closed')

trades = {}
last_trigger = None
parsed_trades = []

for l in run_lines:
    m_trig = pat_trigger.search(l)
    if m_trig:
        last_trigger = {
            'time': m_trig.group(1),
            'type': m_trig.group(2),
            'entry_calc': float(m_trig.group(3)),
            'sl_calc': float(m_trig.group(4)),
            'sl_pts': int(m_trig.group(5)),
            'tp_calc': float(m_trig.group(6)),
            'rr': float(m_trig.group(7)),
            'lots': float(m_trig.group(8))
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
            'bailout': False,
            'close_time': None,
            'close_price': None,
            'close_reason': None,
            'pnl': 0.0
        }
        continue

    m_be = pat_be.search(l)
    if m_be:
        t_id = int(m_be.group(2))
        if t_id in trades: trades[t_id]['be_locked'] = True
        continue

    m_bail = pat_bailout.search(l)
    if m_bail:
        t_id = int(m_bail.group(3))
        if t_id in trades: trades[t_id]['bailout'] = True
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

    m_ord = pat_close_order.search(l)
    if m_ord:
        t_id = int(m_ord.group(2))
        if t_id in trades and trades[t_id]['close_time'] is None:
            t = trades[t_id]
            t['close_time'] = m_ord.group(1)
            # find close price from next log or calculate from bailout
            t['close_reason'] = 'STRUCTURAL_BAILOUT' if t['bailout'] else 'MANUAL_CLOSE'
            # approximate close price
            parsed_trades.append(t)
        continue

print(f"Total parsed trades: {len(parsed_trades)}")

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

# Enrich forensics
for t in parsed_trades:
    t_open = datetime.strptime(t['open_time'], '%Y.%m.%d %H:%M:%S')
    t_close = datetime.strptime(t['close_time'], '%Y.%m.%d %H:%M:%S') if t['close_time'] else t_open
    t['duration_hrs'] = (t_close - t_open).total_seconds() / 3600.0
    t['month_str'] = t_open.strftime('%Y-%m')
    
    trade_bars = [b for b in bars if t_open <= b['time'] <= t_close]
    if not trade_bars: trade_bars = [{'high': t['open_price'], 'low': t['open_price']}]
    
    init_sl = t['trigger_info']['sl_calc'] if t['trigger_info'] else t['open_price']
    sl_dist = abs(t['open_price'] - init_sl)
    
    if t['type'] == 'BUY':
        lowest_during = min(b['low'] for b in trade_bars)
        highest_during = max(b['high'] for b in trade_bars)
        mae = t['open_price'] - lowest_during
        mfe = highest_during - t['open_price']
        clearance = lowest_during - init_sl
    else:
        lowest_during = min(b['low'] for b in trade_bars)
        highest_during = max(b['high'] for b in trade_bars)
        mae = highest_during - t['open_price']
        mfe = t['open_price'] - lowest_during
        clearance = init_sl - highest_during
        
    t['mae_pts'] = round(mae * 100.0, 1)
    t['mfe_pts'] = round(mfe * 100.0, 1)
    t['clearance_pts'] = round(clearance * 100.0, 1)
    t['mfe_r'] = round(mfe / (sl_dist if sl_dist > 0 else 1.0), 2)

# 1. Monthly Breakdown
monthly = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0})
for t in parsed_trades:
    m = t['month_str']
    monthly[m]['total'] += 1
    monthly[m]['pnl'] += t['pnl']
    if t['pnl'] > 0: monthly[m]['wins'] += 1
    else: monthly[m]['losses'] += 1

# 2. Win Stats
wins = [t for t in parsed_trades if t['pnl'] > 0]
win_durations = [t['duration_hrs'] for t in wins]
avg_win_dur = sum(win_durations)/len(win_durations) if wins else 0.0
avg_clearance = sum(t['clearance_pts'] for t in wins)/len(wins) if wins else 0.0
zero_dd_wins = [t for t in wins if t['mae_pts'] <= 55.0]

# 3. Loss Stats
losses = [t for t in parsed_trades if t['pnl'] <= 0]
reversed_after_1r = [t for t in losses if t['mfe_r'] >= 1.0]
reversed_after_1_5r = [t for t in losses if t['mfe_r'] >= 1.5]
pure_fakeouts = [t for t in losses if t['mfe_r'] < 0.5]

# 4. Techniques (SELL vs BUY)
sells = [t for t in parsed_trades if t['type'] == 'SELL']
buys = [t for t in parsed_trades if t['type'] == 'BUY']
sells_win = [t for t in sells if t['pnl'] > 0]
buys_win = [t for t in buys if t['pnl'] > 0]

# 5. Streaks
max_w = max_l = cur_w = cur_l = 0
max_w_amt = max_l_amt = cur_w_amt = cur_l_amt = 0.0

for t in parsed_trades:
    if t['pnl'] > 0:
        cur_w += 1
        cur_w_amt += t['pnl']
        cur_l = 0
        cur_l_amt = 0.0
        if cur_w > max_w:
            max_w = cur_w
            max_w_amt = cur_w_amt
    else:
        cur_l += 1
        cur_l_amt += abs(t['pnl'])
        cur_w = 0
        cur_w_amt = 0.0
        if cur_l > max_l:
            max_l = cur_l
            max_l_amt = cur_l_amt

summary_v25 = {
    'total_trades': len(parsed_trades),
    'wins': len(wins),
    'losses': len(losses),
    'win_rate': round(len(wins)/len(parsed_trades)*100.0, 2) if parsed_trades else 0.0,
    'total_pnl': round(sum(t['pnl'] for t in parsed_trades), 2),
    'monthly': dict(monthly),
    'holding': {
        'avg_hours': round(avg_win_dur, 2),
        'min_hours': round(min(win_durations), 2) if wins else 0,
        'max_hours': round(max(win_durations), 2) if wins else 0,
        'avg_clearance_sl_pts': round(avg_clearance, 1),
        'zero_dd_wins_count': len(zero_dd_wins),
        'zero_dd_pct': round(len(zero_dd_wins)/len(wins)*100.0, 1) if wins else 0
    },
    'loss_anatomy': {
        'pure_fakeout': len(pure_fakeouts),
        'pure_fakeout_pct': round(len(pure_fakeouts)/len(losses)*100.0, 1) if losses else 0,
        'profit_then_reversed_1r': len(reversed_after_1r),
        'profit_then_reversed_1_5r': len(reversed_after_1_5r)
    },
    'techniques': {
        'sell_total': len(sells),
        'sell_wins': len(sells_win),
        'sell_win_rate': round(len(sells_win)/len(sells)*100.0, 1) if sells else 0,
        'buy_total': len(buys),
        'buy_wins': len(buys_win),
        'buy_win_rate': round(len(buys_win)/len(buys)*100.0, 1) if buys else 0
    },
    'streaks': {
        'max_consec_wins': max_w,
        'max_win_streak_profit': round(max_w_amt, 2),
        'max_consec_losses': max_l,
        'max_loss_streak_loss': round(max_l_amt, 2)
    }
}

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v25_forensics_summary.json', 'w') as f:
    json.dump(summary_v25, f, indent=2)

print("V2.5 Forensics completed successfully.")
