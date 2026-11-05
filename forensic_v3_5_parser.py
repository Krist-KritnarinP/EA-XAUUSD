import re, json, struct, math
from datetime import datetime
from collections import defaultdict

# 1. Load M15 bars from GOLD15.hst for MAE / MFE calculation
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

# 2. Parse 20261102.log
log_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261102.log'
with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

lines = text.splitlines()

# Patterns
# Open log:
# 2026.10.07 10:45:00  Gold_POI_Sniper_Tester_v3_5 GOLD,M15: open #196 sell 1.16 GOLD at 4132.70 sl: 4139.45 tp: 4109.07 ok
# 2026.10.07 10:45:00  Gold_POI_Sniper_Tester_v3_5 GOLD,M15: [LONDON SNIPER SELL] Ticket #196 Lots: 1.16 Price: 4132.70 SL: 4139.45 (6.75 USD) TP: 4109.07 (23.63 USD)
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
re_tag = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*\[(LONDON SNIPER|SWEEP FADE|NY POI)[^\]]*\] Ticket #(\d+)')
re_mod = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*modify #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*close #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+) at price ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
re_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')

trades = {}

for l in lines:
    mo = re_open.search(l)
    if mo:
        t_str, t_id, cmd, lots, op, sl, tp = mo.groups()
        t_id = int(t_id)
        trades[t_id] = {
            'ticket': t_id,
            'open_time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'),
            'type': cmd.upper(),
            'lots': float(lots),
            'open_price': float(op),
            'init_sl': float(sl),
            'init_tp': float(tp),
            'engine': 'NY POI', # default
            'modifications': [],
            'close_time': None,
            'close_price': None,
            'close_reason': None,
            'pnl': 0.0
        }
        continue

    mt = re_tag.search(l)
    if mt:
        t_str, tag, t_id = mt.groups()
        t_id = int(t_id)
        if t_id in trades:
            if 'LONDON SNIPER' in tag: trades[t_id]['engine'] = 'London Sniper'
            elif 'SWEEP FADE' in tag: trades[t_id]['engine'] = 'Judas Sweep Fade'
            elif 'NY POI' in tag:     trades[t_id]['engine'] = 'POI NY Sniper'
        continue

    mm = re_mod.search(l)
    if mm:
        t_str, t_id, cmd, lots, op, sl, tp = mm.groups()
        t_id = int(t_id)
        if t_id in trades:
            trades[t_id]['modifications'].append({
                'time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'),
                'sl': float(sl),
                'tp': float(tp)
            })
        continue

    mc = re_close.search(l)
    if mc:
        t_str, t_id, cmd, lots, op, sl, tp, cp = mc.groups()
        t_id = int(t_id)
        if t_id in trades:
            trades[t_id]['close_time'] = datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S')
            trades[t_id]['close_price'] = float(cp)
            if 'sunset' in l.lower():
                trades[t_id]['close_reason'] = 'SUNSET_EXIT'
            elif 'structural' in l.lower():
                trades[t_id]['close_reason'] = 'STRUCTURAL_BAILOUT'
            else:
                trades[t_id]['close_reason'] = 'MANUAL_CLOSE'
        continue

    ms = re_sl.search(l)
    if ms:
        t_str, t_id, sp = ms.groups()
        t_id = int(t_id)
        if t_id in trades:
            trades[t_id]['close_time'] = datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S')
            trades[t_id]['close_price'] = float(sp)
            # Check if this was a Breakeven stop or actual loss
            tr = trades[t_id]
            is_buy = (tr['type'] == 'BUY')
            pnl_pts = (float(sp) - tr['open_price']) if is_buy else (tr['open_price'] - float(sp))
            if pnl_pts >= -0.10:
                trades[t_id]['close_reason'] = 'BE_LOCK'
            else:
                trades[t_id]['close_reason'] = 'STOP_LOSS'
        continue

    mtp = re_tp.search(l)
    if mtp:
        t_str, t_id, tp = mtp.groups()
        t_id = int(t_id)
        if t_id in trades:
            trades[t_id]['close_time'] = datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S')
            trades[t_id]['close_price'] = float(tp)
            trades[t_id]['close_reason'] = 'TAKE_PROFIT'
        continue

# 3. Calculate exact PnL and MAE/MFE for each trade
sorted_tickets = sorted(list(trades.keys()))
print(f"Total parsed trades: {len(sorted_tickets)}")

# Initial deposit $2,000
balance = 2000.0

