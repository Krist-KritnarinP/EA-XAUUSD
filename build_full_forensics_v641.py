# -*- coding: utf-8 -*-
import re
import os
import json
import struct
from datetime import datetime
from collections import defaultdict

log_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log"
hst_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst"

with open(log_path, "r", encoding="latin1") as f:
    raw_lines = f.readlines()

# Run starts at line 5117 and ends at 6654
run_lines = raw_lines[5117:6654]

open_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?open #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)")
sl_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: stop loss #(\d+)\s+at\s+([\d\.]+)")
tp_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: take profit #(\d+)\s+at\s+([\d\.]+)")
close_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)")
modify_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?modify #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+[\d\.]+\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)")
desc_re = re.compile(r"\[(ASIAN SMC|SNIPER RUNNER|SWEEP FADE|NEW YORK INSTITUTIONAL|v6\.4\.1-HybridApex NY)\s+(BUY|SELL).*?\]\s+Ticket:\s+#(\d+)")

orders = {}
descriptions = {}

for line in run_lines:
    m_desc = desc_re.search(line)
    if m_desc:
        engine, side, t_num = m_desc.groups()
        t_num = int(t_num)
        if "ASIAN" in engine:
            descriptions[t_num] = "Asian Scalp"
        elif "SNIPER" in engine:
            descriptions[t_num] = "London Sniper"
        elif "NEW YORK" in engine or "NY" in engine:
            descriptions[t_num] = "New York Reversal"
        elif "SWEEP" in engine:
            descriptions[t_num] = "Sweep Fade"
        else:
            descriptions[t_num] = engine

    m_open = open_re.search(line)
    if m_open:
        t_time, t_num, t_type, t_lots, t_price, t_sl, t_tp = m_open.groups()
        t_num = int(t_num)
        orders[t_num] = {
            "ticket": t_num,
            "open_time": t_time[:16],
            "type": t_type.upper(),
            "lots": float(t_lots),
            "open_price": float(t_price),
            "init_sl": float(t_sl),
            "init_tp": float(t_tp),
            "close_time": None,
            "close_price": None,
            "exit_reason": "UNKNOWN",
            "profit": 0.0,
            "engine": "London Sniper",
            "modifications": []
        }

    m_mod = modify_re.search(line)
    if m_mod:
        t_time, t_num, t_type, t_lots, m_sl, m_tp = m_mod.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["modifications"].append((t_time[:16], float(m_sl), float(m_tp)))

    m_sl = sl_re.search(line)
    if m_sl:
        t_time, t_num, t_price = m_sl.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["exit_reason"] = "SL"

    m_tp = tp_re.search(line)
    if m_tp:
        t_time, t_num, t_price = m_tp.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["exit_reason"] = "TP"

    m_close = re.search(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+.*?at price\s+([\d\.]+)", line)
    if m_close:
        t_time, t_num, t_type, t_lots, t_price = m_close.groups()
        t_num = int(t_num)
        if t_num in orders and orders[t_num]["close_time"] is None:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["exit_reason"] = "MANUAL_OR_FRIDAY"

for t_num, eng in descriptions.items():
    if t_num in orders:
        orders[t_num]["engine"] = eng

trades = []
for t_num, ord_info in sorted(orders.items()):
    if ord_info["close_price"] is not None:
        if ord_info["type"] == "BUY":
            pts = ord_info["close_price"] - ord_info["open_price"]
        else:
            pts = ord_info["open_price"] - ord_info["close_price"]
        profit = pts * ord_info["lots"] * 100.0
        ord_info["profit"] = round(profit, 2)
        trades.append(ord_info)

# Read M15 bars
bars = []
with open(hst_path, "rb") as f:
    f.read(148)
    while True:
        data = f.read(60)
        if len(data) < 60: break
        t_sec, op, hp, lp, cp, vol, sp, rvol = struct.unpack("<Qddddqiq", data)
        bars.append({
            "time": datetime.utcfromtimestamp(t_sec),
            "open": op, "high": hp, "low": lp, "close": cp
        })

bar_map = {b["time"].strftime("%Y.%m.%d %H:%M"): i for i, b in enumerate(bars)}

for t in trades:
    ot = t["open_time"]
    ct = t["close_time"]
    dt_open = datetime.strptime(ot, "%Y.%m.%d %H:%M")
    dt_close = datetime.strptime(ct, "%Y.%m.%d %H:%M") if ct else dt_open
    duration_hrs = (dt_close - dt_open).total_seconds() / 3600.0
    t["holding_hours"] = round(duration_hrs, 2)

    idx_start = bar_map.get(ot)
    idx_end = bar_map.get(ct)
    if idx_start is not None and idx_end is not None:
        sub_bars = bars[idx_start:idx_end+1]
        if sub_bars:
            if t["type"] == "BUY":
                highest = max(b["high"] for b in sub_bars)
                lowest = min(b["low"] for b in sub_bars)
                t["mfe_usd"] = round(highest - t["open_price"], 2)
                t["mae_usd"] = round(t["open_price"] - lowest, 2)
                t["close_to_sl_usd"] = round(abs(lowest - t["init_sl"]), 2)
            else:
                highest = max(b["high"] for b in sub_bars)
                lowest = min(b["low"] for b in sub_bars)
                t["mfe_usd"] = round(t["open_price"] - lowest, 2)
                t["mae_usd"] = round(highest - t["open_price"], 2)
                t["close_to_sl_usd"] = round(abs(highest - t["init_sl"]), 2)
    else:
        t["mfe_usd"] = 0.0
        t["mae_usd"] = 0.0
        t["close_to_sl_usd"] = 0.0

print(f"Loaded {len(trades)} trades with HST tick paths")

# 1. Monthly trade count & PnL
monthly_trades = defaultdict(list)
for t in trades:
    m = t["close_time"][:7] if t["close_time"] else t["open_time"][:7]
    monthly_trades[m].append(t)

# 2. Session win rates per month
# Session mapping:
# 02:00 - 07:00: Asian
# 08:00 - 13:00: London
# 16:00 - 21:00: New York
def get_session(t_str, eng):
    hr = int(t_str[11:13])
    if "Asian" in eng or (2 <= hr < 8):
        return "Asian"
    elif "New York" in eng or (15 <= hr < 22):
        return "New York"
    else:
        return "London"

for t in trades:
    t["session"] = get_session(t["open_time"], t["engine"])

print("\n=== 1 & 2. MONTHLY TRADES & SESSION WIN RATES ===")
for m in sorted(monthly_trades.keys()):
    m_t = monthly_trades[m]
    m_wins = [t for t in m_t if t["profit"] > 0]
    m_pnl = sum(t["profit"] for t in m_t)
    wr = len(m_wins) / len(m_t) * 100
    
    # Session breakdown
    sess_stats = defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0})
    for t in m_t:
        s = t["session"]
        sess_stats[s]["count"] += 1
        sess_stats[s]["pnl"] += t["profit"]
        if t["profit"] > 0: sess_stats[s]["wins"] += 1
    
    sess_str = " | ".join([f"{s}: {st['wins']}/{st['count']} ({st['wins']/st['count']*100:.0f}% WR, ${st['pnl']:+.1f})" for s, st in sess_stats.items()])
    print(f"{m} | Total: {len(m_t):2d} trades | Win: {wr:4.1f}% | Net: ${m_pnl:+8.2f} || {sess_str}")

