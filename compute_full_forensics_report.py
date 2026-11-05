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

# 2. Parse 20261102.log run starting at 207435
log_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261102.log'
with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

latest_text = text[207435:]
lines = latest_text.splitlines()

orders = {}
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
re_tag = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*\[(LONDON SNIPER|SWEEP FADE|NY POI)[^\]]*\] Ticket #(\d+)')
re_mod = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*modify #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*close #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+) at price ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
re_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')

closed = []

for l in lines:
    mo = re_open.search(l)
    if mo:
        t_str, tid, cmd, lots, op, sl, tp = mo.groups()
        tid = int(tid)
        orders[tid] = {
            'ticket': tid, 'open_time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'),
            'type': cmd.upper(), 'lots': float(lots), 'open_price': float(op),
            'init_sl': float(sl), 'init_tp': float(tp), 'cur_sl': float(sl), 'cur_tp': float(tp),
            'engine': 'POI NY Sniper'
        }
        continue
    mt = re_tag.search(l)
    if mt:
        t_str, tag, tid = mt.groups()
        tid = int(tid)
        if tid in orders:
            if 'LONDON SNIPER' in tag: orders[tid]['engine'] = 'London Sniper'
            elif 'SWEEP FADE' in tag: orders[tid]['engine'] = 'Judas Sweep Fade'
            elif 'NY POI' in tag:     orders[tid]['engine'] = 'POI NY Sniper'
        continue
    mm = re_mod.search(l)
    if mm:
        t_str, tid, cmd, lots, op, sl, tp = mm.groups()
        tid = int(tid)
        if tid in orders:
            orders[tid]['cur_sl'] = float(sl)
            orders[tid]['cur_tp'] = float(tp)
        else:
            parent_id = tid - 1
            if parent_id in orders:
                parent = orders[parent_id]
                orders[tid] = {
                    'ticket': tid, 'open_time': parent['open_time'], 'type': parent['type'],
                    'lots': float(lots), 'open_price': parent['open_price'],
                    'init_sl': parent['init_sl'], 'init_tp': parent['init_tp'],
                    'cur_sl': float(sl), 'cur_tp': float(tp), 'engine': parent['engine']
                }
        continue
    mc = re_close.search(l)
    if mc:
        t_str, tid, cmd, lots, op, sl, tp, cp = mc.groups()
        tid = int(tid)
        cp = float(cp)
        c_lots = float(lots)
        c_time = datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S')
        if tid in orders:
            ord_info = orders[tid]
            is_buy = (ord_info['type'] == 'BUY')
            pnl = (cp - ord_info['open_price']) * c_lots * 100.0 if is_buy else (ord_info['open_price'] - cp) * c_lots * 100.0
            
            reason = 'PARTIAL_TP_1.5R' if c_lots < ord_info['lots'] else ('SUNSET_EXIT' if c_time.hour == 13 else 'MANUAL_CLOSE')
            closed.append({
                'tid': tid, 'pnl': pnl, 'lots': c_lots, 'reason': reason,
                'open_time': ord_info['open_time'], 'close_time': c_time,
                'type': ord_info['type'], 'open_price': ord_info['open_price'],
                'close_price': cp, 'init_sl': ord_info['init_sl'], 'init_tp': ord_info['init_tp'],
                'cur_sl': ord_info['cur_sl'], 'engine': ord_info['engine']
            })
            if c_lots < ord_info['lots']:
                ord_info['lots'] -= c_lots
        continue
    ms = re_sl.search(l)
    if ms:
        t_str, tid, sl_p = ms.groups()
        tid = int(tid)
        sl_p = float(sl_p)
        c_time = datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S')
        if tid not in orders and (tid - 1) in orders:
            parent = orders[tid - 1]
            orders[tid] = {
                'ticket': tid, 'open_time': parent['open_time'], 'type': parent['type'],
                'lots': parent['lots'], 'open_price': parent['open_price'],
                'init_sl': parent['init_sl'], 'init_tp': parent['init_tp'],
                'cur_sl': parent['cur_sl'], 'cur_tp': parent['cur_tp'], 'engine': parent['engine']
            }
        if tid in orders:
            ord_info = orders[tid]
            is_buy = (ord_info['type'] == 'BUY')
            pnl = (sl_p - ord_info['open_price']) * ord_info['lots'] * 100.0 if is_buy else (ord_info['open_price'] - sl_p) * ord_info['lots'] * 100.0
            reason = 'BE_LOCK' if pnl >= 0 else 'STOP_LOSS'
            closed.append({
                'tid': tid, 'pnl': pnl, 'lots': ord_info['lots'], 'reason': reason,
                'open_time': ord_info['open_time'], 'close_time': c_time,
                'type': ord_info['type'], 'open_price': ord_info['open_price'],
                'close_price': sl_p, 'init_sl': ord_info['init_sl'], 'init_tp': ord_info['init_tp'],
                'cur_sl': ord_info['cur_sl'], 'engine': ord_info['engine']
            })
        continue
    mtp = re_tp.search(l)
    if mtp:
        t_str, tid, tp_p = mtp.groups()
        tid = int(tid)
        tp_p = float(tp_p)
        c_time = datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S')
        if tid not in orders and (tid - 1) in orders:
            parent = orders[tid - 1]
            orders[tid] = {
                'ticket': tid, 'open_time': parent['open_time'], 'type': parent['type'],
                'lots': parent['lots'], 'open_price': parent['open_price'],
                'init_sl': parent['init_sl'], 'init_tp': parent['init_tp'],
                'cur_sl': parent['cur_sl'], 'cur_tp': parent['cur_tp'], 'engine': parent['engine']
            }
        if tid in orders:
            ord_info = orders[tid]
            is_buy = (ord_info['type'] == 'BUY')
            pnl = (tp_p - ord_info['open_price']) * ord_info['lots'] * 100.0 if is_buy else (ord_info['open_price'] - tp_p) * ord_info['lots'] * 100.0
            closed.append({
                'tid': tid, 'pnl': pnl, 'lots': ord_info['lots'], 'reason': 'TAKE_PROFIT',
                'open_time': ord_info['open_time'], 'close_time': c_time,
                'type': ord_info['type'], 'open_price': ord_info['open_price'],
                'close_price': tp_p, 'init_sl': ord_info['init_sl'], 'init_tp': ord_info['init_tp'],
                'cur_sl': ord_info['cur_sl'], 'engine': ord_info['engine']
            })
        continue

