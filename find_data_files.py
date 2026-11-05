import json, os, glob

scratch = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"

# Check files
for pat in ["*betab*.py", "*betab*.json", "*v623*.json", "*v25*.json", "*poi*.json"]:
    matches = glob.glob(os.path.join(scratch, pat))
    for m in matches:
        print(f"Found: {os.path.basename(m)} ({os.path.getsize(m)} bytes)")
