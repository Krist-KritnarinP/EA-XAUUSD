import os

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v2_5.mq4", "r", encoding="utf-8") as f:
    v25_code = f.read()

# Let's verify what v25 ExportMarketState looks like
pos1 = v25_code.find("void ExportMarketState()")
pos2 = v25_code.find("bool IsTradingTime()")
export_func_v25 = v25_code[pos1:pos2]
print("Export func length in v25:", len(export_func_v25))
