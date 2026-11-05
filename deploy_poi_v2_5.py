import os, shutil

mt4_dir = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts'
scratch_dir = r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4'
archive_dir = os.path.join(mt4_dir, '_archive_experts')
os.makedirs(archive_dir, exist_ok=True)
metaeditor = r'C:\Program Files (x86)\MetaTrader 4\metaeditor.exe'

# Read Tester v1 content
src_tester = os.path.join(mt4_dir, 'Gold_POI_Sniper_Tester_v1.mq4')
if not os.path.exists(src_tester):
    src_tester = os.path.join(scratch_dir, 'Gold_POI_Sniper_Tester_v1.mq4')

with open(src_tester, 'r', encoding='utf-8') as f:
    tester_code = f.read()

tester_code = tester_code.replace('Gold_POI_Sniper_Tester_v1.mq4', 'Gold_POI_Sniper_Tester_v2_5.mq4')

for p in [os.path.join(mt4_dir, 'Gold_POI_Sniper_Tester_v2_5.mq4'), os.path.join(scratch_dir, 'Gold_POI_Sniper_Tester_v2_5.mq4')]:
    with open(p, 'w', encoding='utf-8') as f:
        f.write(tester_code)

# Read Master v1 content
src_master = os.path.join(mt4_dir, 'Gold_POI_Sniper_Master_v1.mq4')
if not os.path.exists(src_master):
    src_master = os.path.join(scratch_dir, 'Gold_POI_Sniper_Master_v1.mq4')

with open(src_master, 'r', encoding='utf-8') as f:
    master_code = f.read()

master_code = master_code.replace('Gold_POI_Sniper_Master_v1.mq4', 'Gold_POI_Sniper_Master_v2_5.mq4')

for p in [os.path.join(mt4_dir, 'Gold_POI_Sniper_Master_v2_5.mq4'), os.path.join(scratch_dir, 'Gold_POI_Sniper_Master_v2_5.mq4')]:
    with open(p, 'w', encoding='utf-8') as f:
        f.write(master_code)

# Archive v0 and v1 files from MT4 Experts
for fname in ['Gold_POI_Sniper_Master_v0.ex4', 'Gold_POI_Sniper_Master_v0.mq4',
              'Gold_POI_Sniper_Tester_v0.ex4', 'Gold_POI_Sniper_Tester_v0.mq4',
              'Gold_POI_Sniper_Master_v1.ex4', 'Gold_POI_Sniper_Master_v1.mq4',
              'Gold_POI_Sniper_Tester_v1.ex4', 'Gold_POI_Sniper_Tester_v1.mq4']:
    src = os.path.join(mt4_dir, fname)
    dst = os.path.join(archive_dir, fname)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f'Archived {fname}')

import subprocess
# Compile both new v2_5 files
for fname in ['Gold_POI_Sniper_Tester_v2_5.mq4', 'Gold_POI_Sniper_Master_v2_5.mq4']:
    target = os.path.join(mt4_dir, fname)
    log_name = 'compile_' + fname.replace('.mq4', '.log')
    log_path = os.path.join(scratch_dir, log_name)
    subprocess.call([metaeditor, f'/compile:{target}', f'/log:{log_path}'])
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-16-le', errors='replace') as lf:
            print(f'=== Compile {fname} ===')
            print(lf.read().strip())

print('Deploy completed successfully!')
