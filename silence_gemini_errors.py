with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'safe_print(f"    [Gemini HTTP Error {he.code}] {model_name}: {he}")'
replacement = '# Silent fallback to next model in cascade without console noise\n            pass'

if target in text:
    text = text.replace(target, replacement)
    with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Silenced HTTP error prints in gold_ai_agent.py')
