import struct
from datetime import datetime

hst_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst'
with open(hst_file, 'rb') as f:
    f.read(148)
    bars = []
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

start_dt = datetime(2025, 10, 1)
end_dt = datetime(2026, 10, 31)

daily_highs = {}
daily_lows = {}
for b in bars:
    d = b['time'].date()
    if d not in daily_highs or b['high'] > daily_highs[d]: daily_highs[d] = b['high']
    if d not in daily_lows or b['low'] < daily_lows[d]: daily_lows[d] = b['low']
dates_sorted = sorted(list(daily_highs.keys()))

results = []
for rr in [2.5, 3.0, 3.5, 4.0]:
    for be_mult in [1.5, 2.0]:
        for wick_ratio in [0.35, 0.40]:
            trades = []
            open_pos = None
            for i in range(100, len(bars)):
                b = bars[i]
                if b['time'] < start_dt or b['time'] > end_dt: continue
                if open_pos is not None:
                    pos = open_pos
                    if pos['type'] == 'BUY':
                        if not pos['is_be'] and b['high'] >= pos['open'] + (pos['open'] - pos['init_sl']) * be_mult:
                            pos['sl'] = pos['open'] + 0.30
                            pos['is_be'] = True
                        if b['low'] <= pos['sl']:
                            pnl = (pos['sl'] - pos['open']) * pos['lots'] * 100.0
                            trades.append({'time': b['time'], 'type': 'BUY', 'pnl': pnl, 'reason': 'BE' if pos['is_be'] else 'SL'})
                            open_pos = None
                        elif b['high'] >= pos['tp']:
                            pnl = (pos['tp'] - pos['open']) * pos['lots'] * 100.0
                            trades.append({'time': b['time'], 'type': 'BUY', 'pnl': pnl, 'reason': 'TP'})
                            open_pos = None
                    elif pos['type'] == 'SELL':
                        if not pos['is_be'] and b['low'] <= pos['open'] - (pos['init_sl'] - pos['open']) * be_mult:
                            pos['sl'] = pos['open'] - 0.30
                            pos['is_be'] = True
                        if b['high'] >= pos['sl']:
                            pnl = (pos['open'] - pos['sl']) * pos['lots'] * 100.0
                            trades.append({'time': b['time'], 'type': 'SELL', 'pnl': pnl, 'reason': 'BE' if pos['is_be'] else 'SL'})
                            open_pos = None
                        elif b['low'] <= pos['tp']:
                            pnl = (pos['open'] - pos['tp']) * pos['lots'] * 100.0
                            trades.append({'time': b['time'], 'type': 'SELL', 'pnl': pnl, 'reason': 'TP'})
                            open_pos = None
                if open_pos is not None: continue
                t = b['time']
                m = t.hour * 60 + t.minute
                if not (8*60 <= m <= 20*60 + 30): continue
                cur_date = t.date()
                idx_d = dates_sorted.index(cur_date) if cur_date in dates_sorted else -1
                if idx_d <= 0: continue
                prev_date = dates_sorted[idx_d - 1]
                pdh = daily_highs.get(prev_date, 0.0)
                pdl = daily_lows.get(prev_date, 999999.0)
                asian_bars = [x for x in bars[i-40:i] if x['time'].date() == cur_date and 0 <= x['time'].hour < 7]
                if not asian_bars: continue
                asian_high = max(x['high'] for x in asian_bars)
                asian_low = min(x['low'] for x in asian_bars)
                c1 = bars[i-1]
                c1_rng = c1['high'] - c1['low']
                if c1_rng <= 0.80: continue
                c1_upper_wick = c1['high'] - max(c1['open'], c1['close'])
                c1_lower_wick = min(c1['open'], c1['close']) - c1['low']
                
                # Sell setup
                at_res = (c1['high'] >= asian_high or c1['high'] >= pdh)
                if at_res and (c1_upper_wick / c1_rng) >= wick_ratio and c1['close'] < c1['open']:
                    sl = c1['high'] + 1.00
                    entry = b['open']
                    sl_dist = sl - entry
                    if 1.50 <= sl_dist <= 6.00:
                        tp = entry - (sl_dist * rr)
                        open_pos = {'type': 'SELL', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp, 'lots': 0.10, 'is_be': False}
                        continue
                # Buy setup
                at_sup = (c1['low'] <= asian_low or c1['low'] <= pdl)
                if at_sup and (c1_lower_wick / c1_rng) >= wick_ratio and c1['close'] > c1['open']:
                    sl = c1['low'] - 1.00
                    entry = b['open']
                    sl_dist = entry - sl
                    if 1.50 <= sl_dist <= 6.00:
                        tp = entry + (sl_dist * rr)
                        open_pos = {'type': 'BUY', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp, 'lots': 0.10, 'is_be': False}
                        continue
            gross_p = sum(x['pnl'] for x in trades if x['pnl'] > 0)
            gross_l = abs(sum(x['pnl'] for x in trades if x['pnl'] < 0))
            pf = gross_p / (gross_l if gross_l > 0 else 1)
            net = gross_p - gross_l
            results.append((pf, net, len(trades), rr, be_mult, wick_ratio))

results.sort(reverse=True)
for r in results[:10]:
    print(f"PF: {r[0]:.2f} | Net: ${r[1]:.2f} | Trades: {r[2]} | RR: {r[3]} | BE: {r[4]} | Wick: {r[5]}")