for tid in sorted_tickets:
    tr = trades[tid]
    is_buy = (tr['type'] == 'BUY')
    op = tr['open_price']
    cp = tr['close_price'] if tr['close_price'] is not None else op
    lots = tr['lots']
    
    if is_buy:
        pnl = (cp - op) * lots * 100.0
    else:
        pnl = (op - cp) * lots * 100.0
    tr['pnl'] = pnl
    tr['win'] = (pnl > 0)
    
    # Holding duration
    ot = tr['open_time']
    ct = tr['close_time'] if tr['close_time'] is not None else ot
    dur_hours = (ct - ot).total_seconds() / 3600.0
    tr['dur_hours'] = dur_hours
    
    # MAE (Maximum Adverse Excursion) & MFE (Maximum Favorable Excursion)
    # Search bars between ot and ct
    sl_dist = abs(op - tr['init_sl'])
    max_adv = 0.0 # max drawdown in price against position
    max_fav = 0.0 # max profit in price in favor of position
    
    # Find start bar
    # Find bar with time closest to ot
    b_start = None
    for b_idx in range(len(bars)):
        if bars[b_idx]['time'] >= ot:
            b_start = b_idx
            break
            
    if b_start is not None:
        for b_idx in range(b_start, len(bars)):
            b = bars[b_idx]
            if b['time'] > ct:
                break
            if is_buy:
                adv = op - b['low']
                fav = b['high'] - op
            else:
                adv = b['high'] - op
                fav = op - b['low']
            if adv > max_adv: max_adv = adv
            if fav > max_fav: max_fav = fav
            
    tr['mae_usd'] = max_adv
    tr['mae_pct_sl'] = (max_adv / sl_dist * 100.0) if sl_dist > 0 else 0.0
    tr['mfe_usd'] = max_fav
    tr['mfe_r'] = (max_fav / sl_dist) if sl_dist > 0 else 0.0
    tr['sl_dist'] = sl_dist

# 4. Forensics Analytics
wins = [tr for tr in trades.values() if tr['win']]
losses = [tr for tr in trades.values() if not tr['win']]

print(f"Total Wins: {len(wins)} | Total Losses: {len(losses)}")
print(f"Total Net Profit: ${sum(tr['pnl'] for tr in trades.values()):,.2f}")

# A. Monthly breakdown
monthly = defaultdict(list)
for tr in trades.values():
    ym = tr['open_time'].strftime('%Y-%m')
    monthly[ym].append(tr)

# B. Engine breakdown
by_engine = defaultdict(list)
for tr in trades.values():
    by_engine[tr['engine']].append(tr)

# C. Session breakdown
# London: 08:00 - 11:30 | NY: 15:00 - 20:30
def get_session(t):
    h, m = t.hour, t.minute
    total_m = h * 60 + m
    if 480 <= total_m <= 690:
        return 'London Session (08:00-11:30)'
    elif 900 <= total_m <= 1230:
        return 'NY Session (15:00-20:30)'
    return 'Other'

# D. Streaks
curr_w_streak = 0
curr_w_pnl = 0.0
max_w_streak = 0
max_w_pnl = 0.0

curr_l_streak = 0
curr_l_pnl = 0.0
max_l_streak = 0
max_l_pnl = 0.0

for tid in sorted_tickets:
    tr = trades[tid]
    if tr['win']:
        curr_w_streak += 1
        curr_w_pnl += tr['pnl']
        if curr_w_streak > max_w_streak or (curr_w_streak == max_w_streak and curr_w_pnl > max_w_pnl):
            max_w_streak = curr_w_streak
            max_w_pnl = curr_w_pnl
        curr_l_streak = 0
        curr_l_pnl = 0.0
    else:
        curr_l_streak += 1
        curr_l_pnl += tr['pnl']
        if curr_l_streak > max_l_streak or (curr_l_streak == max_l_streak and curr_l_pnl < max_l_pnl):
            max_l_streak = curr_l_streak
            max_l_pnl = curr_l_pnl
        curr_w_streak = 0
        curr_w_pnl = 0.0

# E. Loss Autopsy
loss_straight_trap = [] # plunged straight to SL, never even reached +0.5R
loss_gave_back_profit = [] # reached >= +0.5R but did not reach TP / BE, reversed to SL
loss_be_break = [] # closed at BE or small profit/loss
loss_structural = [] # structural bailout

