import re
import datetime
import json

log_path = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261013.log'

with open(log_path, 'r', encoding='cp1252', errors='ignore') as f:
    lines = f.readlines()

v632_lines = lines[224:555]

trades = {}
open_order_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_2 GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
# [NEW YORK TREND-RIDER SELL v6.3.2] Ticket: #50
engine_pattern = re.compile(r'\[(NEW YORK TREND-RIDER|SNIPER RUNNER|ASIAN SQUEEZE).*?\]\s+Ticket:\s+#(\d+)')
sunset_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_2 GOLD,M15: close #(\d+).*?at price ([\d\.]+)')
sl_hit_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+) \(([\d\.]+) / ([\d\.]+)\)')
tp_hit_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+) \(([\d\.]+) / ([\d\.]+)\)')
close_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: close #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+)')

for line in v632_lines:
    m_open = open_order_pattern.search(line)
    if m_open:
        time_str, ticket, side, lots, price, sl, tp = m_open.groups()
        ticket = int(ticket)
        trades[ticket] = {
            'ticket': ticket,
            'open_time': time_str,
            'side': side.upper(),
            'lots': float(lots),
            'open_price': float(price),
            'sl': float(sl),
            'tp': float(tp),
            'engine': 'UNKNOWN',
            'events': []
        }
        continue
    
    m_eng = engine_pattern.search(line)
    if m_eng:
        eng, t = m_eng.groups()
        t = int(t)
        if t in trades:
            trades[t]['engine'] = eng
        continue

    # Sunset close
    m_sunset = sunset_pattern.search(line)
    if m_sunset:
        time_str, ticket, price = m_sunset.groups()
        ticket = int(ticket)
        if ticket in trades:
            trades[ticket]['close_time'] = time_str
            trades[ticket]['close_price'] = float(price)
            trades[ticket]['close_reason'] = 'SUNSET_EXIT'
        continue

    # SL hit
    m_sl = sl_hit_pattern.search(line)
    if m_sl:
        time_str, ticket, sl_price, bid, ask = m_sl.groups()
        ticket = int(ticket)
        if ticket in trades:
            trades[ticket]['close_time'] = time_str
            side = trades[ticket]['side']
            close_p = float(bid) if side == 'BUY' else float(ask)
            trades[ticket]['close_price'] = close_p
            trades[ticket]['close_reason'] = 'STOP_LOSS'
        continue

    # TP hit
    m_tp = tp_hit_pattern.search(line)
    if m_tp:
        time_str, ticket, tp_price, bid, ask = m_tp.groups()
        ticket = int(ticket)
        if ticket in trades:
            trades[ticket]['close_time'] = time_str
            side = trades[ticket]['side']
            close_p = float(bid) if side == 'BUY' else float(ask)
            trades[ticket]['close_price'] = close_p
            trades[ticket]['close_reason'] = 'TAKE_PROFIT'
        continue

    # Generic close
    m_cl = close_pattern.search(line)
    if m_cl:
        time_str, ticket, side, lots, price = m_cl.groups()
        ticket = int(ticket)
        if ticket in trades and 'close_time' not in trades[ticket]:
            trades[ticket]['close_time'] = time_str
            trades[ticket]['close_price'] = float(price)
            trades[ticket]['close_reason'] = 'CLOSED'
        continue

engine_stats = {
    'SNIPER RUNNER': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gross_profit': 0.0, 'gross_loss': 0.0},
    'NEW YORK TREND-RIDER': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gross_profit': 0.0, 'gross_loss': 0.0},
    'ASIAN SQUEEZE': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gross_profit': 0.0, 'gross_loss': 0.0},
    'UNKNOWN': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gross_profit': 0.0, 'gross_loss': 0.0}
}

monthly_stats = {}
weekly_stats = {}

balance = 1000.0
total_pnl = 0.0
max_balance = balance
max_dd_usd = 0.0
max_dd_pct = 0.0

trade_list = sorted(trades.values(), key=lambda x: x['open_time'])

