import re, json, struct, math
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

# 2. Daily levels for POI classification
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

# 3. Read log file
log_path = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log'
with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

idx_open1 = 7243391
idx_end = text.find('14:33:15.522')
run_text = text[idx_open1-200:idx_end+500]

opens = {}
for m in re.finditer(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v3 GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)', run_text):
    t_str, ticket, cmd, lots, open_p, sl, tp = m.groups()
    ticket = int(ticket)
    if ticket not in opens:
        opens[ticket] = {
            'ticket': ticket,
            'open_time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'),
            'type': cmd.upper(),
            'lots': float(lots),
            'open_price': float(open_p),
            'init_sl': float(sl),
            'init_tp': float(tp),
            'modifications': []
        }

for m in re.finditer(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Gold_POI_Sniper_Tester_v3 GOLD,M15: modify #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)', run_text):
    t_str, ticket, cmd, lots, open_p, sl, tp = m.groups()
    ticket = int(ticket)
    if ticket in opens:
        opens[ticket]['modifications'].append({
            'time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'),
            'sl': float(sl),
            'tp': float(tp)
        })

closes = {}
for m in re.finditer(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+(Tester: (stop loss|take profit)|Gold_POI_Sniper_Tester_v3 GOLD,M15: close) #(\d+).*?at (price )?([\d\.]+)', run_text):
    t_str, full_kind, sub_kind, ticket, _, close_p = m.groups()
    ticket = int(ticket)
    if ticket in opens and ticket not in closes:
        reason = 'TP' if 'take profit' in full_kind else ('SL' if 'stop loss' in full_kind else 'CLOSE')
        closes[ticket] = {
            'close_time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'),
            'close_price': float(close_p),
            'reason': reason
        }

# 4. Process each trade
trades = []
balance = 2000.0
peak_balance = 2000.0

