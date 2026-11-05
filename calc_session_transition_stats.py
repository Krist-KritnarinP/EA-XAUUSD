import struct, glob
from datetime import datetime, timezone, timedelta

files_h1 = glob.glob('C:/Users/Kritnarin/AppData/Roaming/MetaQuotes/Terminal/**/GOLD60.hst', recursive=True)
with open(files_h1[0], 'rb') as f:
    f.read(148)
    bars = []
    while True:
        c = f.read(60)
        if len(c) < 60: break
        t, o, h, l, cl, v, s, r = struct.unpack('<qddddqiq', c)
        bars.append({'t': t, 'o': o, 'h': h, 'l': l, 'c': cl, 'v': v})

# Group bars by day (Server Time)
# Server time:
# Pre-Market Asian: 04:00 - 08:00
# London Window: 08:00 - 11:30
# Pre-NY Handover: 12:00 - 15:00
# NY Session: 15:00 - 18:00

days = {}
for b in bars:
    dt = datetime.fromtimestamp(b['t'], tz=timezone(timedelta(hours=2)))
    d_str = dt.strftime('%Y-%m-%d')
    if d_str not in days: days[d_str] = {}
    days[d_str][dt.hour] = b

# Analyze days where London broke down (Bearish Breakdown)
# In London (bars 8, 9, 10): price broke below Asian Low (min of bars 4, 5, 6, 7)
total_breakdown_days = 0
continued_down = 0
spiked_above_london_high = 0

for d_str, h_dict in days.items():
    asian_bars = [h_dict[h] for h in [4, 5, 6, 7] if h in h_dict]
    london_bars = [h_dict[h] for h in [8, 9, 10] if h in h_dict]
    ny_bars = [h_dict[h] for h in [12, 13, 14, 15, 16, 17] if h in h_dict]
    
    if len(asian_bars) >= 3 and len(london_bars) >= 2 and len(ny_bars) >= 3:
        asian_low = min(b['l'] for b in asian_bars)
        london_low = min(b['l'] for b in london_bars)
        london_high = max(b['h'] for b in london_bars)
        
        # Did London breakdown below Asian Low by >= $2?
        if (asian_low - london_low) >= 2.0:
            total_breakdown_days += 1
            
            # Check NY transition (bars 12 to 17):
            # Did NY spike above London High + buffer ($4)?
            ny_max_high = max(b['h'] for b in ny_bars)
            ny_min_low = min(b['l'] for b in ny_bars)
            
            # Did it continue down to make a lower low than London?
            if ny_min_low < london_low:
                continued_down += 1
            
            # Did it spike above the London SL zone (London High + 2 USD)?
            if ny_max_high >= (london_high + 2.0):
                spiked_above_london_high += 1

print(f"Total London Breakdown Days Analyzed: N={total_breakdown_days}")
print(f"Continued Down (Trend Continuation into NY): {continued_down}/{total_breakdown_days} ({continued_down/total_breakdown_days*100:.1f}%)")
print(f"Spiked above London High (SL Hunt Reversal): {spiked_above_london_high}/{total_breakdown_days} ({spiked_above_london_high/total_breakdown_days*100:.1f}%)")