# 3. Winning trades forensics
win_trades = [t for t in trades if t["profit"] > 0]
loss_trades = [t for t in trades if t["profit"] <= 0]

avg_win_duration = sum(t["holding_hours"] for t in win_trades) / len(win_trades)
avg_loss_duration = sum(t["holding_hours"] for t in loss_trades) / len(loss_trades)
immediate_wins = [t for t in win_trades if t["mae_usd"] <= 0.50] # went into profit immediately (<$0.50 adverse excursion)
avg_close_to_sl = sum(t["close_to_sl_usd"] for t in win_trades) / len(win_trades)

print("\n=== 3. WINNING TRADES HOLDING & MAE FORENSICS ===")
print(f"Total Wins: {len(win_trades)}")
print(f"Average Holding Time (Wins): {avg_win_duration:.2f} hours (min: {min(t['holding_hours'] for t in win_trades)}h, max: {max(t['holding_hours'] for t in win_trades)}h)")
print(f"Average Margin from Initial SL: ${avg_close_to_sl:.2f} USD")
print(f"Immediate Wins (went green immediately, MAE <= $0.50): {len(immediate_wins)} of {len(win_trades)} ({len(immediate_wins)/len(win_trades)*100:.1f}%)")

# 4. Losing trades classification:
# - Category A: Pure Fakeout / Instant Loss (MFE <= $1.50 - never went anywhere, straight to SL)
# - Category B: Profit First / Give-back Loss (MFE >= $3.00 - was green nicely, then reversed to hit SL)
# - Category C: Structure Broken Trap (stayed in trade > 2 hours while price chopped back through entry)
cat_a = [t for t in loss_trades if t["mfe_usd"] < 1.50]
cat_b = [t for t in loss_trades if t["mfe_usd"] >= 3.00]
cat_c = [t for t in loss_trades if 1.50 <= t["mfe_usd"] < 3.00]

print("\n=== 4. LOSING TRADES ROOT-CAUSE BREAKDOWN ===")
print(f"Total Losses: {len(loss_trades)}")
print(f"Category A (Pure Fakeout / Straight to SL, MFE < $1.50): {len(cat_a)} trades ({len(cat_a)/len(loss_trades)*100:.1f}%), Loss: ${sum(t['profit'] for t in cat_a):.2f}")
print(f"Category B (Profit First / Reversed to SL, MFE >= $3.00): {len(cat_b)} trades ({len(cat_b)/len(loss_trades)*100:.1f}%), Loss: ${sum(t['profit'] for t in cat_b):.2f}")
print(f"Category C (Chop & False Break, $1.50 <= MFE < $3.00): {len(cat_c)} trades ({len(cat_c)/len(loss_trades)*100:.1f}%), Loss: ${sum(t['profit'] for t in cat_c):.2f}")

