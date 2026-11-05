import struct
from datetime import datetime

hst_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst'
with open(hst_file, 'rb') as f:
    header = f.read(148)
    bars = []
    while True:
        data = f.read(60)
        if len(data) < 60: break
        unp = struct.unpack('<QddddQiq', data)
        dt = datetime.fromtimestamp(unp[0])
        bars.append({
            'time': dt,
            'open': unp[1],
            'high': unp[2], # correct: high is 2
            'low': unp[3],  # correct: low is 3
            'close': unp[4]
        })

start_dt = datetime(2025, 10, 1)
end_dt = datetime(2026, 10, 31)

# Pre-calculate 50 EMA on M15
closes = [b['close'] for b in bars]
ema50 = [0.0] * len(bars)
k = 2.0 / (50 + 1)
ema50[49] = sum(closes[:50]) / 50.0
for i in range(50, len(bars)):
    ema50[i] = closes[i] * k + ema50[i-1] * (1.0 - k)

trades = []
open_pos = None
active_fvg = None

for i in range(100, len(bars)):
    b = bars[i]
    if b['time'] < start_dt or b['time'] > end_dt:
        continue
        
    # Manage open position
    if open_pos is not None:
        pos = open_pos
        if pos['type'] == 'BUY':
            # BE at 1:1.2 RR
            if not pos['is_be'] and b['high'] >= pos['open'] + (pos['open'] - pos['init_sl']) * 1.2:
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
            if not pos['is_be'] and b['low'] <= pos['open'] - (pos['init_sl'] - pos['open']) * 1.2:
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

    # Check active FVG fill
    if open_pos is None and active_fvg is not None:
        f = active_fvg
        f['bars'] += 1
        if f['bars'] > 8: # expire after 2 hours
            active_fvg = None
        else:
            if f['type'] == 'BUY':
                if b['low'] < f['sl']:
                    active_fvg = None
                elif b['low'] <= f['entry']:
                    open_pos = {'type': 'BUY', 'open': f['entry'], 'sl': f['sl'], 'init_sl': f['sl'], 'tp': f['tp'], 'lots': 0.10, 'is_be': False}
                    active_fvg = None
                    continue
            elif f['type'] == 'SELL':
                if b['high'] > f['sl']:
                    active_fvg = None
                elif b['high'] >= f['entry']:
                    open_pos = {'type': 'SELL', 'open': f['entry'], 'sl': f['sl'], 'init_sl': f['sl'], 'tp': f['tp'], 'lots': 0.10, 'is_be': False}
                    active_fvg = None
                    continue

    if open_pos is not None:
        continue

    # Window check
    t = b['time']
    m = t.hour * 60 + t.minute
    in_london = (8*60 <= m <= 11*60 + 30)
    in_ny = (14*60 + 30 <= m <= 17*60 + 30)
    if not (in_london or in_ny):
        continue

    # ICT 2022 Model: Check Displacement + FVG
    c1 = bars[i-3]
    c2 = bars[i-2] # displacement candle
    c3 = bars[i-1]

    # Bullish Setup:
    # 1. c2 is strong green candle
    # 2. c3['low'] > c1['high'] (FVG exists)
    # 3. c2 closed above recent swing high of last 5 bars (MSS)
    c2_body = c2['close'] - c2['open']
    c2_rng = c2['high'] - c2['low']
    if c2_body > 1.80 and c2_rng > 0 and (c2_body / c2_rng) >= 0.50:
        if c3['low'] > c1['high']: # FVG exists
            swing_high = max(bars[i-j]['high'] for j in range(4, 9))
            if c2['close'] > swing_high and c2['close'] > ema50[i-2]: # MSS + Trend
                fvg_gap = c3['low'] - c1['high']
                if fvg_gap >= 0.60:
                    entry = c3['low'] # top of FVG
                    sl = c2['low'] - 1.00 # below displacement candle
                    sl_dist = entry - sl
                    if 2.0 <= sl_dist <= 10.0:
                        active_fvg = {
                            'type': 'BUY',
                            'entry': entry,
                            'sl': sl,
                            'tp': entry + (sl_dist * 2.0), # 1:2 RR
                            'bars': 0
                        }

    # Bearish Setup:
    c2_bear_body = c2['open'] - c2['close']
    if c2_bear_body > 1.80 and c2_rng > 0 and (c2_bear_body / c2_rng) >= 0.50:
        if c3['high'] < c1['low']: # Bearish FVG exists
            swing_low = min(bars[i-j]['low'] for j in range(4, 9))
            if c2['close'] < swing_low and c2['close'] < ema50[i-2]: # MSS + Trend
                fvg_gap = c1['low'] - c3['high']
                if fvg_gap >= 0.60:
                    entry = c3['high'] # bottom of FVG
                    sl = c2['high'] + 1.00 # above displacement candle
                    sl_dist = sl - entry
                    if 2.0 <= sl_dist <= 10.0:
                        active_fvg = {
                            'type': 'SELL',
                            'entry': entry,
                            'sl': sl,
                            'tp': entry - (sl_dist * 2.0),
                            'bars': 0
                        }

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
print(f"TP Hits (1:2 RR): {len(tp_hits)} | Breakeven Hits: {len(be_hits)} | Losses: {len(losses)}")
print(f"Total Net Profit: ${total_pnl:.2f} (Gross Profit: ${gross_p:.2f}, Gross Loss: -${gross_l:.2f})")
print(f"Profit Factor: {pf:.2f}")
