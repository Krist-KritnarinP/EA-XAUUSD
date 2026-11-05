import struct, json
from datetime import datetime

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

start_dt = datetime(2025, 10, 1)
end_dt = datetime(2026, 10, 31)

# Daily bars
daily = {}
for b in bars:
    d = b['time'].date()
    if d not in daily:
        daily[d] = {'open': b['open'], 'high': b['high'], 'low': b['low'], 'close': b['close']}
    else:
        if b['high'] > daily[d]['high']: daily[d]['high'] = b['high']
        if b['low'] < daily[d]['low']: daily[d]['low'] = b['low']
        daily[d]['close'] = b['close']

dates_sorted = sorted(list(daily.keys()))

# Daily ATR 14
daily_atr = {}
for idx in range(14, len(dates_sorted)):
    cur_d = dates_sorted[idx]
    tr_sum = 0.0
    for j in range(idx-13, idx+1):
        d_j = dates_sorted[j]
        d_prev = dates_sorted[j-1]
        tr = max(daily[d_j]['high'] - daily[d_j]['low'], abs(daily[d_j]['high'] - daily[d_prev]['close']), abs(daily[d_j]['low'] - daily[d_prev]['close']))
        tr_sum += tr
    daily_atr[cur_d] = tr_sum / 14.0

# Calculate EMA 50 on H4 equivalent (M15 EMA 800)
closes = [b['close'] for b in bars]
ema800 = [closes[0]] * len(closes)
k = 2.0 / (800 + 1)
for idx in range(1, len(closes)):
    ema800[idx] = closes[idx] * k + ema800[idx-1] * (1 - k)

# Test macro guard
print("Testing Macro Guard for V3...")
oct26_buys_blocked = 0
for d in dates_sorted:
    if d.year == 2026 and d.month == 10:
        prev_idx = dates_sorted.index(d) - 1
        prev_d = dates_sorted[prev_idx]
        prev_bar = daily[prev_d]
        prev_rng = prev_bar['high'] - prev_bar['low']
        atr = daily_atr.get(d, 50.0)
        is_dump = (prev_bar['close'] < prev_bar['open']) and (prev_rng >= atr * 1.0)
        if is_dump:
            print(f"Date: {d} | Prev D1 Dump: {prev_d} (Range: ${prev_rng:.2f} >= ATR ${atr:.2f}) -> Macro BUY BLOCKED!")
