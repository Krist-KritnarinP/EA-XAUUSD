import struct, glob
from datetime import datetime, timezone

hst_files = glob.glob('C:/Users/Kritnarin/AppData/Roaming/MetaQuotes/Terminal/**/GOLD1440.hst', recursive=True)
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

# Downside Dump Analysis:
# Condition: Same 155 setups (where price broke to a multi-week low, showed an initial absorption/rejection wick).
# What percentage of the time does price BREAK the swing low (make a new lower low) within 1, 2, or 3 bars?
new_low_1d = 0
new_low_2d = 0
new_low_3d = 0
dump_more_than_30 = 0
dump_more_than_50 = 0
total_samples = 0

for i in range(50, len(bars)-3):
    recent_low = min(b['low'] for b in bars[i-15:i])
    if bars[i]['low'] <= recent_low + 5.0:
        bar_range = bars[i]['high'] - bars[i]['low']
        lower_wick = min(bars[i]['open'], bars[i]['close']) - bars[i]['low']
        if bar_range > 0 and (lower_wick / bar_range >= 0.25):
            total_samples += 1
            cur_low = bars[i]['low']
            
            # Check if day 1, 2, 3 makes a lower low than cur_low
            min_future = min(bars[i+1]['low'], bars[i+2]['low'], bars[i+3]['low'])
            if bars[i+1]['low'] < cur_low:
                new_low_1d += 1
            if min(bars[i+1]['low'], bars[i+2]['low']) < cur_low:
                new_low_2d += 1
            if min_future < cur_low:
                new_low_3d += 1
                if (cur_low - min_future) >= 30.0:
                    dump_more_than_30 += 1
                if (cur_low - min_future) >= 50.0:
                    dump_more_than_50 += 1

print(f"Total absorption setups analyzed: N={total_samples}")
print(f"Breakdown to NEW LOW within 1 Day (Day+1): {new_low_1d}/{total_samples} ({new_low_1d/total_samples*100:.1f}%)")
print(f"Breakdown to NEW LOW within 2 Days (Day+1 or Day+2): {new_low_2d}/{total_samples} ({new_low_2d/total_samples*100:.1f}%)")
print(f"Breakdown to NEW LOW within 3 Days (Total failure): {new_low_3d}/{total_samples} ({new_low_3d/total_samples*100:.1f}%)")
print(f"Severe Dump >= $30 below low (to < $3,945): {dump_more_than_30}/{total_samples} ({dump_more_than_30/total_samples*100:.1f}%)")
print(f"Severe Dump >= $50 below low (to < $3,925): {dump_more_than_50}/{total_samples} ({dump_more_than_50/total_samples*100:.1f}%)")
