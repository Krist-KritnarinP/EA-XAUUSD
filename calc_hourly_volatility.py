import struct, glob
from datetime import datetime, timezone, timedelta

files_h1 = glob.glob('C:/Users/Kritnarin/AppData/Roaming/MetaQuotes/Terminal/**/GOLD60.hst', recursive=True)
if not files_h1:
    print("H1 not found")
    exit()

bars = []
with open(files_h1[0], 'rb') as f:
    f.read(148)
    while True:
        c = f.read(60)
        if len(c) < 60: break
        t, o, h, l, cl, v, s, r = struct.unpack('<qddddqiq', c)
        bars.append({'t': t, 'o': o, 'h': h, 'l': l, 'c': cl, 'v': v})

# Calculate average hourly range by Thai Time (UTC+7)
hourly_ranges = {h: [] for h in range(24)}
for b in bars[-1000:]: # last 1000 H1 bars (~2 months of active trading)
    dt_th = datetime.fromtimestamp(b['t'], tz=timezone(timedelta(hours=7)))
    rng = b['h'] - b['l']
    hourly_ranges[dt_th.hour].append(rng)

print("Average Range ($) by Thai Hour (UTC+7):")
for h in range(24):
    avg_r = sum(hourly_ranges[h])/len(hourly_ranges[h]) if hourly_ranges[h] else 0
    bar_chart = "#" * int(avg_r)
    print(f"{h:02d}:00 TH | Avg Range: ${avg_r:5.2f} | {bar_chart}")
