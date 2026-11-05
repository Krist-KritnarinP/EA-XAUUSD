import re
import json
from datetime import datetime
from collections import defaultdict

with open(r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log', 'r', encoding='latin-1') as f:
    lines = f.readlines()[80443:81192]

trades = {}
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*close #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+) at price ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+Tester: (?:take profit|stop loss) #(\d+) at ([\d\.]+)')
re_mod = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*modify #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
re_bailout = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*STRUCTURAL BAILOUT.*Closing Ticket #(\d+)')

for l in lines:
    mo = re_open.search(l)
    if mo:
        t_time, ticket, t_type, lots, o_price, sl, tp = mo.groups()
        trades[ticket] = {
            'ticket': int(ticket),
            'open_time': t_time,
            'type': t_type.upper(),
            'lots': float(lots),
            'open_price': float(o_price),
            'init_sl': float(sl),
            'init_tp': float(tp),
            'modifications': [],
            'close_time': None,
            'close_price': None,
            'close_reason': None
        }
    mm = re_mod.search(l)
    if mm:
        m_time, ticket, t_type, lots, o_p, sl, tp = mm.groups()
        if ticket in trades:
            trades[ticket]['modifications'].append((m_time, float(sl), float(tp)))
    mb = re_bailout.search(l)
    if mb:
        b_time, ticket = mb.groups()
        if ticket in trades:
            trades[ticket]['close_reason'] = 'STRUCTURAL_BAILOUT'
    mc = re_close.search(l)
    if mc:
        c_time, ticket, t_type, lots, o_price, sl, tp, c_price = mc.groups()
        if ticket in trades:
            trades[ticket]['close_time'] = c_time
            trades[ticket]['close_price'] = float(c_price)
            if not trades[ticket]['close_reason']:
                trades[ticket]['close_reason'] = 'MANUAL_OR_BAILOUT'
    ms = re_sl.search(l)
    if ms:
        s_time, ticket, s_price = ms.groups()
        if ticket in trades:
            trades[ticket]['close_time'] = s_time
            trades[ticket]['close_price'] = float(s_price)
            if 'take profit' in l.lower():
                trades[ticket]['close_reason'] = 'TAKE_PROFIT'
            elif 'stop loss' in l.lower():
                trades[ticket]['close_reason'] = 'STOP_LOSS'

trade_list = sorted(trades.values(), key=lambda x: x['ticket'])
for t in trade_list:
    o_dt = datetime.strptime(t['open_time'], '%Y.%m.%d %H:%M:%S')
    c_dt = datetime.strptime(t['close_time'], '%Y.%m.%d %H:%M:%S') if t['close_time'] else o_dt
    t['duration_hours'] = round((c_dt - o_dt).total_seconds() / 3600.0, 2)
    t['month'] = o_dt.strftime('%Y-%m')
    t['hour'] = o_dt.hour
    if 15 <= t['hour'] < 18:
        t['session'] = 'NY Open (15:00-18:00)'
    else:
        t['session'] = 'NY Late (18:00-20:30)'
        
    diff = (t['close_price'] - t['open_price']) if t['type'] == 'BUY' else (t['open_price'] - t['close_price'])
    t['profit_usd'] = round(diff * t['lots'] * 100.0, 2)
    sl_dist = abs(t['open_price'] - t['init_sl'])
    t['profit_r'] = round(diff / sl_dist, 2) if sl_dist > 0 else 0.0

# 1. Monthly trade count & profit
monthly = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'profit': 0.0, 'sessions': defaultdict(lambda: {'trades': 0, 'wins': 0, 'profit': 0.0})})
for t in trade_list:
    m = t['month']
    monthly[m]['trades'] += 1
    monthly[m]['profit'] += t['profit_usd']
    sess = t['session']
    monthly[m]['sessions'][sess]['trades'] += 1
    monthly[m]['sessions'][sess]['profit'] += t['profit_usd']
    if t['profit_usd'] > 0:
        monthly[m]['wins'] += 1
        monthly[m]['sessions'][sess]['wins'] += 1
    else:
        monthly[m]['losses'] += 1

print('=== MONTHLY PERFORMANCE ===')
for m, data in sorted(monthly.items()):
    wr = (data['wins'] / data['trades']) * 100 if data['trades'] > 0 else 0
    print(f'{m}: {data["trades"]} trades | Wins: {data["wins"]} ({wr:.1f}%) | Profit: ${data["profit"]:,.2f}')
    for s, sdata in sorted(data['sessions'].items()):
        swr = (sdata['wins'] / sdata['trades']) * 100 if sdata['trades'] > 0 else 0
        print(f'   - {s}: {sdata["trades"]} trades | WinRate {swr:.1f}% ({sdata["wins"]}/{sdata["trades"]}) | Profit: ${sdata["profit"]:,.2f}')

