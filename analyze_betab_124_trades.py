import re, json, struct, math, statistics
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

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\run_betab_exact.txt', 'r', encoding='utf-8') as f:
    text = f.read()

opens = {}
for m in re.finditer(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_8_beta_b GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)', text):
    t_str, ticket, cmd, lots, open_p, sl, tp = m.groups()
    ticket = int(ticket)
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
for m in re.finditer(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: (stop loss|take profit) #(\d+) at ([\d\.]+)', text):
    t_str, kind, ticket, close_p = m.groups()
    closes[int(ticket)] = {'time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'), 'price': float(close_p), 'reason': 'TP' if kind == 'take profit' else 'SL'}

for m in re.finditer(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_8_beta_b GOLD,M15: close #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+) at price ([\d\.]+)', text):
    t_str, ticket, cmd, lots, open_p, sl, tp, close_p = m.groups()
    closes[int(ticket)] = {'time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'), 'price': float(close_p), 'reason': 'MANUAL'}

print(f'Total opens parsed: {len(opens)}')
print(f'Total closes parsed: {len(closes)}')

# Process trades
balance = 2000.0
peak_balance = 2000.0
min_balance = 2000.0
max_abs_dd = 0.0
max_dd_usd = 0.0
max_dd_pct = 0.0

trades = []
for t_id in sorted(opens.keys()):
    op = opens[t_id]
    cl = closes.get(t_id)
    if not cl: continue
    
    cmd = op['type']
    lots = op['lots']
    entry = op['open_price']
    exit_p = cl['price']
    init_sl = op['init_sl']
    sl_dist = abs(entry - init_sl)
    
    if cmd == 'BUY':
        pnl = (exit_p - entry) * lots * 100.0
        pnl_r = (exit_p - entry) / sl_dist if sl_dist > 0 else 0
    else:
        pnl = (entry - exit_p) * lots * 100.0
        pnl_r = (entry - exit_p) / sl_dist if sl_dist > 0 else 0
        
    pnl = round(pnl, 2)
    balance += pnl
    if balance > peak_balance: peak_balance = balance
    if balance < min_balance: min_balance = balance
    
    abs_dd = 2000.0 - min_balance
    if abs_dd > max_abs_dd: max_abs_dd = abs_dd
    
    dd_usd = peak_balance - balance
    dd_pct = (dd_usd / peak_balance) * 100.0 if peak_balance > 0 else 0.0
    if dd_usd > max_dd_usd: max_dd_usd = dd_usd
    if dd_pct > max_dd_pct: max_dd_pct = dd_pct
    
    hold_hours = (cl['time'] - op['open_time']).total_seconds() / 3600.0
    
    # Active bars
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
    
    # Session
    h = op['open_time'].hour
    if 0 <= h < 8: session_name = 'Asian Session (00:00-08:00)'
    elif 8 <= h < 14: session_name = 'London Session (08:00-14:00)'
    elif 14 <= h < 21: session_name = 'NY Session (14:00-21:00)'
    else: session_name = 'Late Session (21:00-24:00)'
    
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
        'session': session_name,
        'balance': round(balance, 2),
        'dd_usd': round(dd_usd, 2)
    })

win_trades = [t for t in trades if t['pnl'] > 0]
loss_trades = [t for t in trades if t['pnl'] <= 0]
gross_profit = sum(t['pnl'] for t in win_trades)
gross_loss = sum(abs(t['pnl']) for t in loss_trades)
net_profit = gross_profit - gross_loss

