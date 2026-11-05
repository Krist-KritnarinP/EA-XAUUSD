import urllib.request, json
from datetime import datetime, timezone, timedelta

def parse_event_time_thai(iso_str):
    try:
        main_part = iso_str[:19]
        dt = datetime.strptime(main_part, '%Y-%m-%dT%H:%M:%S')
        tz_part = iso_str[19:]
        sign = 1 if tz_part[0] == '+' else -1
        offset_hours = sign * int(tz_part[1:3])
        offset_minutes = sign * int(tz_part[4:6])
        event_tz = timezone(timedelta(hours=offset_hours, minutes=offset_minutes))
        return dt.replace(tzinfo=event_tz).astimezone(timezone(timedelta(hours=7)))
    except Exception:
        return None

url = 'https://nfs.faireconomy.media/ff_calendar_thisweek.json'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))

usd_high = []
for e in data:
    if e.get('country') == 'USD' and e.get('impact') == 'High':
        dt = parse_event_time_thai(e['date'])
        usd_high.append({
            'title': e.get('title'),
            'time_th': dt.strftime('%A %d/%m %H:%M น.') if dt else 'N/A',
            'dt': dt,
            'forecast': e.get('forecast'),
            'previous': e.get('previous')
        })

print(f"Total High Impact USD events this week: {len(usd_high)}")
for e in usd_high:
    print(f"{e['time_th']} | {e['title']} | Forecast: {e['forecast']} | Prev: {e['previous']}")