for tr in losses:
    if tr['close_reason'] == 'BE_LOCK' or abs(tr['pnl']) < 10.0:
        loss_be_break.append(tr)
    elif tr['close_reason'] == 'STRUCTURAL_BAILOUT':
        loss_structural.append(tr)
    elif tr['mfe_r'] >= 0.50:
        loss_gave_back_profit.append(tr)
    else:
        loss_straight_trap.append(tr)

# F. Win Quality
avg_win_hold = sum(w['dur_hours'] for w in wins) / len(wins)
avg_win_mae = sum(w['mae_usd'] for w in wins) / len(wins)
avg_win_mae_pct = sum(w['mae_pct_sl'] for w in wins) / len(wins)
immediate_runups = [w for w in wins if w['mae_usd'] <= 0.60]

# G. Drawdown
bal = 2000.0
peak_bal = 2000.0
max_drawdown_usd = 0.0
max_drawdown_pct = 0.0

for tid in sorted_tickets:
    tr = trades[tid]
    bal += tr['pnl']
    if bal > peak_bal: peak_bal = bal
    dd_usd = peak_bal - bal
    dd_pct = (dd_usd / peak_bal) * 100.0
    if dd_usd > max_drawdown_usd: max_drawdown_usd = dd_usd
    if dd_pct > max_drawdown_pct: max_drawdown_pct = dd_pct

# Save full forensic json
summary = {
    'total_trades': len(trades),
    'wins': len(wins),
    'losses': len(losses),
    'win_rate': len(wins) / len(trades) * 100.0,
    'net_profit': sum(tr['pnl'] for tr in trades.values()),
    'profit_factor': sum(w['pnl'] for w in wins) / abs(sum(l['pnl'] for l in losses)),
    'max_drawdown_usd': max_drawdown_usd,
    'max_drawdown_pct': max_drawdown_pct,
    'avg_win_hold_hours': avg_win_hold,
    'avg_win_mae_usd': avg_win_mae,
    'avg_win_mae_pct_sl': avg_win_mae_pct,
    'immediate_runups_count': len(immediate_runups),
    'immediate_runups_pct': len(immediate_runups) / len(wins) * 100.0,
    'max_win_streak': max_w_streak,
    'max_win_streak_pnl': max_w_pnl,
    'max_loss_streak': max_l_streak,
    'max_loss_streak_pnl': max_l_pnl,
    'loss_straight_trap_count': len(loss_straight_trap),
    'loss_straight_trap_pnl': sum(l['pnl'] for l in loss_straight_trap),
    'loss_gave_back_profit_count': len(loss_gave_back_profit),
    'loss_gave_back_profit_pnl': sum(l['pnl'] for l in loss_gave_back_profit),
    'loss_be_break_count': len(loss_be_break),
    'loss_be_break_pnl': sum(l['pnl'] for l in loss_be_break),
    'loss_structural_count': len(loss_structural),
    'loss_structural_pnl': sum(l['pnl'] for l in loss_structural)
}

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v3_5_forensic_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\n=== SUMMARY FORENSICS ===")
print(json.dumps(summary, indent=2))

print("\n=== MONTHLY BREAKDOWN ===")
for ym in sorted(monthly.keys()):
    m_trs = monthly[ym]
    m_w = [t for t in m_trs if t['win']]
    m_l = [t for t in m_trs if not t['win']]
    m_pnl = sum(t['pnl'] for t in m_trs)
    m_wr = len(m_w) / len(m_trs) * 100.0
    print(f"{ym} | Trades: {len(m_trs):2d} | Wins: {len(m_w):2d} ({m_wr:5.1f}%) | Net: ${m_pnl:+9.2f}")
    
    # Engine breakdown in month
    m_eng = defaultdict(list)
    for t in m_trs: m_eng[t['engine']].append(t)
    for eng, etrs in m_eng.items():
        ew = [t for t in etrs if t['win']]
        epnl = sum(t['pnl'] for t in etrs)
        ewr = len(ew) / len(etrs) * 100.0
        print(f"   [{eng:16s}] Trades: {len(etrs):2d} | Wins: {len(ew):2d} ({ewr:5.1f}%) | PnL: ${epnl:+8.2f}")

print("\n=== ENGINE TOTALS ===")
for eng, etrs in by_engine.items():
    ew = [t for t in etrs if t['win']]
    epnl = sum(t['pnl'] for t in etrs)
    ewr = len(ew) / len(etrs) * 100.0
    print(f"[{eng:16s}] Total Trades: {len(etrs):3d} | Wins: {len(ew):3d} ({ewr:5.1f}%) | Total Net: ${epnl:+10.2f}")
