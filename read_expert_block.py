with open(r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\profiles\default\chart01.chr', 'r', encoding='latin1') as f:
    text = f.read()

import re
m = re.search(r'<expert>(.*?)</expert>', text, re.DOTALL)
if m:
    print(m.group(1))
else:
    print("No expert block found")
