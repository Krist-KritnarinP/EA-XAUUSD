import struct, os, math
from datetime import datetime

hst_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46"

def load_bars(fn):
    path = os.path.join(hst_dir, fn)
    bars = []
    with open(path, 'rb') as f:
        f.read(148)
        while True:
            data = f.read(60)
            if len(data) < 60:
                break
            t, o, h, l, c, v, s, r = struct.unpack('<QddddQiq', data)
            bars.append({'time': datetime.utcfromtimestamp(t), 'open': o, 'high': h, 'low': l, 'close': c, 'vol': v})
    return bars

d1 = load_bars('GOLD1440.hst')
h4 = load_bars('GOLD240.hst')
h1 = load_bars('GOLD60.hst')
m15 = load_bars('GOLD15.hst')

print(f"D1 total: {len(d1)}, latest: {d1[-1]}")
print(f"H4 total: {len(h4)}, latest: {h4[-1]}")
print(f"H1 total: {len(h1)}, latest: {h1[-1]}")
print(f"M15 total: {len(m15)}, latest: {m15[-1]}")

# ATR(14) on D1
trs = []
for i in range(1, len(d1)):
    prev_c = d1[i-1]['close']
    h = d1[i]['high']
    l = d1[i]['low']
    tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
    trs.append(tr)

atr14_d1 = sum(trs[-14:]) / 14.0
adr20_d1 = sum([d['high'] - d['low'] for d in d1[-20:]]) / 20.0

print(f"\nD1 ATR(14): {atr14_d1:.2f} USD ({atr14_d1*100:.0f} pts)")
print(f"D1 ADR(20): {adr20_d1:.2f} USD ({adr20_d1*100:.0f} pts)")

# Recent 5 days stats
print("\nRecent 5 D1 candles:")
for b in d1[-5:]:
    change = b['close'] - b['open']
    rng = b['high'] - b['low']
    print(f"{b['time'].strftime('%Y-%m-%d')} | O:{b['open']:.2f} H:{b['high']:.2f} L:{b['low']:.2f} C:{b['close']:.2f} | Chg:{change:+.2f} Rng:{rng:.2f}")

# Weekly high/low (last week: 2026-10-26 to 2026-10-30)
last_week_bars = [b for b in d1 if b['time'] >= datetime(2026, 10, 26) and b['time'] <= datetime(2026, 10, 30)]
pw_open = last_week_bars[0]['open']
pw_high = max(b['high'] for b in last_week_bars)
pw_low = min(b['low'] for b in last_week_bars)
pw_close = last_week_bars[-1]['close']
print(f"\nLast Week (2026-10-26 to 10-30): Open: {pw_open:.2f}, High: {pw_high:.2f}, Low: {pw_low:.2f}, Close: {pw_close:.2f}, Range: {pw_high - pw_low:.2f}")

# Friday drop stats
fri_o = d1[-1]['open']
fri_h = d1[-1]['high']
fri_l = d1[-1]['low']
fri_c = d1[-1]['close']
print(f"Friday Range: {fri_h - fri_l:.2f} USD ({fri_h - fri_l:.2f} pts)")
print(f"Friday Drop %: {((fri_c - fri_o) / fri_o)*100:.2f}%")

# Fibonacci retracements of Friday's dump (from High 4026.15 to Low 3869.95)
swing_h = fri_h
swing_l = fri_l
diff = swing_h - swing_l
fibs = {
    '0.000 (Low)': swing_l,
    '0.236': swing_l + diff * 0.236,
    '0.382': swing_l + diff * 0.382,
    '0.500 (Equilibrium)': swing_l + diff * 0.500,
    '0.618 (Golden Pocket)': swing_l + diff * 0.618,
    '0.705 (Institutional OTE)': swing_l + diff * 0.705,
    '0.786': swing_l + diff * 0.786,
    '1.000 (High)': swing_h
}
print("\nFibonacci Retracement of Friday Drop:")
for k, v in fibs.items():
    print(f"  {k}: {v:.2f}")

# H4 EMAs (EMA 20, 50, 200)
closes_h4 = [b['close'] for b in h4]
def calc_ema(prices, period):
    k = 2.0 / (period + 1.0)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = p * k + ema * (1 - k)
    return ema

ema20_h4 = calc_ema(closes_h4, 20)
ema50_h4 = calc_ema(closes_h4, 50)
ema200_h4 = calc_ema(closes_h4, 200)
print(f"\nH4 EMAs -> EMA20: {ema20_h4:.2f}, EMA50: {ema50_h4:.2f}, EMA200: {ema200_h4:.2f}")

# H1 FVGs (Fair Value Gaps) from Friday drop
print("\nH1 FVGs (Bearish Imbalances) on 2026-10-30:")
for i in range(2, len(h1)):
    b0 = h1[i-2] # candle 1
    b1 = h1[i-1] # candle 2 (impulse)
    b2 = h1[i]   # candle 3
    if b1['time'] >= datetime(2026, 10, 30, 0, 0):
        # Bearish FVG: Low of candle 1 > High of candle 3
        if b0['low'] > b2['high']:
            print(f"Bearish FVG at {b1['time'].strftime('%H:%M')}: Upper {b0['low']:.2f} - Lower {b2['high']:.2f} (Gap: {b0['low'] - b2['high']:.2f} USD)")

# M15 Range at Friday close
m15_late = [b for b in m15 if b['time'] >= datetime(2026, 10, 30, 20, 0)]
m15_late_h = max(b['high'] for b in m15_late)
m15_late_l = min(b['low'] for b in m15_late)
print(f"\nM15 Late Friday Consolidation Range: {m15_late_l:.2f} - {m15_late_h:.2f} (Width: {m15_late_h - m15_late_l:.2f} USD)")
