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

# Pre-calculate Asian session ranges
asian_ranges = {}
for b in bars:
    d = b['time'].date()
    if 0 <= b['time'].hour < 7:
        if d not in asian_ranges:
            asian_ranges[d] = {'high': b['high'], 'low': b['low']}
        else:
            if b['high'] > asian_ranges[d]['high']: asian_ranges[d]['high'] = b['high']
            if b['low'] < asian_ranges[d]['low']: asian_ranges[d]['low'] = b['low']

# Calculate EMA 200 on M15 (~ EMA 50 on H1)
closes = [b['close'] for b in bars]
ema200 = [closes[0]] * len(closes)
k = 2.0 / (200 + 1)
for idx in range(1, len(closes)):
    ema200[idx] = closes[idx] * k + ema200[idx-1] * (1 - k)

# Test with EMA filter vs without EMA filter
for use_ema in [False, True]:
    for max_sl in [4.50, 5.00, 6.00]:
        for rr in [3.0, 3.5, 4.0]:
            trades = []
            open_pos = None
            for i in range(250, len(bars)):
                b = bars[i]
                if b['time'] < start_dt or b['time'] > end_dt: continue
                if open_pos is not None:
                    pos = open_pos
                    if pos['type'] == 'BUY':
                        if not pos['is_be'] and b['high'] >= pos['open'] + (pos['open'] - pos['init_sl']) * 2.0:
                            pos['sl'] = pos['open'] + 0.30
                            pos['is_be'] = True
                        if b['low'] <= pos['sl']:
                            pnl = (pos['sl'] - pos['open']) * pos['lots'] * 100.0
                            trades.append({'pnl': pnl, 'win': pnl > 0})
                            open_pos = None
                        elif b['high'] >= pos['tp']:
                            pnl = (pos['tp'] - pos['open']) * pos['lots'] * 100.0
                            trades.append({'pnl': pnl, 'win': True})
                            open_pos = None
                    elif pos['type'] == 'SELL':
                        if not pos['is_be'] and b['low'] <= pos['open'] - (pos['init_sl'] - pos['open']) * 2.0:
                            pos['sl'] = pos['open'] - 0.30
                            pos['is_be'] = True
                        if b['high'] >= pos['sl']:
                            pnl = (pos['open'] - pos['sl']) * pos['lots'] * 100.0
                            trades.append({'pnl': pnl, 'win': pnl > 0})
                            open_pos = None
                        elif b['low'] <= pos['tp']:
                            pnl = (pos['open'] - pos['tp']) * pos['lots'] * 100.0
                            trades.append({'pnl': pnl, 'win': True})
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
                if cur_date not in asian_ranges: continue
                asian_high = asian_ranges[cur_date]['high']
                asian_low = asian_ranges[cur_date]['low']
                
                c1 = bars[i-1]
                c1_rng = c1['high'] - c1['low']
                if c1_rng <= 0.80: continue
                c1_upper_wick = c1['high'] - max(c1['open'], c1['close'])
                c1_lower_wick = min(c1['open'], c1['close']) - c1['low']
                
                # Sell setup
                at_res = (c1['high'] >= asian_high or c1['high'] >= pdh)
                ema_cond_sell = (not use_ema) or (c1['close'] < ema200[i-1] or c1['high'] > ema200[i-1]) # or overextended above EMA
                if at_res and (c1_upper_wick / c1_rng) >= 0.35 and c1['close'] < c1['open'] and ema_cond_sell:
                    sl = c1['high'] + 1.00
                    entry = b['open']
                    sl_dist = sl - entry
                    if 1.50 <= sl_dist <= max_sl:
                        tp = entry - (sl_dist * rr)
                        open_pos = {'type': 'SELL', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp, 'lots': 0.10, 'is_be': False}
                        continue
                        
                # Buy setup
                at_sup = (c1['low'] <= asian_low or c1['low'] <= pdl)
                ema_cond_buy = (not use_ema) or (c1['close'] > ema200[i-1] or c1['low'] < ema200[i-1])
                if at_sup and (c1_lower_wick / c1_rng) >= 0.35 and c1['close'] > c1['open'] and ema_cond_buy:
                    sl = c1['low'] - 1.00
                    entry = b['open']
                    sl_dist = entry - sl
                    if 1.50 <= sl_dist <= max_sl:
                        tp = entry + (sl_dist * rr)
                        open_pos = {'type': 'BUY', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp, 'lots': 0.10, 'is_be': False}
                        continue

            gross_p = sum(x['pnl'] for x in trades if x['pnl'] > 0)
            gross_l = abs(sum(x['pnl'] for x in trades if x['pnl'] < 0))
            pf = gross_p / (gross_l if gross_l > 0 else 1)
            net = gross_p - gross_l
            win_rate = (sum(1 for x in trades if x['win']) / len(trades) * 100) if trades else 0
            print(f"EMA: {use_ema} | MaxSL: {max_sl} | RR: {rr} | Trades: {len(trades)} | WinRate: {win_rate:.1f}% | Net: ${net:.2f} | PF: {pf:.2f}")