print('=== BETAB EXECUTION AUDIT (124 TRADES) ===')
print('Initial Deposit: 2000.00 | Net Profit: ' + str(round(net_profit, 2)) + ' | Final Balance: ' + str(round(balance, 2)))
print('Gross Profit: ' + str(round(gross_profit, 2)) + ' | Gross Loss: -' + str(round(gross_loss, 2)))
print('Profit Factor: ' + str(round(gross_profit / gross_loss, 2)))
print('Absolute Drawdown: ' + str(round(max_abs_dd, 2)) + ' (Min Balance: $' + str(round(min_balance, 2)) + ')')
print('Maximal Drawdown: $' + str(round(max_dd_usd, 2)) + ' (' + str(round(max_dd_pct, 2)) + '%)')
print('Total Trades: ' + str(len(trades)) + ' | Wins: ' + str(len(win_trades)) + ' (' + str(round(len(win_trades)/len(trades)*100, 2)) + '%) | Losses: ' + str(len(loss_trades)))

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

print('Max Consecutive Wins: ' + str(max_cw) + ' trades (Total: +$' + str(round(max_cw_usd, 2)) + ')')
print('Max Consecutive Losses: ' + str(max_cl) + ' trades (Total: -$' + str(round(max_cl_usd, 2)) + ')')

# Holding time and MAE
avg_hold = sum(t['hold_hours'] for t in win_trades) / len(win_trades)
avg_mae_dlr = sum(t['mae_dlr'] for t in win_trades) / len(win_trades)
avg_mae_pct = sum(t['mae_pct'] for t in win_trades) / len(win_trades)
zero_mae = [t for t in win_trades if t['mae_dlr'] <= 0.50]
print('Avg Win Hold Time: ' + str(round(avg_hold, 2)) + ' hours')
print('Avg Win MAE: $' + str(round(avg_mae_dlr, 2)) + ' (' + str(round(avg_mae_pct, 1)) + '% of SL)')
print('Immediate Profit Trades (MAE <= $0.50): ' + str(len(zero_mae)) + ' (' + str(round(len(zero_mae)/len(win_trades)*100, 1)) + '%)')

# Monthly and Session Breakdown
monthly_dict = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'sessions': defaultdict(lambda: {'trades': 0, 'wins': 0})})
for t in trades:
    m = t['month']
    md = monthly_dict[m]
    md['trades'] += 1
    if t['pnl'] > 0: md['wins'] += 1
    else: md['losses'] += 1
    md['pnl'] += t['pnl']
    
    s = t['session']
    md['sessions'][s]['trades'] += 1
    if t['pnl'] > 0: md['sessions'][s]['wins'] += 1

print('\n=== MONTHLY & SESSION BREAKDOWN (13 MONTHS) ===')
for m, md in sorted(monthly_dict.items()):
    wr = md['wins'] / md['trades'] * 100
    print(m + ' | Trades: ' + str(md['trades']) + ' | Wins: ' + str(md['wins']) + ' | WR: ' + str(round(wr, 1)) + '% | PnL: $' + str(round(md['pnl'], 2)))
    for s, sd in sorted(md['sessions'].items()):
        swr = sd['wins'] / sd['trades'] * 100
        print('   Session ' + s + ': ' + str(sd['trades']) + ' trades, ' + str(sd['wins']) + ' wins (' + str(round(swr, 1)) + '%)')

# Loss autopsy
trapped = [t for t in loss_trades if t['mfe_r'] < 0.5]
reversed_loss = [t for t in loss_trades if t['mfe_r'] >= 1.0]
chop_loss = [t for t in loss_trades if 0.5 <= t['mfe_r'] < 1.0]
print('\n=== LOSS AUTOPSY (65 LOSSES) ===')
print('1. Trapped / False Breakout (plunged straight to SL, never +0.5R): ' + str(len(trapped)) + ' trades (-$' + str(round(sum(abs(t['pnl']) for t in trapped), 2)) + ')')
print('2. Chop / Lost momentum (+0.5R to +1.0R): ' + str(len(chop_loss)) + ' trades (-$' + str(round(sum(abs(t['pnl']) for t in chop_loss), 2)) + ')')
print('3. Profitable First (+1.0R+), then reversed to SL: ' + str(len(reversed_loss)) + ' trades (-$' + str(round(sum(abs(t['pnl']) for t in reversed_loss), 2)) + ')')
