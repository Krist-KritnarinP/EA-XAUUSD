with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_cascade_match = re.search(r'MODEL_CASCADE\s*=\s*\[.*?\]', text, re.DOTALL)
if old_cascade_match:
    new_cascade = '''MODEL_CASCADE = [
    "models/gemini-3.5-flash-lite",      # 1. Primary (500 RPD / 15 RPM)
    "models/gemini-3.1-flash-lite",      # 2. Fallback 1 (500 RPD / 15 RPM)
    "models/gemini-3.6-flash"            # 3. Fallback 2 (20 RPD / 5 RPM)
]'''
    text = text[:old_cascade_match.start()] + new_cascade + text[old_cascade_match.end():]
    
    # Increase timeout default from 12 to 15s for flash-lite
    text = text.replace('def call_gemini_json_safe(prompt, api_key, temperature=0.2, timeout=12):',
                        'def call_gemini_json_safe(prompt, api_key, temperature=0.2, timeout=15):')
    
    with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated MODEL_CASCADE to user specified order: 3.5 -> 3.1 -> 3.6!')
