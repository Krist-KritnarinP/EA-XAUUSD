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

# 2. Load latest run from 20261102.log
log_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261102.log'
with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

latest_text = text[207435:]
lines = latest_text.splitlines()

# Track all orders
orders = {}
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
re_tag = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*\[(LONDON SNIPER|SWEEP FADE|NY POI)[^\]]*\] Ticket #(\d+)')
re_mod = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*modify #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*close #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+) at price ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)\s+\(([\d\.]+)\s+/\s+([\d\.]+)\)')
re_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)\s+\(([\d\.]+)\s+/\s+([\d\.]+)\)')

# MT4 generates closed trades
# Each close event produces a completed trade in the report
closed_trades = []

# When partial close happens, order #X is closed with partial lot, and remainder becomes #X+1
for l in lines:
    mo = re_open.search(l)
    if mo:
        t_str, tid, cmd, lots, op, sl, tp = mo.groups()
        tid = int(tid)
        orders[tid] = {
            'ticket': tid,
            'open_time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'),
            'type': cmd.upper(),
            'lots': float(lots),
            'open_price': float(op),
            'init_sl': float(sl),
            'init_tp': float(tp),
            'cur_sl': float(sl),
            'cur_tp': float(tp),
            'engine': 'POI NY Sniper' # default
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
            # child ticket from partial close
            # inherits from previous ticket
            parent_id = tid - 1
            if parent_id in orders:
                parent = orders[parent_id]
                orders[tid] = {
                    'ticket': tid,
                    'open_time': parent['open_time'],
                    'type': parent['type'],
                    'lots': float(lots),
                    'open_price': parent['open_price'],
                    'init_sl': parent['init_sl'],
                    'init_tp': parent['init_tp'],
                    'cur_sl': float(sl),
                    'cur_tp': float(tp),
                    'engine': parent['engine']
                }
        continue

    mc = re_close.search(l)
    if mc:
        t_str, tid, cmd, lots, op, sl, tp, cp = mc.groups()
        tid = int(tid)
        c_time = datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S')
        cp = float(cp)
        c_lots = float(lots)
        
        if tid in orders:
            ord_info = orders[tid]
            is_buy = (ord_info['type'] == 'BUY')
            pnl = (cp - ord_info['open_price']) * c_lots * 100.0 if is_buy else (ord_info['open_price'] - cp) * c_lots * 100.0
            
            # If partial close
            if c_lots < ord_info['lots']:
                ord_info['lots'] -= c_lots
                reason = 'PARTIAL_TP_1.5R'
            elif 'sunset' in l.lower() or c_time.hour == 13:
                reason = 'SUNSET_EXIT'
            elif 'structural' in l.lower():
                reason = 'STRUCTURAL_BAILOUT'
            else:
                reason = 'MANUAL_CLOSE'
                
            closed_trades.append({
                'ticket': tid,
                'open_time': ord_info['open_time'],
                'close_time': c_time,
                'type': ord_info['type'],
                'lots': c_lots,
                'open_price': ord_info['open_price'],
                'close_price': cp,
                'init_sl': ord_info['init_sl'],
                'init_tp': ord_info['init_tp'],
                'cur_sl': ord_info['cur_sl'],
                'engine': ord_info['engine'],
                'reason': reason,
                'pnl': pnl
            })
        continue

    ms = re_sl.search(l)
    if ms:
        t_str, tid, sl_p, bid_p, ask_p = ms.groups()
        tid = int(tid)
        c_time = datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S')
        sl_p = float(sl_p)
        bid_p = float(bid_p)
        ask_p = float(ask_p)
        
        if tid not in orders and (tid - 1) in orders:
            # Child ticket
            parent = orders[tid - 1]
            orders[tid] = {
                'ticket': tid,
                'open_time': parent['open_time'],
                'type': parent['type'],
                'lots': parent['lots'],
                'open_price': parent['open_price'],
                'init_sl': parent['init_sl'],
                'init_tp': parent['init_tp'],
                'cur_sl': parent['cur_sl'],
                'cur_tp': parent['cur_tp'],
                'engine': parent['engine']
            }
            
        if tid in orders:
            ord_info = orders[tid]
            is_buy = (ord_info['type'] == 'BUY')
            exec_p = bid_p if is_buy else ask_p # Buy closes at Bid, Sell closes at Ask
            pnl = (exec_p - ord_info['open_price']) * ord_info['lots'] * 100.0 if is_buy else (ord_info['open_price'] - exec_p) * ord_info['lots'] * 100.0
            
            pnl_pts = (exec_p - ord_info['open_price']) if is_buy else (ord_info['open_price'] - exec_p)
            reason = 'BE_LOCK' if pnl_pts >= -0.30 else 'STOP_LOSS'
            
            closed_trades.append({
                'ticket': tid,
                'open_time': ord_info['open_time'],
                'close_time': c_time,
                'type': ord_info['type'],
                'lots': ord_info['lots'],
                'open_price': ord_info['open_price'],
                'close_price': exec_p,
                'init_sl': ord_info['init_sl'],
                'init_tp': ord_info['init_tp'],
                'cur_sl': ord_info['cur_sl'],
                'engine': ord_info['engine'],
                'reason': reason,
                'pnl': pnl
            })
        continue

    mtp = re_tp.search(l)
    if mtp:
        t_str, tid, tp_p, bid_p, ask_p = mtp.groups()
        tid = int(tid)
        c_time = datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S')
        tp_p = float(tp_p)
        bid_p = float(bid_p)
        ask_p = float(ask_p)
        
        if tid not in orders and (tid - 1) in orders:
            parent = orders[tid - 1]
            orders[tid] = {
                'ticket': tid,
                'open_time': parent['open_time'],
                'type': parent['type'],
                'lots': parent['lots'],
                'open_price': parent['open_price'],
                'init_sl': parent['init_sl'],
                'init_tp': parent['init_tp'],
                'cur_sl': parent['cur_sl'],
                'cur_tp': parent['cur_tp'],
                'engine': parent['engine']
            }
            
        if tid in orders:
            ord_info = orders[tid]
            is_buy = (ord_info['type'] == 'BUY')
            exec_p = bid_p if is_buy else ask_p
            pnl = (exec_p - ord_info['open_price']) * ord_info['lots'] * 100.0 if is_buy else (ord_info['open_price'] - exec_p) * ord_info['lots'] * 100.0
            
            closed_trades.append({
                'ticket': tid,
                'open_time': ord_info['open_time'],
                'close_time': c_time,
                'type': ord_info['type'],
                'lots': ord_info['lots'],
                'open_price': ord_info['open_price'],
                'close_price': exec_p,
                'init_sl': ord_info['init_sl'],
                'init_tp': ord_info['init_tp'],
                'cur_sl': ord_info['cur_sl'],
                'engine': ord_info['engine'],
                'reason': 'TAKE_PROFIT',
                'pnl': pnl
            })
        continue

print(f"Total closed trades parsed: {len(closed_trades)}")
total_pnl = sum(t['pnl'] for t in closed_trades)
wins = [t for t in closed_trades if t['pnl'] > 0]
losses = [t for t in closed_trades if t['pnl'] <= 0]
gross_profit = sum(t['pnl'] for t in wins)
gross_loss = abs(sum(t['pnl'] for t in losses))
pf = gross_profit / gross_loss if gross_loss > 0 else 999.0
print(f"Gross Profit: ${gross_profit:,.2f} | Gross Loss: -${gross_loss:,.2f}")
print(f"Total Net Profit: ${total_pnl:,.2f} | Profit Factor: {pf:.2f}")
print(f"Wins: {len(wins)} ({len(wins)/len(closed_trades)*100:.1f}%) | Losses: {len(losses)} ({len(losses)/len(closed_trades)*100:.1f}%)")
