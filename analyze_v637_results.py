import re
import os

log_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261026.log"

text = ""
for enc in ['utf-8', 'latin1', 'cp1252', 'utf-16-le']:
    try:
        with open(log_path, 'r', encoding=enc) as f:
            text = f.read()
            if 'GoldSniper_Tester_v6_3_7_beta' in text:
                print(f"Read {len(text)} chars with encoding {enc}")
                break
    except Exception as e:
        continue

start_idx = text.rfind("GoldSniper_Tester_v6_3_7_beta inputs:")
if start_idx != -1:
    pass_text = text[start_idx:]
    lines = pass_text.splitlines()
    
    orders = {}
    for line in lines:
        m_open = re.search(r'open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)', line)
        if m_open:
            t = int(m_open.group(1))
            orders[t] = {
                'side': m_open.group(2),
                'lot': float(m_open.group(3)),
                'open_price': float(m_open.group(4)),
                'sl': float(m_open.group(5)),
                'tp': float(m_open.group(6)),
                'fast_be': False,
                'close_type': 'open',
                'close_price': 0.0,
                'engine': 'Unknown'
            }
        
        m_eng = re.search(r'\[(NEW YORK.*?|SNIPER RUNNER.*?|ASIAN.*?|SWEEP FADE.*?)\] Ticket: #(\d+)', line)
        if m_eng:
            eng = m_eng.group(1)
            t = int(m_eng.group(2))
            if t in orders:
                orders[t]['engine'] = eng

        m_be = re.search(r'\[FAST BREAKEVEN.*?Ticket #(\d+)', line)
        if m_be:
            t = int(m_be.group(1))
            if t in orders:
                orders[t]['fast_be'] = True

        m_tp = re.search(r'take profit #(\d+) at ([\d\.]+)', line)
        if m_tp:
            t = int(m_tp.group(1))
            if t in orders:
                orders[t]['close_type'] = 'TP'
                orders[t]['close_price'] = float(m_tp.group(2))

        m_sl = re.search(r'stop loss #(\d+) at ([\d\.]+)', line)
        if m_sl:
            t = int(m_sl.group(1))
            if t in orders:
                orders[t]['close_type'] = 'SL'
                orders[t]['close_price'] = float(m_sl.group(2))

        m_close = re.search(r'close #(\d+) (buy|sell) .*? at price ([\d\.]+)', line)
        if m_close:
            t = int(m_close.group(1))
            if t in orders:
                orders[t]['close_type'] = 'Manual/Partial'
                orders[t]['close_price'] = float(m_close.group(3))

    print(f"\n--- Total Tracked Orders: {len(orders)} ---")
    
    tp_count = sum(1 for o in orders.values() if o['close_type'] == 'TP')
    sl_count = sum(1 for o in orders.values() if o['close_type'] == 'SL')
    be_sl_count = sum(1 for o in orders.values() if o['close_type'] == 'SL' and o['fast_be'])
    loss_sl_count = sum(1 for o in orders.values() if o['close_type'] == 'SL' and not o['fast_be'])
    
    print(f"TP Hits: {tp_count}")
    print(f"SL Hits: {sl_count} (Of which stopped out at Fast Breakeven: {be_sl_count}, True Loss SL: {loss_sl_count})")
    print(f"Fast BE Triggered Total: {sum(1 for o in orders.values() if o['fast_be'])}")
    
    # Calculate PnL for each order
    results_by_engine = {}
    for t, o in orders.items():
        if o['close_price'] > 0:
            if o['side'] == 'buy':
                pnl_pts = o['close_price'] - o['open_price']
            else:
                pnl_pts = o['open_price'] - o['close_price']
            
            pnl_usd = pnl_pts * o['lot'] * 100.0
            o['pnl_usd'] = pnl_usd
            
            eng = o['engine']
            if eng not in results_by_engine:
                results_by_engine[eng] = {'wins': 0, 'losses': 0, 'be_wins': 0, 'total_pnl': 0.0, 'trades': 0}
            
            results_by_engine[eng]['trades'] += 1
            results_by_engine[eng]['total_pnl'] += pnl_usd
            if pnl_usd > 1.0:
                results_by_engine[eng]['wins'] += 1
            elif pnl_usd > -1.0:
                results_by_engine[eng]['be_wins'] += 1
            else:
                results_by_engine[eng]['losses'] += 1

    print("\n--- Breakdown by Engine ---")
    for eng, res in results_by_engine.items():
        print(f"Engine: {eng}")
        print(f"  Trades: {res['trades']}, PnL: ${res['total_pnl']:.2f}")
        print(f"  Wins (> $1): {res['wins']}, BE Micro-wins ($0-$1): {res['be_wins']}, Real Losses: {res['losses']}")
