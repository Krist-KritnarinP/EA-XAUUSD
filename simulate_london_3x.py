# -*- coding: utf-8 -*-
import json
from collections import defaultdict

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v641_official_forensic.json", "r", encoding="utf-8") as f:
    trades = json.load(f)

print(f"Loaded {len(trades)} trades")

def get_session(t_str, eng):
    hr = int(t_str[11:13])
    if "Asian" in eng or (2 <= hr < 8):
        return "Asian"
    elif "New York" in eng or (15 <= hr < 22):
        return "New York"
    else:
        return "London"

for t in trades:
    t["session"] = get_session(t["open_time"], t.get("engine", "London Sniper"))

base_total_pnl = sum(t["profit"] for t in trades)
london_trades = [t for t in trades if t["session"] == "London" or t.get("engine") == "London Sniper"]
base_london_pnl = sum(t["profit"] for t in london_trades)
print(f"Base Total PnL: ${base_total_pnl:,.2f}")
print(f"Base London Trades: {len(london_trades)} trades, Base London PnL: ${base_london_pnl:,.2f}")

# Simulation: London 3x Lots
sim_trades = []
sim_equity = 2000.0
sim_peak = 2000.0
sim_max_dd_usd = 0.0
sim_max_dd_pct = 0.0

monthly_base = defaultdict(float)
monthly_sim = defaultdict(float)

for t in trades:
    is_london = (t["session"] == "London" or t.get("engine") == "London Sniper")
    pnl = t["profit"]
    m = t["close_time"][:7] if t["close_time"] else t["open_time"][:7]
    monthly_base[m] += pnl
    
    if is_london:
        sim_pnl = pnl * 3.0
    else:
        sim_pnl = pnl
        
    monthly_sim[m] += sim_pnl
    sim_equity += sim_pnl
    if sim_equity > sim_peak:
        sim_peak = sim_equity
    dd_usd = sim_peak - sim_equity
    dd_pct = (dd_usd / sim_peak) * 100.0 if sim_peak > 0 else 0.0
    if dd_usd > sim_max_dd_usd:
        sim_max_dd_usd = dd_usd
    if dd_pct > sim_max_dd_pct:
        sim_max_dd_pct = dd_pct
        
    sim_trades.append({
        "ticket": t["ticket"],
        "open_time": t["open_time"],
        "type": t["type"],
        "is_london": is_london,
        "base_profit": pnl,
        "sim_profit": sim_pnl,
        "equity": sim_equity
    })

sim_net = sum(t["sim_profit"] for t in sim_trades)
sim_wins = [t["sim_profit"] for t in sim_trades if t["sim_profit"] > 0]
sim_losses = [t["sim_profit"] for t in sim_trades if t["sim_profit"] < 0]
sim_gw = sum(sim_wins)
sim_gl = abs(sum(sim_losses))
sim_pf = sim_gw / sim_gl if sim_gl > 0 else 999.0

print("\n" + "="*75)
print("=== QUANT SIMULATION: LONDON SESSION 3X LOTS / RISK (15% RISK) ===")
print("="*75)
print(f"Initial Deposit: $2,000.00")
print(f"Base Net Profit:       ${base_total_pnl:10,.2f}  --->  Simulated Net Profit: ${sim_net:10,.2f}")
print(f"Net Profit Increase:   +${sim_net - base_total_pnl:10,.2f} (+{(sim_net/base_total_pnl - 1)*100:.1f}% surge!)")
print(f"Ending Equity:         ${2000 + base_total_pnl:10,.2f}  --->  Simulated Equity:     ${sim_equity:10,.2f}")
print(f"Gross Profit:          ${sim_gw:10,.2f}  |  Gross Loss: -${sim_gl:10,.2f}")
print(f"Profit Factor:         {sim_pf:.2f} (Base was 1.91)")
print(f"Max Equity Drawdown:   ${sim_max_dd_usd:10,.2f} ({sim_max_dd_pct:.2f}%) (Base was 17.59%)")
print(f"Largest Win Trade:     ${max(sim_wins):10,.2f} (Base was $780.50)")
print(f"Largest Loss Trade:    ${min(sim_losses):10,.2f} (Base was -$283.00)")

print("\n" + "="*75)
print(f"{'Month':<10} | {'Base Net':<14} | {'London 3x Net':<16} | {'Difference':<14}")
print("="*75)
for m in sorted(monthly_base.keys()):
    diff = monthly_sim[m] - monthly_base[m]
    print(f"{m:<10} | ${monthly_base[m]:+12.2f} | ${monthly_sim[m]:+14.2f} | ${diff:+12.2f}")
print("="*75)

# Consecutive streaks in 3x
curr_w = 0
curr_w_val = 0.0
max_w = 0
max_w_val = 0.0
curr_l = 0
curr_l_val = 0.0
max_l = 0
max_l_val = 0.0

for t in sim_trades:
    if t["sim_profit"] > 0:
        curr_w += 1
        curr_w_val += t["sim_profit"]
        if curr_w > max_w:
            max_w = curr_w
            max_w_val = curr_w_val
        curr_l = 0
        curr_l_val = 0.0
    else:
        curr_l += 1
        curr_l_val += t["sim_profit"]
        if curr_l > max_l:
            max_l = curr_l
            max_l_val = curr_l_val
        curr_w = 0
        curr_w_val = 0.0

print(f"Max Consecutive Wins: {max_w} trades | Total Profit: ${max_w_val:,.2f}")
print(f"Max Consecutive Losses: {max_l} trades | Total Loss: ${max_l_val:,.2f}")
