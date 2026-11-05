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

# POI Simulation:
# POIs:
# 1. Asian High & Low (00:00 - 07:00 Server Time)
# 2. Previous Day High & Low (PDH & PDL)
# Trigger:
# When price touches or breaches POI, candle prints >= 35% rejection wick
# SL = Wick extreme + $1.00 USD
# TP = 3.0x SL distance (1:3 RR) or 3.5x
# BE = Move to BE at 1.5x RR

trades = []
open_pos = None

# Pre-calculate daily High & Low
daily_highs = {}
daily_lows = {}
for b in bars:
    d = b['time'].date()
    if d not in daily_highs or b['high'] > daily_highs[d]: daily_highs[d] = b['high']
    if d not in daily_lows or b['low'] < daily_lows[d]: daily_lows[d] = b['low']

dates_sorted = sorted(list(daily_highs.keys()))

for i in range(100, len(bars)):
    b = bars[i]
    if b['time'] < start_dt or b['time'] > end_dt: continue

    # Manage open position
    if open_pos is not None:
        pos = open_pos
        if pos['type'] == 'BUY':
            # BE at 1.5 RR
            if not pos['is_be'] and b['high'] >= pos['open'] + (pos['open'] - pos['init_sl']) * 1.5:
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
            if not pos['is_be'] and b['low'] <= pos['open'] - (pos['init_sl'] - pos['open']) * 1.5:
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

    # Full Day Trading Window: 08:00 to 20:30 Server Time
    t = b['time']
    m = t.hour * 60 + t.minute
    if not (8*60 <= m <= 20*60 + 30): continue

    # Find PDH & PDL
    cur_date = t.date()
    idx_d = dates_sorted.index(cur_date) if cur_date in dates_sorted else -1
    if idx_d <= 0: continue
    prev_date = dates_sorted[idx_d - 1]
    pdh = daily_highs.get(prev_date, 0.0)
    pdl = daily_lows.get(prev_date, 999999.0)

    # Asian Range (00:00 - 07:00)
    asian_bars = [x for x in bars[i-40:i] if x['time'].date() == cur_date and 0 <= x['time'].hour < 7]
    if not asian_bars: continue
    asian_high = max(x['high'] for x in asian_bars)
    asian_low = min(x['low'] for x in asian_bars)

    # Check previous bar (c1 = bars[i-1]) for POI Rejection
    c1 = bars[i-1]
    c1_rng = c1['high'] - c1['low']
    if c1_rng <= 0.80: continue # ignore micro doji

    c1_upper_wick = c1['high'] - max(c1['open'], c1['close'])
    c1_lower_wick = min(c1['open'], c1['close']) - c1['low']

    # SELL SETUP at Resistance POI (Asian High or PDH):
    # Price pierced or touched POI and formed strong Upper Wick (>= 35% of candle range)
    at_resistance = (c1['high'] >= asian_high or c1['high'] >= pdh)
    if at_resistance and (c1_upper_wick / c1_rng) >= 0.35 and c1['close'] < c1['open']:
        # Tight Sniper SL:
        sl = c1['high'] + 1.00 # $1.00 buffer above rejection wick
        entry = b['open']
        sl_dist = sl - entry
        if 1.50 <= sl_dist <= 6.00: # Tight Risk!
            tp = entry - (sl_dist * 3.0) # 1:3 RR!
            open_pos = {
                'type': 'SELL',
                'open': entry,
                'sl': sl,
                'init_sl': sl,
                'tp': tp,
                'lots': 0.10,
                'is_be': False
            }
            continue

    # BUY SETUP at Support POI (Asian Low or PDL):
    # Price pierced or touched POI and formed strong Lower Wick (>= 35% of candle range)
    at_support = (c1['low'] <= asian_low or c1['low'] <= pdl)
    if at_support and (c1_lower_wick / c1_rng) >= 0.35 and c1['close'] > c1['open']:
        sl = c1['low'] - 1.00 # $1.00 buffer below rejection wick
        entry = b['open']
        sl_dist = entry - sl
        if 1.50 <= sl_dist <= 6.00: # Tight Risk!
            tp = entry + (sl_dist * 3.0) # 1:3 RR!
            open_pos = {
                'type': 'BUY',
                'open': entry,
                'sl': sl,
                'init_sl': sl,
                'tp': tp,
                'lots': 0.10,
                'is_be': False
            }
            continue

wins = [t for t in trades if t['pnl'] > 0]
losses = [t for t in trades if t['pnl'] < 0]
tp_hits = [t for t in trades if t['reason'] == 'TP']
be_hits = [t for t in trades if t['reason'] == 'BE']
total_pnl = sum(t['pnl'] for t in trades)
gross_p = sum(t['pnl'] for t in wins)
gross_l = abs(sum(t['pnl'] for t in losses))
pf = gross_p / gross_l if gross_l > 0 else 999.0
wr = (len(wins) / len(trades) * 100) if trades else 0

print(f"Total Trades: {len(trades)}")
print(f"Win Rate: {wr:.1f}% ({len(wins)}/{len(trades)})")
print(f"TP Hits (1:3 RR): {len(tp_hits)} | Breakeven Hits: {len(be_hits)} | Losses: {len(losses)}")
print(f"Total Net Profit: ${total_pnl:.2f} (Gross Profit: ${gross_p:.2f}, Gross Loss: -${gross_l:.2f})")
print(f"Profit Factor: {pf:.2f}")
