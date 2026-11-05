with open('GoldSniper_Bridge_v6_3_5_beta.mq4', 'r', encoding='latin1') as f:
    text = f.read()

# 1. Scalper close inside ManageOpenPositions
idx_mop = text.find('void ManageOpenPositions()')
s3 = '// Auto-close open scalp at 07:45 before London volatility'
i5 = text.find(s3, idx_mop)
end3 = '// 2. LONDON SNIPER RUNNER MANAGEMENT'
i6 = text.find(end3, i5)
print('Scalper close block found:', i5 != -1, i6 != -1, 'length:', i6 - i5)

# 2. Asian block inside OnTick
idx_ontick = text.find('// 1. ENGINE A: ASIAN SQUEEZE RANGE SWEEPER')
s1 = 'double asianSpan = aHigh - aLow;'
i1 = text.find(s1, idx_ontick)
end1 = '// 2. ENGINE B: LONDON SNIPER RUNNER'
i2 = text.find(end1, i1)
print('Asian block found:', i1 != -1, i2 != -1, 'length:', i2 - i1)

# 3. NY block inside OnTick
idx_ny = text.find('// 3. ENGINE C: NEW YORK INSTITUTIONAL TREND-RIDER ENGINE')
s2 = '// Volume filter & ADX Trend filter for NY Expansion'
i3 = text.find(s2, idx_ny)
end2 = '// 4. ENGINE D: THE LIQUIDITY SWEEP FADE'
i4 = text.find(end2, i3)
print('NY block found:', i3 != -1, i4 != -1, 'length:', i4 - i3)
