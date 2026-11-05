import re, json, struct
from datetime import datetime
from collections import defaultdict

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
bar_map = {b['time']: idx for idx, b in enumerate(bars)}

daily = {}
for b in bars:
    d = b['time'].date()
    if d not in daily:
        daily[d] = {'open': b['open'], 'high': b['high'], 'low': b['low'], 'close': b['close']}
    else:
        if b['high'] > daily[d]['high']: daily[d]['high'] = b['high']
        if b['low'] < daily[d]['low']: daily[d]['low'] = b['low']
        daily[d]['close'] = b['close']
dates_sorted = sorted(list(daily.keys()))

asian_ranges = {}
for b in bars:
    d = b['time'].date()
    if 0 <= b['time'].hour < 7:
        if d not in asian_ranges:
            asian_ranges[d] = {'high': b['high'], 'low': b['low']}
        else:
            if b['high'] > asian_ranges[d]['high']: asian_ranges[d]['high'] = b['high']
            if b['low'] < asian_ranges[d]['low']: asian_ranges[d]['low'] = b['low']

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\run_1433_exact.txt', 'r', encoding='utf-8') as f:
    text = f.read()

opens = {}
for m in re.finditer(r'open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)', text):
    ticket, cmd, lots, open_p, sl, tp = m.groups()
    ticket = int(ticket)
    m_time = re.search(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v3 GOLD,M15: open #' + str(ticket), text)
    t_str = m_time.group(1) if m_time else '2025.10.01 00:00:00'
    opens[ticket] = {
        'ticket': ticket,
        'open_time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'),
        'type': cmd.upper(),
        'lots': float(lots),
        'open_price': float(open_p),
        'init_sl': float(sl),
        'init_tp': float(tp)
    }

closes = {}
for m in re.finditer(r'Tester: (stop loss|take profit) #(\d+) at ([\d\.]+)', text):
    kind, ticket, close_p = m.groups()
    m_time = re.search(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: (stop loss|take profit) #' + ticket, text)
    t_str = m_time.group(1) if m_time else '2025.10.01 00:00:00'
    closes[int(ticket)] = {'time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'), 'price': float(close_p), 'reason': 'TP' if kind == 'take profit' else 'SL'}

for m in re.finditer(r'close #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+) at price ([\d\.]+)', text):
    ticket, cmd, lots, open_p, sl, tp, close_p = m.groups()
    m_time = re.search(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v3 GOLD,M15: close #' + ticket, text)
    t_str = m_time.group(1) if m_time else '2025.10.01 00:00:00'
    closes[int(ticket)] = {'time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'), 'price': float(close_p), 'reason': 'MANUAL'}