# 2. Holding hours
win_durations = [t['duration_hours'] for t in trade_list if t['profit_usd'] > 0]
loss_durations = [t['duration_hours'] for t in trade_list if t['profit_usd'] <= 0]
print('\n=== HOLDING TIME ===')
print(f'Win holding hours: Avg {sum(win_durations)/len(win_durations):.2f}h | Min {min(win_durations):.2f}h | Max {max(win_durations):.2f}h')
print(f'Loss holding hours: Avg {sum(loss_durations)/len(loss_durations):.2f}h | Min {min(loss_durations):.2f}h | Max {max(loss_durations):.2f}h')

# 3. Breakeven moves & immediate profit
be_trades = [t for t in trade_list if len(t['modifications']) > 0]
be_tp_wins = [t for t in be_trades if t['close_reason'] == 'TAKE_PROFIT']
be_hit_sl = [t for t in be_trades if t['close_reason'] == 'STOP_LOSS']

print('\n=== BREAKEVEN & TRAIL ANALYSIS ===')
print(f'Total trades where BE was triggered (+1.8R): {len(be_trades)}')
print(f'  - Reached full TP (+3.5R): {len(be_tp_wins)} trades')
print(f'  - Returned to Breakeven (+0.3R buffer locked): {len(be_hit_sl)} trades')
for b in be_hit_sl[:5]:
    print(f'    * Ticket #{b["ticket"]} {b["type"]} Lots {b["lots"]} Open {b["open_price"]} Close {b["close_price"]} Profit ${b["profit_usd"]}')

# 4. Losses autopsy
print('\n=== LOSSES AUTOPSY ===')
sl_hit_full = [t for t in trade_list if t['profit_usd'] < 0 and t['close_reason'] == 'STOP_LOSS' and len(t['modifications']) == 0]
bailouts = [t for t in trade_list if t['close_reason'] == 'STRUCTURAL_BAILOUT']
be_small_wins = [t for t in be_hit_sl if t['profit_usd'] > 0]

print(f'Total losing trades: {len([t for t in trade_list if t["profit_usd"] <= 0])}')
print(f'1) Direct Full SL (Fakeout liquidity sweep before reaching BE): {len(sl_hit_full)} trades')
print(f'2) Structural Bailout (AI/System cut trade early upon opposite reversal bar): {len(bailouts)} trades')
print(f'3) Locked Breakeven protected trades (went to +1.8R, returned and closed in slight green buffer): {len(be_small_wins)} trades')

# Streaks
streaks_w = []
streaks_l = []
cur_cw = 0; cur_cw_profit = 0; temp_w_trades = []
cur_cl = 0; cur_cl_loss = 0; temp_l_trades = []

for t in trade_list:
    if t['profit_usd'] > 0:
        if cur_cl > 0:
            streaks_l.append((cur_cl, cur_cl_loss, temp_l_trades))
            cur_cl = 0; cur_cl_loss = 0; temp_l_trades = []
        cur_cw += 1
        cur_cw_profit += t['profit_usd']
        temp_w_trades.append(t)
    else:
        if cur_cw > 0:
            streaks_w.append((cur_cw, cur_cw_profit, temp_w_trades))
            cur_cw = 0; cur_cw_profit = 0; temp_w_trades = []
        cur_cl += 1
        cur_cl_loss += t['profit_usd']
        temp_l_trades.append(t)

if cur_cw > 0:
    streaks_w.append((cur_cw, cur_cw_profit, temp_w_trades))
if cur_cl > 0:
    streaks_l.append((cur_cl, cur_cl_loss, temp_l_trades))

streaks_w.sort(key=lambda x: x[0], reverse=True)
streaks_l.sort(key=lambda x: x[0], reverse=True)

print('\n=== STREAKS ===')
print(f'Max Consecutive Wins: {streaks_w[0][0]} trades | Total Streak Profit: +${streaks_w[0][1]:,.2f}')
print(f'Max Consecutive Losses: {streaks_l[0][0]} trades | Total Streak Loss: ${streaks_l[0][1]:,.2f}')
for l in streaks_l[0][2]:
    print(f'   - Ticket #{l["ticket"]} ({l["open_time"]}) {l["type"]} Lots {l["lots"]} Profit ${l["profit_usd"]:.2f} ({l["close_reason"]})')
