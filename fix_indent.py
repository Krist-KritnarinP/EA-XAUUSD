with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('            else:\n                # Silent fallback to next model in cascade without console noise\n            pass', '            else:\n                # Silent fallback to next model in cascade without console noise\n                pass')
text = text.replace('        except Exception as e:\n            safe_print(f"    [Gemini Fallback] {model_name}: {e}")', '        except Exception as e:\n            pass')

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Indentation fixed.')
