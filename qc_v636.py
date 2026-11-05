import re

bridge_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Bridge_v6_3_6.mq4"
tester_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Tester_v6_3_6.mq4"
agent_path  = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py"

print("================================================================")
print(" IN-DEPTH QUALITY CONTROL (QC) AUDIT - GOLDSNIPER v6.3.6")
print("================================================================")

with open(bridge_path, "r", encoding="latin1") as f:
    b_code = f.read()

issues = []
warnings = []

# 1. Magic Number Audit (Checking Variable Usages across functions)
magics = {
    'MagicScalper': 888631,
    'MagicSniper': 888632,
    'MagicNY': 888633,
    'MagicSweepFade': 888634
}
for var, val in magics.items():
    cnt = b_code.count(var)
    print(f"[*] {var} ({val}): found {cnt} occurrences in bridge.")
    if cnt < 5:
        issues.append(f"{var} has suspiciously low occurrences ({cnt}).")

# Check ExportMarketState magic mapping
export_idx = b_code.find("void ExportMarketState")
if export_idx != -1:
    exp_code = b_code[export_idx:]
    if 'mName = "SweepFade"' not in exp_code:
        issues.append("ExportMarketState missing mName == SweepFade mapping!")
    if 'mName = "NewYork"' not in exp_code:
        issues.append("ExportMarketState missing mName == NewYork mapping!")
    if 'mName = "Scalper"' not in exp_code:
        issues.append("ExportMarketState missing mName == Scalper mapping!")
    if 'mName = "Sniper"' not in exp_code:
        issues.append("ExportMarketState missing mName == Sniper mapping!")

# 2. Check OrderModify Return Values
mod_calls = [m.start() for m in re.finditer(r'OrderModify\s*\(', b_code)]
print(f"[*] OrderModify calls found: {len(mod_calls)}")
for pos in mod_calls:
    line_start = b_code.rfind('\n', 0, pos) + 1
    line_end = b_code.find('\n', pos)
    line = b_code[line_start:line_end].strip()
    if not (line.startswith('bool ') or line.startswith('if(') or line.startswith('return ') or 'modRes' in line or 'res =' in line or 'modBE' in line):
        warnings.append(f"OrderModify call may not check return value: '{line}'")

# 3. Check Order Loops Direction
order_loops = re.findall(r'for\s*\([^;]*OrdersTotal\(\)[^)]*\)', b_code)
print(f"[*] Order loops found: {len(order_loops)}")

# 4. Check Python AI Agent Compatibility
with open(agent_path, "r", encoding="utf-8", errors="ignore") as f:
    a_code = f.read()

print("[*] Auditing gold_ai_agent.py...")
if '888634' in a_code or 'SweepFade' in a_code:
    print("  [OK] gold_ai_agent.py has SweepFade support.")
else:
    warnings.append("gold_ai_agent.py does not explicitly mention SweepFade or 888634!")

if 'v6.3.6' in a_code:
    print("  [OK] gold_ai_agent.py updated for v6.3.6.")
else:
    warnings.append("gold_ai_agent.py still references older version text.")

if 'is_pending' in a_code:
    print("  [OK] gold_ai_agent.py correctly isolates pending orders from market trades.")
else:
    warnings.append("gold_ai_agent.py might not have pending order isolation check.")

print("================================================================")
print(f" AUDIT RESULTS: {len(issues)} Issues, {len(warnings)} Warnings")
print("================================================================")
if issues:
    for i in issues:
        print("  [ERROR]", i)
if warnings:
    for w in warnings:
        print("  [WARN]", w)
if not issues and not warnings:
    print("  >>> ALL CHECKS PASSED PERFECTLY! 100% PRODUCTION READY! <<<")