for t_id in sorted(opens.keys()):
    op = opens[t_id]
    cl = closes.get(t_id)
    if not cl: continue
    
    cmd = op['type']
    lots = op['lots']
    entry = op['open_price']
    exit_p = cl['close_price']
    init_sl = op['init_sl']
    init_tp = op['init_tp']
    sl_dist = abs(entry - init_sl)
    
    # PnL calculation (MT4: 100 oz per lot for GOLD)
    if cmd == 'BUY':
        pnl = (exit_p - entry) * lots * 100.0
        pnl_r = (exit_p - entry) / sl_dist if sl_dist > 0 else 0
    else:
        pnl = (entry - exit_p) * lots * 100.0
        pnl_r = (entry - exit_p) / sl_dist if sl_dist > 0 else 0
        
    pnl = round(pnl, 2)
    balance += pnl
    if balance > peak_balance: peak_balance = balance
    dd_usd = peak_balance - balance
    dd_pct = (dd_usd / peak_balance) * 100.0
    
    hold_hours = (cl['close_time'] - op['open_time']).total_seconds() / 3600.0
    
    # Identify POI Setup
    cur_date = op['open_time'].date()
    idx_d = dates_sorted.index(cur_date) if cur_date in dates_sorted else -1
    prev_d = dates_sorted[idx_d - 1] if idx_d > 0 else None
    pdh = daily[prev_d]['high'] if prev_d else 0.0
    pdl = daily[prev_d]['low'] if prev_d else 0.0
    asian_h = asian_ranges[cur_date]['high'] if cur_date in asian_ranges else 0.0
    asian_l = asian_ranges[cur_date]['low'] if cur_date in asian_ranges else 0.0
    
    # Bar level MAE / MFE
    # Find bars between open_time and close_time
    start_b_idx = bar_map.get(op['open_time'])
    if start_b_idx is None:
        # find closest
        for b_i, b in enumerate(bars):
            if b['time'] >= op['open_time']:
                start_b_idx = b_i
                break
    end_b_idx = bar_map.get(cl['close_time'])
    if end_b_idx is None:
        for b_i in range(start_b_idx, len(bars)):
            if bars[b_i]['time'] >= cl['close_time']:
                end_b_idx = b_i
                break
    if end_b_idx is None: end_b_idx = start_b_idx + 1
    
    trade_bars = bars[start_b_idx:end_b_idx+1]
    
    mae_pts = 0.0
    mfe_pts = 0.0
    mae_dollars = 0.0
    mae_pct_sl = 0.0
    
    if trade_bars:
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
    else:
        mfe_r = 0.0

    # Determine POI type
    setup_name = 'OTHER'
    if cmd == 'SELL':
        if abs(entry - pdh) <= 2.5 or entry >= pdh: setup_name = 'PDH Sweep SELL'
        elif abs(entry - asian_h) <= 2.5 or entry >= asian_h: setup_name = 'Asian High Sweep SELL'
        else: setup_name = 'Resistance Liquidity SELL'
    else:
        if abs(entry - pdl) <= 2.5 or entry <= pdl: setup_name = 'PDL Sweep BUY'
        elif abs(entry - asian_l) <= 2.5 or entry <= asian_l: setup_name = 'Asian Low Sweep BUY'
        else: setup_name = 'Support Liquidity BUY'
        
    # Sub-session
    h = op['open_time'].hour
    if 15 <= h < 17: sub_session = 'Early NY (15:00-17:00)'
    elif 17 <= h < 19: sub_session = 'Mid NY (17:00-19:00)'
    else: sub_session = 'Late NY (19:00-20:30)'
    
    # Loss categorization
    loss_category = 'N/A'
    if pnl <= 0:
        if mfe_r >= 1.2:
            loss_category = 'Profitable First (+1.2R+) then Reversed'
        elif mfe_r >= 0.8:
            loss_category = 'Profitable First (+0.8R to +1.2R) then Reversed'
        elif mae_pct_sl >= 95.0 and len(op['modifications']) == 0:
            loss_category = 'Immediate Trap / Squeeze to Full SL'
        else:
            loss_category = 'Chop / Structural Breakdown'
            
    trades.append({
        'ticket': t_id,
        'open_time': op['open_time'].strftime('%Y-%m-%d %H:%M'),
        'close_time': cl['close_time'].strftime('%Y-%m-%d %H:%M'),
        'month': op['open_time'].strftime('%Y-%m'),
        'type': cmd,
        'lots': lots,
        'entry': entry,
        'exit': exit_p,
        'sl': init_sl,
        'tp': init_tp,
        'sl_dist': round(sl_dist, 2),
        'pnl': pnl,
        'pnl_r': round(pnl_r, 2),
        'hold_hours': round(hold_hours, 2),
        'close_reason': cl['reason'],
        'sub_session': sub_session,
        'setup': setup_name,
        'mae_dollars': round(mae_dollars, 2),
        'mae_pct_sl': round(mae_pct_sl, 1),
        'mfe_r': round(mfe_r, 2),
        'mod_count': len(op['modifications']),
        'loss_category': loss_category,
        'balance': round(balance, 2),
        'dd_usd': round(dd_usd, 2),
        'dd_pct': round(dd_pct, 2)
    })

print(f'Total processed trades: {len(trades)}')

# 5. Consecutive analysis
max_consec_wins = 0
cur_consec_wins = 0
max_consec_wins_usd = 0.0
cur_consec_wins_usd = 0.0

max_consec_losses = 0
cur_consec_losses = 0
max_consec_losses_usd = 0.0
cur_consec_losses_usd = 0.0

for t in trades:
    if t['pnl'] > 0:
        cur_consec_wins += 1
        cur_consec_wins_usd += t['pnl']
        if cur_consec_wins > max_consec_wins:
            max_consec_wins = cur_consec_wins
            max_consec_wins_usd = cur_consec_wins_usd
        cur_consec_losses = 0
        cur_consec_losses_usd = 0.0
    else:
        cur_consec_losses += 1
        cur_consec_losses_usd += abs(t['pnl'])
        if cur_consec_losses > max_consec_losses:
            max_consec_losses = cur_consec_losses
            max_consec_losses_usd = cur_consec_losses_usd
        cur_consec_wins = 0
        cur_consec_wins_usd = 0.0

