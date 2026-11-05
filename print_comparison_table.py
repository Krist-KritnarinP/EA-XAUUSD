import json

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\comparison_monthly_session.json', 'r') as f:
    res = json.load(f)

months = res['months']
betab = res['betab']
v623 = res['v623']
poi = res['poi']

def print_model_table(name, model_data):
    print(f"\n==================== {name} ====================")
    print(f"{'Month':<8} | {'Asian (Tr/W/PnL)':<22} | {'London (Tr/W/PnL)':<22} | {'New York (Tr/W/PnL)':<22} | {'Total PnL':<10}")
    print("-" * 95)
    tot_tr = 0
    tot_w = 0
    tot_pnl = 0.0
    tot_s = {'Asian': [0,0,0.0], 'London': [0,0,0.0], 'New York': [0,0,0.0]}
    
    for m in months:
        d = model_data.get(m, {
            'all': {'trades': 0, 'wins': 0, 'pnl': 0.0},
            'Asian': {'trades': 0, 'wins': 0, 'pnl': 0.0},
            'London': {'trades': 0, 'wins': 0, 'pnl': 0.0},
            'New York': {'trades': 0, 'wins': 0, 'pnl': 0.0}
        })
        
        a = d['Asian']
        l = d['London']
        ny = d['New York']
        al = d['all']
        
        tot_tr += al['trades']
        tot_w += al['wins']
        tot_pnl += al['pnl']
        
        for s, s_data in [('Asian', a), ('London', l), ('New York', ny)]:
            tot_s[s][0] += s_data['trades']
            tot_s[s][1] += s_data['wins']
            tot_s[s][2] += s_data['pnl']
            
        a_str = f"{a['trades']} / {a['wins']} (${a['pnl']:+.1f})" if a['trades'] > 0 else "-"
        l_str = f"{l['trades']} / {l['wins']} (${l['pnl']:+.1f})" if l['trades'] > 0 else "-"
        ny_str = f"{ny['trades']} / {ny['wins']} (${ny['pnl']:+.1f})" if ny['trades'] > 0 else "-"
        
        print(f"{m:<8} | {a_str:<22} | {l_str:<22} | {ny_str:<22} | ${al['pnl']:+9.2f}")
        
    print("-" * 95)
    a_tot_str = f"{tot_s['Asian'][0]} / {tot_s['Asian'][1]} (${tot_s['Asian'][2]:+.1f})"
    l_tot_str = f"{tot_s['London'][0]} / {tot_s['London'][1]} (${tot_s['London'][2]:+.1f})"
    ny_tot_str = f"{tot_s['New York'][0]} / {tot_s['New York'][1]} (${tot_s['New York'][2]:+.1f})"
    print(f"{'TOTAL':<8} | {a_tot_str:<22} | {l_tot_str:<22} | {ny_tot_str:<22} | ${tot_pnl:+9.2f}")

print_model_table("1. GoldSniper v6.3.8-BetaB", betab)
print_model_table("2. GoldSniper v6.2.3-x3", v623)
print_model_table("3. Gold POI Sniper v2.5", poi)
