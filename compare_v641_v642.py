# -*- coding: utf-8 -*-
import json

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v641_trades.json", "r", encoding="utf-8") as f:
    t641 = json.load(f)

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v642_all_trades.json", "r", encoding="utf-8") as f:
    t642 = json.load(f)

print(f"v6.4.1 trades: {len(t641)}")
print(f"v6.4.2 trades: {len(t642)}")

# Let's see monthly net profit comparison
from collections import defaultdict
m641 = defaultdict(float)
m642 = defaultdict(float)

for t in t641:
    m = t["close_time"][:7] if "close_time" in t and t["close_time"] else t["open_time"][:7]
    val = t.get("profit", t.get("pnl", 0.0))
    m641[m] += val

for t in t642:
    m = t["close_time"][:7] if "close_time" in t and t["close_time"] else t["open_time"][:7]
    m642[m] += t["profit"]

all_months = sorted(set(list(m641.keys()) + list(m642.keys())))
print(f"{'Month':<10} | {'v6.4.1 Net':<12} | {'v6.4.2 Net':<12} | {'Difference':<12}")
print("-" * 55)
for m in all_months:
    diff = m642[m] - m641[m]
    print(f"{m:<10} | ${m641[m]:+10.2f} | ${m642[m]:+10.2f} | ${diff:+10.2f}")