trades = []
for t_id in sorted(opens.keys()):
    op = opens[t_id]
    cl = closes[t_id]
    entry = op['open_price']
    exit_p = cl['price']
    lots = op['lots']
    cmd = op['type']
    init_sl = op['init_sl']
    sl_dist = abs(entry - init_sl)
    
    if cmd == 'BUY':
        pnl = (exit_p - entry) * lots * 100.0
        pnl_r = (exit_p - entry) / sl_dist if sl_dist > 0 else 0
    else:
        pnl = (entry - exit_p) * lots * 100.0
        pnl_r = (entry - exit_p) / sl_dist if sl_dist > 0 else 0
        
    pnl = round(pnl, 2)
    hold_hours = (cl['time'] - op['open_time']).total_seconds() / 3600.0
    
    # Bar level MAE / MFE
    start_b_idx = bar_map.get(op['open_time'])
    if start_b_idx is None:
        for b_i, b in enumerate(bars):
            if b['time'] >= op['open_time']:
                start_b_idx = b_i
                break
    end_b_idx = bar_map.get(cl['time'])
    if end_b_idx is None:
        for b_i in range(start_b_idx, len(bars)):
            if bars[b_i]['time'] >= cl['time']:
                end_b_idx = b_i
                break
    if end_b_idx is None: end_b_idx = start_b_idx + 1
    
    trade_bars = bars[start_b_idx:end_b_idx+1]
    if cmd == 'BUY':
        worst_p = min(b['low'] for b in trade_bars)
        best_p = max(b['high'] for b in trade_bars)
        adverse = entry - worst_p
        favorable = best_p - entry
    else:
        worst_p = max(b['high'] for b in trade_bars)
        best_p = min(b['low'] for b in trade_bars)
        adverse = worst_p - entry
        favorable = entry - best_p
        
    mae_dollars = max(0.0, adverse)
    mfe_dollars = max(0.0, favorable)
    mae_pct_sl = (mae_dollars / sl_dist * 100.0) if sl_dist > 0 else 0.0
    mfe_r = (mfe_dollars / sl_dist) if sl_dist > 0 else 0.0
    
    # Sub-session
    h = op['open_time'].hour
    if 15 <= h < 17: sub_session = 'Early NY (15:00-17:00)'
    elif 17 <= h < 19: sub_session = 'Mid NY (17:00-19:00)'
    else: sub_session = 'Late NY (19:00-20:30)'
    
    # POI Setup
    cur_date = op['open_time'].date()
    idx_d = dates_sorted.index(cur_date) if cur_date in dates_sorted else -1
    prev_d = dates_sorted[idx_d - 1] if idx_d > 0 else None
    pdh = daily[prev_d]['high'] if prev_d else 0.0
    pdl = daily[prev_d]['low'] if prev_d else 0.0
    asian_h = asian_ranges[cur_date]['high'] if cur_date in asian_ranges else 0.0
    asian_l = asian_ranges[cur_date]['low'] if cur_date in asian_ranges else 0.0
    
    if cmd == 'SELL':
        if abs(entry - pdh) <= 2.5 or entry >= pdh: setup = 'PDH Sweep SELL'
        elif abs(entry - asian_h) <= 2.5 or entry >= asian_h: setup = 'Asian High Sweep SELL'
        else: setup = 'Resistance Liquidity SELL'
    else:
        if abs(entry - pdl) <= 2.5 or entry <= pdl: setup = 'PDL Sweep BUY'
        elif abs(entry - asian_l) <= 2.5 or entry <= asian_l: setup = 'Asian Low Sweep BUY'
        else: setup = 'Support Liquidity BUY'
        
    trades.append({
        'ticket': t_id,
        'open_time': op['open_time'],
        'month': op['open_time'].strftime('%Y-%m'),
        'type': cmd,
        'lots': lots,
        'entry': entry,
        'exit': exit_p,
        'sl': init_sl,
        'sl_dist': round(sl_dist, 2),
        'pnl': pnl,
        'pnl_r': round(pnl_r, 2),
        'hold_hours': round(hold_hours, 2),
        'reason': cl['reason'],
        'mae_dlr': round(mae_dollars, 2),
        'mae_pct': round(mae_pct_sl, 1),
        'mfe_r': round(mfe_r, 2),
        'sub_session': sub_session,
        'setup': setup
    })

win_trades = [t for t in trades if t['pnl'] > 0]
loss_trades = [t for t in trades if t['pnl'] <= 0]

# Monthly
monthly_dict = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'sessions': defaultdict(lambda: {'trades': 0, 'wins': 0}), 'setups': defaultdict(lambda: {'trades': 0, 'wins': 0})})
for t in trades:
    m = t['month']
    md = monthly_dict[m]
    md['trades'] += 1
    if t['pnl'] > 0: md['wins'] += 1
    else: md['losses'] += 1
    md['pnl'] += t['pnl']
    
    md['sessions'][t['sub_session']]['trades'] += 1
    if t['pnl'] > 0: md['sessions'][t['sub_session']]['wins'] += 1
    
    md['setups'][t['setup']]['trades'] += 1
    if t['pnl'] > 0: md['setups'][t['setup']]['wins'] += 1