for t in trade_list:
    side = t['side']
    open_p = t['open_price']
    close_p = t.get('close_price', open_p)
    lots = t['lots']
    
    if side == 'BUY':
        diff = close_p - open_p
    else:
        diff = open_p - close_p
        
    pnl = diff * lots * 100.0
    t['pnl'] = pnl
    t['diff_usd'] = diff
    
    total_pnl += pnl
    balance += pnl
    if balance > max_balance:
        max_balance = balance
    dd_usd = max_balance - balance
    dd_pct = (dd_usd / max_balance) * 100.0 if max_balance > 0 else 0.0
    if dd_usd > max_dd_usd:
        max_dd_usd = dd_usd
    if dd_pct > max_dd_pct:
        max_dd_pct = dd_pct
        
    eng = t['engine']
    if eng not in engine_stats:
        eng = 'UNKNOWN'
    st = engine_stats[eng]
    st['count'] += 1
    st['pnl'] += pnl
    if pnl > 0:
        st['wins'] += 1
        st['gross_profit'] += pnl
    else:
        st['losses'] += 1
        st['gross_loss'] += abs(pnl)
        
    m_key = t['open_time'][:7]
    if m_key not in monthly_stats:
        monthly_stats[m_key] = {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'trades': []}
    monthly_stats[m_key]['count'] += 1
    monthly_stats[m_key]['pnl'] += pnl
    if pnl > 0: monthly_stats[m_key]['wins'] += 1
    else: monthly_stats[m_key]['losses'] += 1
    monthly_stats[m_key]['trades'].append(t)
    
    dt = datetime.datetime.strptime(t['open_time'], '%Y.%m.%d %H:%M:%S')
    w_key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
    if w_key not in weekly_stats:
        weekly_stats[w_key] = {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
    weekly_stats[w_key]['count'] += 1
    weekly_stats[w_key]['pnl'] += pnl
    if pnl > 0: weekly_stats[w_key]['wins'] += 1
    else: weekly_stats[w_key]['losses'] += 1

print("\n" + "="*70)
print(f"OVERALL RESULTS v6.3.2 (2025.06 - 2026.10):")
print(f"Total Trades: {len(trade_list)}")
print(f"Net Profit: ${total_pnl:,.2f}")
print(f"Final Balance (from $1,000): ${balance:,.2f}")
print(f"Max Drawdown: ${max_dd_usd:,.2f} ({max_dd_pct:.2f}%)")
print("="*70)

print("\nPER ENGINE PERFORMANCE:")
for eng, st in engine_stats.items():
    if st['count'] == 0: continue
    wr = (st['wins'] / st['count']) * 100.0
    pf = (st['gross_profit'] / st['gross_loss']) if st['gross_loss'] > 0 else 999.0
    print(f"Engine: {eng:22s} | Trades: {st['count']:3d} | Win: {st['wins']:2d} | Loss: {st['losses']:2d} | WinRate: {wr:5.1f}% | Net PnL: ${st['pnl']:+9.2f} | PF: {pf:.2f}")

print("\nMONTHLY BREAKDOWN:")
for m_key in sorted(monthly_stats.keys()):
    mst = monthly_stats[m_key]
    wr = (mst['wins'] / mst['count']) * 100.0 if mst['count'] > 0 else 0.0
    print(f"Month: {m_key} | Trades: {mst['count']:2d} | Win: {mst['wins']:2d} | Loss: {mst['losses']:2d} | WR: {wr:5.1f}% | Net PnL: ${mst['pnl']:+8.2f}")

print("\nWEEKLY BREAKDOWN:")
for w_key in sorted(weekly_stats.keys()):
    wst = weekly_stats[w_key]
    wr = (wst['wins'] / wst['count']) * 100.0 if wst['count'] > 0 else 0.0
    print(f"Week: {w_key} | Trades: {wst['count']:2d} | Win: {wst['wins']:2d} | Loss: {wst['losses']:2d} | WR: {wr:5.1f}% | Net PnL: ${wst['pnl']:+8.2f}")