# 5. Engine/Technique breakdown per month
print("\n=== 5. SETUP / TECHNIQUE BREAKDOWN (ALL MONTHS) ===")
eng_stats = defaultdict(lambda: {"count": 0, "wins": 0, "losses": 0, "pnl": 0.0, "gross_win": 0.0, "gross_loss": 0.0})
for t in trades:
    eng = t["engine"]
    eng_stats[eng]["count"] += 1
    eng_stats[eng]["pnl"] += t["profit"]
    if t["profit"] > 0:
        eng_stats[eng]["wins"] += 1
        eng_stats[eng]["gross_win"] += t["profit"]
    else:
        eng_stats[eng]["losses"] += 1
        eng_stats[eng]["gross_loss"] += t["profit"]

for eng, st in eng_stats.items():
    wr = st["wins"] / st["count"] * 100
    pf = st["gross_win"] / abs(st["gross_loss"]) if st["gross_loss"] < 0 else 999.0
    print(f"Engine: {eng:22s} | Trades: {st['count']:2d} | W: {st['wins']:2d} | L: {st['losses']:2d} | WR: {wr:5.1f}% | Net: ${st['pnl']:+8.2f} | PF: {pf:4.2f}")

# 6. Consecutive Wins & Losses
max_consec_w = 0
curr_consec_w = 0
max_consec_w_val = 0.0
curr_consec_w_val = 0.0

max_consec_l = 0
curr_consec_l = 0
max_consec_l_val = 0.0
curr_consec_l_val = 0.0

for t in trades:
    if t["profit"] > 0:
        curr_consec_w += 1
        curr_consec_w_val += t["profit"]
        if curr_consec_w > max_consec_w:
            max_consec_w = curr_consec_w
            max_consec_w_val = curr_consec_w_val
        curr_consec_l = 0
        curr_consec_l_val = 0.0
    else:
        curr_consec_l += 1
        curr_consec_l_val += t["profit"]
        if curr_consec_l > max_consec_l:
            max_consec_l = curr_consec_l
            max_consec_l_val = curr_consec_l_val
        curr_consec_w = 0
        curr_consec_w_val = 0.0

print("\n=== 6. CONSECUTIVE STREAKS ===")
print(f"Max Consecutive Wins: {max_consec_w} trades | Total Profit: ${max_consec_w_val:,.2f}")
print(f"Max Consecutive Losses: {max_consec_l} trades | Total Loss: ${max_consec_l_val:,.2f}")

# 7 & 8. AI Impact Analysis
# Check trades during high news, adverse clusters, or lead-lag mismatch
# 9. Stress test: What if New York Risk / Lot is 3x?
print("\n=== 9. STRESS TEST: NEW YORK RISK 3X (3.5% -> 10.5% OR 3X LOTS) ===")
ny_trades = [t for t in trades if t["session"] == "New York" or t["engine"] == "New York Reversal"]
base_ny_pnl = sum(t["profit"] for t in ny_trades)
base_total_pnl = sum(t["profit"] for t in trades)

sim_total_pnl = 0.0
sim_gross_win = 0.0
sim_gross_loss = 0.0
sim_equity = 2000.0
sim_peak = 2000.0
sim_max_dd = 0.0

for t in trades:
    pnl = t["profit"]
    if t["session"] == "New York" or t["engine"] == "New York Reversal":
        pnl *= 3.0 # 3x lots
    sim_total_pnl += pnl
    if pnl > 0:
        sim_gross_win += pnl
    else:
        sim_gross_loss += pnl
    sim_equity += pnl
    if sim_equity > sim_peak:
        sim_peak = sim_equity
    dd = sim_peak - sim_equity
    if dd > sim_max_dd:
        sim_max_dd = dd

print(f"New York Trades Count: {len(ny_trades)}")
print(f"Base New York PnL: ${base_ny_pnl:,.2f} -> 3x New York PnL: ${base_ny_pnl*3:,.2f}")
print(f"Base Total PnL: ${base_total_pnl:,.2f} -> Simulated Total PnL (3x NY): ${sim_total_pnl:,.2f}")
sim_pf = sim_gross_win / abs(sim_gross_loss) if sim_gross_loss < 0 else 999.0
print(f"Simulated Gross Win: ${sim_gross_win:,.2f} | Gross Loss: ${sim_gross_loss:,.2f} | PF: {sim_pf:.2f}")
print(f"Simulated Max Equity Drawdown: ${sim_max_dd:,.2f} ({sim_max_dd/sim_peak*100:.1f}%)")

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v641_official_forensic.json", "w", encoding="utf-8") as f:
    json.dump(trades, f, indent=2)
print("Saved corrected v641_official_forensic.json successfully!")
