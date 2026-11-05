import re
from datetime import datetime
from collections import defaultdict

log_path = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261016.log'
with open(log_path, 'r', encoding='latin1') as f:
    lines = f.readlines()

orders = {}

# Patterns:
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_5_beta GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+)')
re_engine = re.compile(r'Ticket: #(\d+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_5_beta GOLD,M15: close #(\d+) (buy|sell) [\d\.]+ GOLD at [\d\.]+ sl: [\d\.]+ tp: [\d\.]+ at price ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
re_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')

for line in lines:
    m = re_open.search(line)
    if m:
        t_time, ticket, o_type, lots, o_price = m.groups()
        ticket = int(ticket)
        orders[ticket] = {
            'ticket': ticket,
            'open_time': t_time,
            'type': o_type.upper(),
            'lots': float(lots),
            'open_price': float(o_price),
            'engine': 'Unknown',
            'close_time': None,
            'close_price': None,
            'close_reason': 'Unknown',
            'pnl': 0.0
        }
    if 'GoldSniper_Tester_v6_3_5_beta GOLD,M15: [' in line:
        m_t = re_engine.search(line)
        if m_t:
            ticket = int(m_t.group(1))
            if ticket in orders:
                if 'SNIPER RUNNER' in line:
                    orders[ticket]['engine'] = 'London Sniper'
                elif 'NEW YORK TREND-RIDER' in line:
                    orders[ticket]['engine'] = 'New York Trend-Rider'
                elif 'ASIAN BOX SWEEP FADE' in line:
                    orders[ticket]['engine'] = 'Sweep Fade (Asian Box)'
                elif 'SWEEP FADE' in line:
                    orders[ticket]['engine'] = 'Sweep Fade (EMA50 Trap)'
                elif 'ASIAN SQUEEZE' in line:
                    orders[ticket]['engine'] = 'Asian Scalper'

    m_c = re_close.search(line)
    if m_c:
        c_time, ticket, _, c_price = m_c.groups()
        ticket = int(ticket)
        if ticket in orders:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['close_reason'] = 'Sunset Exit / Manual'

    m_sl = re_sl.search(line)
    if m_sl:
        c_time, ticket, c_price = m_sl.groups()
        ticket = int(ticket)
        if ticket in orders:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['close_reason'] = 'Stop Loss'

    m_tp = re_tp.search(line)
    if m_tp:
        c_time, ticket, c_price = m_tp.groups()
        ticket = int(ticket)
        if ticket in orders:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['close_reason'] = 'Take Profit'

# Compute PnL
# Contract size for GOLD on XM = 100
total_pnl = 0.0
gross_profit = 0.0
gross_loss = 0.0

for t, o in orders.items():
    if o['close_price'] is not None:
        if o['type'] == 'BUY':
            pnl = (o['close_price'] - o['open_price']) * o['lots'] * 100.0
        else:
            pnl = (o['open_price'] - o['close_price']) * o['lots'] * 100.0
        o['pnl'] = round(pnl, 2)
        total_pnl += o['pnl']
        if o['pnl'] > 0:
            gross_profit += o['pnl']
        else:
            gross_loss += abs(o['pnl'])

print(f"Total Parsed Orders: {len(orders)}")
print(f"Total Net PnL: ${total_pnl:.2f} (Gross Profit: ${gross_profit:.2f}, Gross Loss: -${gross_loss:.2f})")
print(f"Profit Factor: {(gross_profit/gross_loss):.2f}" if gross_loss > 0 else "PF: inf")

# Breakdown by Engine
eng_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gp': 0.0, 'gl': 0.0})
for t, o in orders.items():
    eng = o['engine']
    eng_stats[eng]['trades'] += 1
    eng_stats[eng]['pnl'] += o['pnl']
    if o['pnl'] > 0:
        eng_stats[eng]['wins'] += 1
        eng_stats[eng]['gp'] += o['pnl']
    else:
        eng_stats[eng]['losses'] += 1
        eng_stats[eng]['gl'] += abs(o['pnl'])

print("\n================== ENGINE BREAKDOWN ==================")
for eng, s in sorted(eng_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
    wr = (s['wins'] / s['trades'] * 100) if s['trades'] > 0 else 0
    pf = (s['gp'] / s['gl']) if s['gl'] > 0 else 99.0
    print(f"{eng:25}: Trades={s['trades']:3}, WinRate={wr:5.1f}%, PnL=${s['pnl']:8.2f}, PF={pf:4.2f}, GP=${s['gp']:7.2f}, GL=${s['gl']:7.2f}")

# Breakdown by Day of Week
dow_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gp': 0.0, 'gl': 0.0})
dow_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

for t, o in orders.items():
    dt = datetime.strptime(o['open_time'], '%Y.%m.%d %H:%M:%S')
    dow = dow_names[dt.weekday()]
    dow_stats[dow]['trades'] += 1
    dow_stats[dow]['pnl'] += o['pnl']
    if o['pnl'] > 0:
        dow_stats[dow]['wins'] += 1
        dow_stats[dow]['gp'] += o['pnl']
    else:
        dow_stats[dow]['losses'] += 1
        dow_stats[dow]['gl'] += abs(o['pnl'])

print("\n================== DAY OF WEEK BREAKDOWN ==================")
for dow in dow_order:
    s = dow_stats[dow]
    wr = (s['wins'] / s['trades'] * 100) if s['trades'] > 0 else 0
    pf = (s['gp'] / s['gl']) if s['gl'] > 0 else 99.0
    print(f"{dow}: Trades={s['trades']:3}, WinRate={wr:5.1f}%, PnL=${s['pnl']:8.2f}, PF={pf:4.2f}, GP=${s['gp']:7.2f}, GL=${s['gl']:7.2f}")

# Breakdown by Month
monthly_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gp': 0.0, 'gl': 0.0})
for t, o in orders.items():
    dt = datetime.strptime(o['open_time'], '%Y.%m.%d %H:%M:%S')
    m_key = dt.strftime('%Y-%m')
    monthly_stats[m_key]['trades'] += 1
    monthly_stats[m_key]['pnl'] += o['pnl']
    if o['pnl'] > 0:
        monthly_stats[m_key]['wins'] += 1
        monthly_stats[m_key]['gp'] += o['pnl']
    else:
        monthly_stats[m_key]['losses'] += 1
        monthly_stats[m_key]['gl'] += abs(o['pnl'])

print("\n================== MONTHLY BREAKDOWN ==================")
for m_key in sorted(monthly_stats.keys()):
    s = monthly_stats[m_key]
    wr = (s['wins'] / s['trades'] * 100) if s['trades'] > 0 else 0
    pf = (s['gp'] / s['gl']) if s['gl'] > 0 else 99.0
    print(f"{m_key}: Trades={s['trades']:2}, WinRate={wr:5.1f}%, PnL=${s['pnl']:8.2f}, PF={pf:4.2f}")

# Breakdown by BUY vs SELL
type_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gp': 0.0, 'gl': 0.0})
for t, o in orders.items():
    typ = o['type']
    type_stats[typ]['trades'] += 1
    type_stats[typ]['pnl'] += o['pnl']
    if o['pnl'] > 0:
        type_stats[typ]['wins'] += 1
        type_stats[typ]['gp'] += o['pnl']
    else:
        type_stats[typ]['losses'] += 1
        type_stats[typ]['gl'] += abs(o['pnl'])

print("\n================== DIRECTION ASYMMETRY (BUY vs SELL) ==================")
for typ in ['BUY', 'SELL']:
    s = type_stats[typ]
    wr = (s['wins'] / s['trades'] * 100) if s['trades'] > 0 else 0
    pf = (s['gp'] / s['gl']) if s['gl'] > 0 else 99.0
    print(f"{typ:4}: Trades={s['trades']:3}, WinRate={wr:5.1f}%, PnL=${s['pnl']:8.2f}, PF={pf:4.2f}, GP=${s['gp']:7.2f}, GL=${s['gl']:7.2f}")

# Find losing streaks and drawdown sequence
cur_loss_streak = []
max_loss_streak = []
cur_loss_sum = 0.0
max_loss_sum = 0.0

cur_win_streak = []
max_win_streak = []

equity = 2000.0
peak_equity = 2000.0
max_dd = 0.0
dd_period = None

for t in sorted(orders.keys()):
    o = orders[t]
    pnl = o['pnl']
    equity += pnl
    if equity > peak_equity:
        peak_equity = equity
    dd = peak_equity - equity
    if dd > max_dd:
        max_dd = dd
        dd_period = (peak_equity, equity, o['close_time'])

    if pnl <= 0:
        cur_loss_streak.append(o)
        cur_loss_sum += pnl
        if len(cur_loss_streak) > len(max_loss_streak):
            max_loss_streak = list(cur_loss_streak)
            max_loss_sum = cur_loss_sum
        cur_win_streak = []
    else:
        cur_win_streak.append(o)
        if len(cur_win_streak) > len(max_win_streak):
            max_win_streak = list(cur_win_streak)
        cur_loss_streak = []
        cur_loss_sum = 0.0

print(f"\n================== STREAK & DRAWDOWN FORENSICS ==================")
print(f"Max Consecutive Loss Streak: {len(max_loss_streak)} trades, Total Loss: ${max_loss_sum:.2f}")
print("Trades in max losing streak:")
for o in max_loss_streak:
    print(f"  #{o['ticket']} ({o['engine']}) {o['type']} {o['lots']} lots | Open: {o['open_time']} | Close: {o['close_time']} | PnL: ${o['pnl']:.2f} ({o['close_reason']})")

print(f"\nMax Consecutive Win Streak: {len(max_win_streak)} trades")
print(f"Peak Drawdown: ${max_dd:.2f} at {dd_period[2] if dd_period else 'N/A'}")
