with open('gold_ai_agent.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('v6.3.5-Beta', 'v6.3.6')
text = text.replace('v6.3.5 Beta', 'v6.3.6')
text = text.replace('v6.3.5', 'v6.3.6')

old_ny_desc = 'NY Institutional Trend-Rider at EMA50 Pullback (ADX >= 18, RR 2.2:1 Target)'
new_ny_desc = 'NY Institutional ICT Silver Bullet & Breaker Block (ADR Exhaustion Guard, RR 2.5:1 Target)'
text = text.replace(old_ny_desc, new_ny_desc)

old_sw_desc = '**Risk Profile:** Fixed `0.02 Lots` • Asymmetric R:R `1 : 5.0` • Auto-BE @ `1.5R` + Dynamic ATR Trail'
new_sw_desc = '**Risk Profile:** Fixed `0.02 Lots` • Asymmetric R:R `1 : 5.0` • **2-Tier Partial TP** (Lock 50% @ `1.5R`, Run 50% @ `5.0R`)'
text = text.replace(old_sw_desc, new_sw_desc)

old_as_desc = 'Asian Range Liquidity Squeeze ($3-$10 Compression, Tight SL $6 / TP $5)'
new_as_desc = 'Asian SMC Range Equilibrium ($3-$12 Range, Dynamic SL, 50% EQ Target)'
text = text.replace(old_as_desc, new_as_desc)

with open('gold_ai_agent.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated gold_ai_agent.py to v6.3.6!')