# 6. Monthly Breakdown
monthly_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'gp': 0.0, 'gl': 0.0, 'pnl': 0.0, 'sessions': defaultdict(lambda: {'trades': 0, 'wins': 0}), 'setups': defaultdict(lambda: {'trades': 0, 'wins': 0})})

for t in trades:
    m = t['month']
    ms = monthly_stats[m]
    ms['trades'] += 1
    if t['pnl'] > 0:
        ms['wins'] += 1
        ms['gp'] += t['pnl']
    else:
        ms['losses'] += 1
        ms['gl'] += abs(t['pnl'])
    ms['pnl'] += t['pnl']
    
    # Session
    ms['sessions'][t['sub_session']]['trades'] += 1
    if t['pnl'] > 0: ms['sessions'][t['sub_session']]['wins'] += 1
    
    # Setup
    ms['setups'][t['setup']]['trades'] += 1
    if t['pnl'] > 0: ms['setups'][t['setup']]['wins'] += 1

# 7. Winning trades metrics
win_trades = [t for t in trades if t['pnl'] > 0]
avg_win_hold = sum(t['hold_hours'] for t in win_trades) / len(win_trades)
avg_win_mae_pct = sum(t['mae_pct_sl'] for t in win_trades) / len(win_trades)
avg_win_mae_dlr = sum(t['mae_dollars'] for t in win_trades) / len(win_trades)
zero_mae_wins = [t for t in win_trades if t['mae_dollars'] <= 0.30] # within 30 cents (spread breath)

# 8. Loss autopsy
loss_trades = [t for t in trades if t['pnl'] <= 0]
loss_cats = defaultdict(list)
for t in loss_trades:
    loss_cats[t['loss_category']].append(t)

# Output summary JSON
output = {
    'total_trades': len(trades),
    'wins': len(win_trades),
    'losses': len(loss_trades),
    'win_rate': round(len(win_trades)/len(trades)*100.0, 2),
    'net_profit': round(sum(t['pnl'] for t in trades), 2),
    'gross_profit': round(sum(t['pnl'] for t in win_trades), 2),
    'gross_loss': round(sum(abs(t['pnl']) for t in loss_trades), 2),
    'profit_factor': round(sum(t['pnl'] for t in win_trades) / sum(abs(t['pnl']) for t in loss_trades), 2),
    'max_dd_usd': round(max(t['dd_usd'] for t in trades), 2),
    'max_dd_pct': round(max(t['dd_pct'] for t in trades), 2),
    'max_consec_wins': max_consec_wins,
    'max_consec_wins_usd': round(max_consec_wins_usd, 2),
    'max_consec_losses': max_consec_losses,
    'max_consec_losses_usd': round(max_consec_losses_usd, 2),
    'avg_win_hold_hours': round(avg_win_hold, 2),
    'avg_win_mae_pct': round(avg_win_mae_pct, 1),
    'avg_win_mae_dlr': round(avg_win_mae_dlr, 2),
    'zero_mae_wins_count': len(zero_mae_wins),
    'zero_mae_wins_pct': round(len(zero_mae_wins) / len(win_trades) * 100.0, 1),
    'monthly_stats': {m: {
        'trades': ms['trades'],
        'wins': ms['wins'],
        'losses': ms['losses'],
        'win_rate': round(ms['wins']/ms['trades']*100.0, 1),
        'pnl': round(ms['pnl'], 2),
        'sessions': {s: {'trades': v['trades'], 'wins': v['wins'], 'wr': round(v['wins']/v['trades']*100.0, 1)} for s, v in ms['sessions'].items()},
        'setups': {s: {'trades': v['trades'], 'wins': v['wins'], 'wr': round(v['wins']/v['trades']*100.0, 1)} for s, v in ms['setups'].items()}
    } for m, ms in sorted(monthly_stats.items())},
    'loss_categories': {k: len(v) for k, v in loss_cats.items()}
}

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v3_strict_audit.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print('Audit completed successfully!')
print(json.dumps(output, indent=2))
