import struct, os, glob
from datetime import datetime, timezone

hst_files = glob.glob('C:/Users/Kritnarin/AppData/Roaming/MetaQuotes/Terminal/**/GOLD1440.hst', recursive=True)
if not hst_files:
    print('HST not found')
    exit()

hst_path = hst_files[0]
bars = []
with open(hst_path, 'rb') as f:
    header = f.read(148)
    while True:
        chunk = f.read(60)
        if len(chunk) < 60:
            break
        t, o, h, l, c, v, s, r = struct.unpack('<qddddqiq', chunk)
        bars.append({'time': t, 'open': o, 'high': h, 'low': l, 'close': c, 'vol': v})

print(f'Total bars: {len(bars)}')
print('Last 10 bars:')
for b in bars[-10:]:
    dt = datetime.fromtimestamp(b['time'], tz=timezone.utc).strftime('%Y-%m-%d')
    print(f"{dt}: O={b['open']:.2f}, H={b['high']:.2f}, L={b['low']:.2f}, C={b['close']:.2f}, Range={b['high']-b['low']:.2f}")

# Short squeeze stats:
# Criteria: When price drops into an extended low and creates a Double Bottom / Rejection wick (Lower wick >= 35% of total bar range or absorption),
# How often does price surge >= $35, $50, $70 within the next 1-3 bars?
tests_35 = 0
bounces_35 = 0
tests_50 = 0
bounces_50 = 0
tests_70 = 0
bounces_70 = 0

for i in range(50, len(bars)-3):
    recent_low = min(b['low'] for b in bars[i-15:i])
    # Tested near recent low or made new low
    if bars[i]['low'] <= recent_low + 5.0:
        bar_range = bars[i]['high'] - bars[i]['low']
        lower_wick = min(bars[i]['open'], bars[i]['close']) - bars[i]['low']
        # If there is rejection wick or small body (absorption)
        if bar_range > 0 and (lower_wick / bar_range >= 0.25):
            tests_35 += 1
            max_future = max(bars[i+1]['high'], bars[i+2]['high'], bars[i+3]['high'])
            bounce = max_future - bars[i]['low']
            if bounce >= 35.0:
                bounces_35 += 1
            if bounce >= 50.0:
                bounces_50 += 1
            if bounce >= 70.0:
                bounces_70 += 1

print(f"Sample size of rejection/absorption setups: N={tests_35}")
print(f"Bounce >= $35 within 3 days (clearing M15/H1 swing highs): {bounces_35}/{tests_35} ({bounces_35/tests_35*100:.1f}%)")
print(f"Bounce >= $50 within 3 days (clearing H4 major resistance): {bounces_50}/{tests_35} ({bounces_50/tests_35*100:.1f}%)")
print(f"Bounce >= $70 within 3 days (full Short Squeeze / Liquidity Sweep): {bounces_70}/{tests_35} ({bounces_70/tests_35*100:.1f}%)")
