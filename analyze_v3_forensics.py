import re, json, struct
from datetime import datetime
from collections import defaultdict

p = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log'
with open(p, 'rb') as f:
    text = f.read().decode('utf-8', errors='replace')

lines = text.splitlines()
indices = [i for i, l in enumerate(lines) if 'Gold_POI_Sniper_Tester_v3' in l and 'loaded successfully' in l]
latest_start = indices[-1] if indices else 0
run_lines = lines[latest_start:]

pat_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v3 GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
pat_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
pat_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')
pat_close = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: order #(\d+) is closed')
pat_modify = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v3 GOLD,M15: modify #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+)')

orders = {}
parsed_trades = []

for l in run_lines:
    m_op = pat_open.search(l)
    if m_op:
        t_id = int(m_op.group(2))
        orders[t_id] = {
            'ticket': t_id,
            'open_time': m_op.group(1),
            'type': m_op.group(3).upper(),
            'lots': float(m_op.group(4)),
            'open_price': float(m_op.group(5)),
            'init_sl': float(m_op.group(6)),
            'init_tp': float(m_op.group(7)),
            'current_sl': float(m_op.group(6)),
            'close_time': None,
            'close_price': None,
            'reason': None,
            'pnl': 0.0,
            'trailed': False
        }
        continue
        
    m_mod = pat_modify.search(l)
    if m_mod:
        t_id = int(m_mod.group(2))
        if t_id in orders:
            orders[t_id]['current_sl'] = float(m_mod.group(6))
            orders[t_id]['trailed'] = True
        continue
        
    m_tp = pat_tp.search(l)
    if m_tp:
        t_id = int(m_tp.group(2))
        if t_id in orders:
            t = orders[t_id]
            t['close_time'] = m_tp.group(1)
            t['close_price'] = float(m_tp.group(3))
            t['reason'] = 'TP'
            pts = (t['close_price'] - t['open_price']) if t['type'] == 'BUY' else (t['open_price'] - t['close_price'])
            t['pnl'] = round(pts * t['lots'] * 100.0, 2)
            parsed_trades.append(t)
        continue
        
    m_sl = pat_sl.search(l)
    if m_sl:
        t_id = int(m_sl.group(2))
        if t_id in orders:
            t = orders[t_id]
            t['close_time'] = m_sl.group(1)
            t['close_price'] = float(m_sl.group(3))
            t['reason'] = 'TRAIL_SL' if t['trailed'] else 'SL'
            pts = (t['close_price'] - t['open_price']) if t['type'] == 'BUY' else (t['open_price'] - t['close_price'])
            t['pnl'] = round(pts * t['lots'] * 100.0, 2)
            parsed_trades.append(t)
        continue

    m_cl = pat_close.search(l)
    if m_cl:
        t_id = int(m_cl.group(2))
        if t_id in orders and orders[t_id]['close_time'] is None:
            t = orders[t_id]
            t['close_time'] = m_cl.group(1)
            t['reason'] = 'STRUCTURAL_BAILOUT'
            parsed_trades.append(t)
        continue

print(f"Total parsed v3 trades: {len(parsed_trades)}")

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

# Forensics enrichment
for t in parsed_trades:
    t_open = datetime.strptime(t['open_time'], '%Y.%m.%d %H:%M:%S')
    t_close = datetime.strptime(t['close_time'], '%Y.%m.%d %H:%M:%S') if t['close_time'] else t_open
    t['duration_hrs'] = (t_close - t_open).total_seconds() / 3600.0
    t['month_str'] = t_open.strftime('%Y-%m')
    
    trade_bars = [b for b in bars if t_open <= b['time'] <= t_close]
    if not trade_bars: trade_bars = [{'high': t['open_price'], 'low': t['open_price']}]
    
    sl_dist = abs(t['open_price'] - t['init_sl'])
    if t['type'] == 'BUY':
        lowest_during = min(b['low'] for b in trade_bars)
        highest_during = max(b['high'] for b in trade_bars)
        mae = t['open_price'] - lowest_during
        mfe = highest_during - t['open_price']
        clearance = lowest_during - t['init_sl']
    else:
        lowest_during = min(b['low'] for b in trade_bars)
        highest_during = max(b['high'] for b in trade_bars)
        mae = highest_during - t['open_price']
        mfe = t['open_price'] - lowest_during
        clearance = t['init_sl'] - highest_during
        
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

summary_v3 = {
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
        'profit_then_reversed_1r': len(reversed_after_1r)
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

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v3_forensics_summary.json', 'w') as f:
    json.dump(summary_v3, f, indent=2)

print("V3 Forensics completed successfully.")
