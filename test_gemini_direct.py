import sys
sys.path.append(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4')
import gold_ai_agent as g

cfg = g.load_config()
key = cfg.get('gemini_api_key', '')
prompt = 'Classify gold market news sentiment. Respond strictly in json: {"sentiment": "BULLISH", "confidence": 0.95}'
res = g.call_gemini_json_safe(prompt, key)
print('Direct Gemini Call Result:', res)