# Streaks
max_cw = 0; cur_cw = 0; max_cw_usd = 0.0; cur_cw_usd = 0.0
max_cl = 0; cur_cl = 0; max_cl_usd = 0.0; cur_cl_usd = 0.0
for t in trades:
    if t['pnl'] > 0:
        cur_cw += 1; cur_cw_usd += t['pnl']
        if cur_cw > max_cw: max_cw = cur_cw; max_cw_usd = cur_cw_usd
        cur_cl = 0; cur_cl_usd = 0.0
    else:
        cur_cl += 1; cur_cl_usd += abs(t['pnl'])
        if cur_cl > max_cl: max_cl = cur_cl; max_cl_usd = cur_cl_usd
        cur_cw = 0; cur_cw_usd = 0.0

# Loss autopsy
trapped = [t for t in loss_trades if t['mfe_r'] < 0.5]
reversed_loss = [t for t in loss_trades if t['mfe_r'] >= 1.0]
chop_loss = [t for t in loss_trades if 0.5 <= t['mfe_r'] < 1.0]

avg_hold = sum(t['hold_hours'] for t in win_trades) / len(win_trades)
avg_mae_dlr = sum(t['mae_dlr'] for t in win_trades) / len(win_trades)
avg_mae_pct = sum(t['mae_pct'] for t in win_trades) / len(win_trades)
trapped_sum = sum(abs(t['pnl']) for t in trapped)
chop_sum = sum(abs(t['pnl']) for t in chop_loss)
reversed_sum = sum(abs(t['pnl']) for t in reversed_loss)

print('=== SUMMARY METRICS ===')
print('Total Trades:', len(trades))
print('Wins:', len(win_trades), 'Losses:', len(loss_trades))
print('Max Consecutive Wins:', max_cw, 'trades (Total: +$' + str(round(max_cw_usd, 2)) + ')')
print('Max Consecutive Losses:', max_cl, 'trades (Total: -$' + str(round(max_cl_usd, 2)) + ')')
print('Avg Win Hold Time:', round(avg_hold, 2), 'hours')
print('Avg Win MAE: $' + str(round(avg_mae_dlr, 2)) + ' (' + str(round(avg_mae_pct, 1)) + '% of SL)')
zero_mae = [t for t in win_trades if t['mae_dlr'] <= 0.50]
print('Immediate Profit Trades (MAE <= $0.50):', len(zero_mae), '(' + str(round(len(zero_mae)/len(win_trades)*100, 1)) + '%)')
print('\nLoss Autopsy:')
print('- Trapped / Fakeout (plunged straight to SL, never +0.5R):', len(trapped), 'trades (-$' + str(round(trapped_sum, 2)) + ')')
print('- Chop / Breakdown (+0.5R to +1.0R then reversed):', len(chop_loss), 'trades (-$' + str(round(chop_sum, 2)) + ')')
print('- Profitable First (+1.0R+), then slipped through trail before lock:', len(reversed_loss), 'trades (-$' + str(round(reversed_sum, 2)) + ')')

print('\n=== MONTHLY BREAKDOWN ===')
for m, md in sorted(monthly_dict.items()):
    wr = md['wins'] / md['trades'] * 100
    print(m + ' | Trades: ' + str(md['trades']) + ' | Wins: ' + str(md['wins']) + ' | WR: ' + str(round(wr, 1)) + '% | PnL: $' + str(round(md['pnl'], 2)))
    for s, sd in sorted(md['sessions'].items()):
        swr = sd['wins'] / sd['trades'] * 100
        print('   Session ' + s + ': ' + str(sd['trades']) + ' trades, ' + str(sd['wins']) + ' wins (' + str(round(swr, 1)) + '%)')
    for st, std in sorted(md['setups'].items()):
        stwr = std['wins'] / std['trades'] * 100
        print('   Setup   ' + st + ': ' + str(std['trades']) + ' trades, ' + str(std['wins']) + ' wins (' + str(round(stwr, 1)) + '%)')
