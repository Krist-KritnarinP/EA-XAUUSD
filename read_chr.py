with open(r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\profiles\default\chart01.chr', 'r', encoding='latin1') as f:
    text = f.read()
for line in text.split('\n'):
    if 'expert' in line.lower() or 'symbol' in line.lower() or 'period' in line.lower():
        print(line.strip())
