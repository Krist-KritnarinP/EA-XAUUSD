import shutil
import os

mt4_experts = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
files = [
    "GoldSniper_Bridge_v6_3_4_beta.ex4",
    "GoldSniper_Bridge_v6_3_4_beta.mq4",
    "GoldSniper_Tester_v6_3_4_beta.ex4",
    "GoldSniper_Tester_v6_3_4_beta.mq4",
    "GoldSniper_Bridge_v6_3_3.ex4",
    "GoldSniper_Bridge_v6_3_3.mq4",
    "GoldSniper_Tester_v6_3_3.ex4",
    "GoldSniper_Tester_v6_3_3.mq4"
]

for f in files:
    src = os.path.join(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4", f)
    dst = os.path.join(mt4_experts, f)
    shutil.copy2(src, dst)
    print(f"Copied {f} -> {dst} ({os.path.getsize(dst)} bytes)")

print("\nAll 8 production files deployed to MT4 Experts successfully!")
