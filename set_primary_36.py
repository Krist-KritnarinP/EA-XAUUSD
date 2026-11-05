with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_cascade_match = re.search(r'MODEL_CASCADE\s*=\s*\[.*?\]', text, re.DOTALL)
if old_cascade_match:
    new_cascade = '''MODEL_CASCADE = [
    "models/gemini-3.6-flash",          # Primary (Verified Code 200 in your AI Studio)
    "models/gemini-3.1-flash-lite",     # Fallback 1 (500 RPD)
    "models/gemini-2.0-flash"           # Fallback 2
]'''
    text = text[:old_cascade_match.start()] + new_cascade + text[old_cascade_match.end():]
    with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated MODEL_CASCADE with gemini-3.6-flash as primary!')
