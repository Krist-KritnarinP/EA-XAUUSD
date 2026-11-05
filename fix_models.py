with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"models/gemini-3.5-flash-lite"', '"models/gemini-2.0-flash"')
text = text.replace('"models/gemini-flash-lite-latest"', '"models/gemini-1.5-flash"')
text = text.replace('"models/gemini-2.5-flash-lite"', '"models/gemini-1.5-flash-8b"')

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated MODEL_CASCADE in gold_ai_agent.py')
