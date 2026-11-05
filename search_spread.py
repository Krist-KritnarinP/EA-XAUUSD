import os

search_paths = [
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch',
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4'
]

target = '"spread"'

for sp in search_paths:
    for root, dirs, files in os.walk(sp):
        for f in files:
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    if target in content and not p.endswith('.json'):
                        print('Match in:', p)
            except:
                pass
