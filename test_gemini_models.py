import json
import urllib.request
import urllib.error

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\config.json', 'r') as f:
    cfg = json.load(f)

api_key = cfg.get('gemini_api_key', '')
print('Has API key:', bool(api_key))

# Models from user screenshot:
# Gemini 3.5 Flash Lite
# Gemini 3.6 Flash
# Gemini 3.1 Flash Lite
models_to_test = [
    'gemini-3.5-flash-lite',
    'models/gemini-3.5-flash-lite',
    'gemini-3.6-flash',
    'models/gemini-3.6-flash',
    'gemini-3.1-flash-lite',
    'models/gemini-3.1-flash-lite',
    'gemini-2.0-flash',
    'gemini-1.5-flash'
]

for m in models_to_test:
    endpoint = m if m.startswith('models/') else f'models/{m}'
    url = f'https://generativelanguage.googleapis.com/v1beta/{endpoint}:generateContent?key={api_key}'
    body = {
        'contents': [{'parts': [{'text': 'Respond in json: {"ping": "pong"}'}]}],
        'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json'}
    }
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            res_str = resp.read().decode('utf-8', errors='ignore')
            print(f'SUCCESS: {m} (Code {resp.status}) -> {res_str[:120]}')
            break
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        print(f'FAIL: {m} -> HTTP {e.code}: {err_body[:180]}')
    except Exception as ex:
        print(f'ERROR: {m} -> {ex}')
