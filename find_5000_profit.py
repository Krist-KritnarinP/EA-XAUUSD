import glob, re, os

mds = glob.glob(r"C:\Users\Kritnarin\.gemini\antigravity\brain\cfa8c9a4-8fee-4644-8a15-fc849f6e4f64\*.md")
for m in mds:
    with open(m, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    # Search for numbers around 5000-5999 associated with profit or balance
    matches = re.findall(r"(?:net profit|profit|total profit|gain|กำไร|ยอดกำไร)[^\n]{0,60}(?:5,\d{3}|5\d{3})", txt, re.IGNORECASE)
    if matches:
        print("FILE:", os.path.basename(m))
        for x in matches[:5]:
            print("  ->", x.strip())
