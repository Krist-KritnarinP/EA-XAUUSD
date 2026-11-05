import os

p = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\compile_tester.log"
if os.path.exists(p):
    with open(p, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-16le")
    except:
        text = data.decode("latin1", errors="ignore")
    print(text.encode('ascii', errors='replace').decode('ascii'))
else:
    print("compile_tester.log not found")