print(f"Total parsed closed trades: {len(closed)}")

# Calculate MAE / MFE and Hold Time
for tr in closed:
    ot = tr['open_time']
    ct = tr['close_time']
    dur = (ct - ot).total_seconds() / 3600.0
    tr['hold_hours'] = dur
    
    op = tr['open_price']
    sl = tr['init_sl']
    sl_dist = abs(op - sl)
    is_buy = (tr['type'] == 'BUY')
    
    # Session
    h = ot.hour
    m = ot.minute
    tot_m = h * 60 + m
    if 480 <= tot_m <= 690:
        tr['session'] = 'London (08:00-11:30)'
    elif 900 <= tot_m <= 1230:
        tr['session'] = 'New York (15:00-20:30)'
    else:
        tr['session'] = 'Other'
        
    # Find bars
    max_adv = 0.0
    max_fav = 0.0
    b_start = None
    for b_idx in range(len(bars)):
        if bars[b_idx]['time'] >= ot:
            b_start = b_idx
            break
            
    if b_start is not None:
        for b_idx in range(b_start, len(bars)):
            b = bars[b_idx]
            if b['time'] > ct: break
            if is_buy:
                adv = op - b['low']
                fav = b['high'] - op
            else:
                adv = b['high'] - op
                fav = op - b['low']
            if adv > max_adv: max_adv = adv
            if fav > max_fav: max_fav = fav
            
    tr['mae_usd'] = max_adv
    tr['mae_pts'] = max_adv * 100.0
    tr['mae_pct_sl'] = (max_adv / sl_dist * 100.0) if sl_dist > 0 else 0.0
    tr['mfe_usd'] = max_fav
    tr['mfe_r'] = (max_fav / sl_dist) if sl_dist > 0 else 0.0
    tr['sl_dist'] = sl_dist

