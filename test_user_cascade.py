import json
import urllib.request
import urllib.error

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\config.json', 'r') as f:
    cfg = json.load(f)

api_key = cfg.get('gemini_api_key', '')

models = [
    'models/gemini-3.5-flash-lite',
    'models/gemini-3.1-flash-lite',
    'models/gemini-3.6-flash'
]

for m in models:
    url = f'https://generativelanguage.googleapis.com/v1beta/{m}:generateContent?key={api_key}'
    body = {
        'contents': [{'parts': [{'text': 'Respond in json: {"ping": "pong"}'}]}],
        'generationConfig': {'temperature': 0.1, 'responseMimeType': 'application/json'}
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            print(f'{m}: SUCCESS (Code {resp.status})')
    except urllib.error.HTTPError as e:
        print(f'{m}: HTTPError {e.code} -> {e.read().decode("utf-8", errors="ignore")[:150]}')
    except Exception as ex:
        print(f'{m}: Exception -> {ex}')