wins = [t for t in closed if t['pnl'] > 0]
losses = [t for t in closed if t['pnl'] <= 0]

# Analytics on Wins
avg_win_hold = sum(t['hold_hours'] for t in wins) / len(wins)
avg_win_mae_usd = sum(t['mae_usd'] for t in wins) / len(wins)
avg_win_mae_pct = sum(t['mae_pct_sl'] for t in wins) / len(wins)
immediate_runups = [t for t in wins if t['mae_usd'] <= 0.60]

# Analytics on Losses
straight_traps = [t for t in losses if t['mfe_r'] < 0.50]
gave_back_profit = [t for t in losses if t['mfe_r'] >= 0.50]

print(f"\n=== WINS FORENSICS ===")
print(f"Total Wins: {len(wins)}")
print(f"Average Hold Time: {avg_win_hold:.2f} hours ({avg_win_hold*60:.0f} mins)")
print(f"Average MAE: ${avg_win_mae_usd:.2f} ({avg_win_mae_pct:.1f}% of SL distance)")
print(f"Immediate Runups (MAE <= $0.60): {len(immediate_runups)} trades ({len(immediate_runups)/len(wins)*100:.1f}%)")

print(f"\n=== LOSSES FORENSICS ===")
print(f"Total Losses: {len(losses)}")
print(f"1. Straight Traps / False Breakout (MFE < 0.5R, plunged straight to SL): {len(straight_traps)} trades (${sum(t['pnl'] for t in straight_traps):,.2f})")
print(f"2. Profit First then Reversed to SL (MFE >= 0.5R, was in solid profit): {len(gave_back_profit)} trades (${sum(t['pnl'] for t in gave_back_profit):,.2f})")

# Monthly Table
monthly = defaultdict(list)
for t in closed:
    ym = t['open_time'].strftime('%Y-%m')
    monthly[ym].append(t)

print(f"\n=== MONTHLY BREAKDOWN ===")
monthly_data = {}
for ym in sorted(monthly.keys()):
    trs = monthly[ym]
    m_w = [t for t in trs if t['pnl'] > 0]
    m_l = [t for t in trs if t['pnl'] <= 0]
    pnl = sum(t['pnl'] for t in trs)
    wr = len(m_w) / len(trs) * 100.0
    
    # Session breakdown
    lon_trs = [t for t in trs if 'London' in t['session']]
    lon_w = [t for t in lon_trs if t['pnl'] > 0]
    lon_wr = len(lon_w) / len(lon_trs) * 100.0 if lon_trs else 0.0
    lon_pnl = sum(t['pnl'] for t in lon_trs)
    
    ny_trs = [t for t in trs if 'New York' in t['session']]
    ny_w = [t for t in ny_trs if t['pnl'] > 0]
    ny_wr = len(ny_w) / len(ny_trs) * 100.0 if ny_trs else 0.0
    ny_pnl = sum(t['pnl'] for t in ny_trs)
    
    # Engine breakdown
    eng_counts = {}
    for eng in ['London Sniper', 'Judas Sweep Fade', 'POI NY Sniper']:
        e_trs = [t for t in trs if t['engine'] == eng]
        e_w = [t for t in e_trs if t['pnl'] > 0]
        eng_counts[eng] = {
            'trades': len(e_trs),
            'wins': len(e_w),
            'wr': len(e_w)/len(e_trs)*100.0 if e_trs else 0.0,
            'pnl': sum(t['pnl'] for t in e_trs)
        }
        
    monthly_data[ym] = {
        'trades': len(trs),
        'wins': len(m_w),
        'losses': len(m_l),
        'wr': wr,
        'pnl': pnl,
        'london': {'trades': len(lon_trs), 'wins': len(lon_w), 'wr': lon_wr, 'pnl': lon_pnl},
        'ny': {'trades': len(ny_trs), 'wins': len(ny_w), 'wr': ny_wr, 'pnl': ny_pnl},
        'engines': eng_counts
    }
    
    print(f"{ym} | Trades: {len(trs):2d} | Wins: {len(m_w):2d} ({wr:5.1f}%) | PnL: ${pnl:+9.2f} | London: {len(lon_trs)} tr ({lon_wr:4.1f}%, ${lon_pnl:+7.2f}) | NY: {len(ny_trs)} tr ({ny_wr:4.1f}%, ${ny_pnl:+7.2f})")

# Streaks
curr_w_cnt = 0
curr_w_sum = 0.0
max_w_cnt = 0
max_w_sum = 0.0

curr_l_cnt = 0
curr_l_sum = 0.0
max_l_cnt = 0
max_l_sum = 0.0

for t in closed:
    if t['pnl'] > 0:
        curr_w_cnt += 1
        curr_w_sum += t['pnl']
        if curr_w_cnt > max_w_cnt or (curr_w_cnt == max_w_cnt and curr_w_sum > max_w_sum):
            max_w_cnt = curr_w_cnt
            max_w_sum = curr_w_sum
        curr_l_cnt = 0
        curr_l_sum = 0.0
    else:
        curr_l_cnt += 1
        curr_l_sum += t['pnl']
        if curr_l_cnt > max_l_cnt or (curr_l_cnt == max_l_cnt and curr_l_sum < max_l_sum):
            max_l_cnt = curr_l_cnt
            max_l_sum = curr_l_sum
        curr_w_cnt = 0
        curr_w_sum = 0.0

print(f"\n=== STREAKS ===")
print(f"Max Consecutive Wins: {max_w_cnt} trades | Total Profit: ${max_w_sum:,.2f}")
print(f"Max Consecutive Losses: {max_l_cnt} trades | Total Loss: ${max_l_sum:,.2f}")

# Engine Totals
print(f"\n=== ENGINE TOTALS ===")
for eng in ['London Sniper', 'Judas Sweep Fade', 'POI NY Sniper']:
    e_trs = [t for t in closed if t['engine'] == eng]
    e_w = [t for t in e_trs if t['pnl'] > 0]
    e_pnl = sum(t['pnl'] for t in e_trs)
    print(f"[{eng:16s}] Trades: {len(e_trs):3d} | Wins: {len(e_w):3d} ({len(e_w)/len(e_trs)*100:5.1f}%) | Total Net: ${e_pnl:+10.2f}")

# Save full results json
full_res = {
    'summary': {
        'total_trades': len(closed),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': len(wins)/len(closed)*100.0,
        'gross_profit': sum(t['pnl'] for t in wins),
        'gross_loss': abs(sum(t['pnl'] for t in losses)),
        'net_profit': sum(t['pnl'] for t in closed),
        'profit_factor': sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses)),
        'avg_win_hold_hours': avg_win_hold,
        'avg_win_mae_usd': avg_win_mae_usd,
        'avg_win_mae_pct': avg_win_mae_pct,
        'immediate_runups': len(immediate_runups),
        'immediate_runups_pct': len(immediate_runups)/len(wins)*100.0,
        'straight_traps': len(straight_traps),
        'straight_traps_pnl': sum(t['pnl'] for t in straight_traps),
        'gave_back_profit': len(gave_back_profit),
        'gave_back_profit_pnl': sum(t['pnl'] for t in gave_back_profit),
        'max_win_streak': max_w_cnt,
        'max_win_streak_pnl': max_w_sum,
        'max_loss_streak': max_l_cnt,
        'max_loss_streak_pnl': max_l_sum
    },
    'monthly': monthly_data
}

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v3_5_official_200_trades_forensic.json', 'w') as f:
    json.dump(full_res, f, indent=2)
print("\nSaved v3_5_official_200_trades_forensic.json successfully.")
