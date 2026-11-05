import os
from compile_mq4 import compile_mq4
import shutil

# Paths
base_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
mt4_experts = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"

# ==============================================================================
# 1. REVERT v6.3.3 (Bridge & Tester) TO ORIGINAL LOGIC
# ==============================================================================
fixed_master = '''input ENUM_FLIP_MODE  OperatingMode           = MODE_TRI_SESSION_ULTRA; // Master Operating Architecture
input bool            UseFixedLot             = true;           // Enforce Fixed Lot Size (0.02) for All Trades
input double          FixedLotSize            = 0.02;           // Enforced Fixed Lot Size (0.02 Lot)
input double          SniperRiskPercent       = 5.0;            // London Sniper Dynamic Risk (% if FixedLot=false)'''

orig_master = '''input ENUM_FLIP_MODE  OperatingMode           = MODE_TRI_SESSION_ULTRA; // Master Operating Architecture
input double          SniperRiskPercent       = 5.0;            // London Sniper Risk (% of Equity - 2x Lot)'''

fixed_calc = '''double CalculateLotSize(double riskPct, double slUSD)
{
   if(UseFixedLot)
   {
      double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
      double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
      double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
      if(lotStep <= 0) lotStep = 0.01;
      double lot = MathFloor(FixedLotSize / lotStep) * lotStep;
      if(lot < minLot) lot = minLot;
      if(lot > maxLot) lot = maxLot;
      return lot;
   }

   double riskUsd = AccountEquity() * (riskPct / 100.0);'''

orig_calc = '''double CalculateLotSize(double riskPct, double slUSD)
{
   double riskUsd = AccountEquity() * (riskPct / 100.0);'''

v633_files = [
    os.path.join(base_dir, "GoldSniper_Bridge_v6_3_3.mq4"),
    os.path.join(base_dir, "GoldSniper_Tester_v6_3_3.mq4")
]

for fp in v633_files:
    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        c = f.read()
    if fixed_master in c:
        c = c.replace(fixed_master, orig_master)
    if fixed_calc in c:
        c = c.replace(fixed_calc, orig_calc)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(c)
    ok = compile_mq4(fp)
    print(f"Reverted & Compiled {os.path.basename(fp)}: OK = {ok}")

# ==============================================================================
# 2. UPDATE v6.3.4-Beta: ENFORCE LOT 0.02 ONLY ON SWEEP FADE (ไม้สวน B+)
# ==============================================================================
v634_files = [
    os.path.join(base_dir, "GoldSniper_Bridge_v6_3_4_beta.mq4"),
    os.path.join(base_dir, "GoldSniper_Tester_v6_3_4_beta.mq4")
]

for fp in v634_files:
    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        c = f.read()

    # Revert Master inputs to original (keep London, NY, Scalper original)
    if fixed_master in c:
        c = c.replace(fixed_master, orig_master)
    if fixed_calc in c:
        c = c.replace(fixed_calc, orig_calc)

    # In Sweep Fade inputs: enforce SweepFadeFixedLot = 0.02
    old_sweep_in = '''input string          Header_SweepFade        = "=== LIQUIDITY SWEEP FADE (v6.3.4 Beta) ===";
input bool            EnableSweepFadeTrade    = false;          // Enable Auto-Trade on Liquidity Sweep Fade (Default False for Signal Mode)
input bool            EnableSweepFadeSignal   = true;           // Enable Broadcast Grade A+ Alpha Sweep Signal to Discord
input double          SweepFadeRiskPercent    = 1.0;            // Risk Percent per Sweep Fade Trade
input double          SweepMinWickRatio       = 0.35;           // Min Rejection Wick Ratio (>= 35% Pin-bar / Rejection)'''

    old_sweep_in_tester = '''input string          Header_SweepFade        = "=== LIQUIDITY SWEEP FADE (v6.3.4 Beta) ===";
input bool            EnableSweepFadeTrade    = true;           // Enable Auto-Trade on Liquidity Sweep Fade (Default False for Signal Mode)
input bool            EnableSweepFadeSignal   = true;           // Enable Broadcast Grade A+ Alpha Sweep Signal to Discord
input double          SweepFadeRiskPercent    = 1.0;            // Risk Percent per Sweep Fade Trade
input double          SweepMinWickRatio       = 0.35;           // Min Rejection Wick Ratio (>= 35% Pin-bar / Rejection)'''

    new_sweep_in = '''input string          Header_SweepFade        = "=== LIQUIDITY SWEEP FADE (v6.3.4 Beta) ===";
input bool            EnableSweepFadeTrade    = false;          // Enable Auto-Trade on Liquidity Sweep Fade (Default False for Signal Mode)
input bool            EnableSweepFadeSignal   = true;           // Enable Broadcast Grade A+ Alpha Sweep Signal to Discord
input double          SweepFadeFixedLot       = 0.02;           // Enforced Fixed Lot Size for Sweep Fade (0.02 Lot)
input double          SweepMinWickRatio       = 0.35;           // Min Rejection Wick Ratio (>= 35% Pin-bar / Rejection)'''

    new_sweep_in_tester = '''input string          Header_SweepFade        = "=== LIQUIDITY SWEEP FADE (v6.3.4 Beta) ===";
input bool            EnableSweepFadeTrade    = true;           // Enable Auto-Trade on Liquidity Sweep Fade (Default False for Signal Mode)
input bool            EnableSweepFadeSignal   = true;           // Enable Broadcast Grade A+ Alpha Sweep Signal to Discord
input double          SweepFadeFixedLot       = 0.02;           // Enforced Fixed Lot Size for Sweep Fade (0.02 Lot)
input double          SweepMinWickRatio       = 0.35;           // Min Rejection Wick Ratio (>= 35% Pin-bar / Rejection)'''

    if old_sweep_in in c:
        c = c.replace(old_sweep_in, new_sweep_in)
    elif old_sweep_in_tester in c:
        c = c.replace(old_sweep_in_tester, new_sweep_in_tester)

    # Update Sweep Fade order opening to use SweepFadeFixedLot
    old_exec_sell = '''                  if(EnableSweepFadeTrade)
                  {
                     double lot = CalculateLotSize(SweepFadeRiskPercent, slDist);
                     int ticket = OrderSend(Symbol(), OP_SELL, lot, entryPrice, SlippagePoints, sweepSL, sweepTP, "v6.3.4 Sweep Fade SELL", MagicSweepFade, 0, clrRed);'''

    new_exec_sell = '''                  if(EnableSweepFadeTrade)
                  {
                     double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
                     double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
                     double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
                     if(lotStep <= 0) lotStep = 0.01;
                     double lot = MathFloor(SweepFadeFixedLot / lotStep) * lotStep;
                     if(lot < minLot) lot = minLot;
                     if(lot > maxLot) lot = maxLot;
                     int ticket = OrderSend(Symbol(), OP_SELL, lot, entryPrice, SlippagePoints, sweepSL, sweepTP, "v6.3.4 Sweep Fade SELL", MagicSweepFade, 0, clrRed);'''

    old_exec_buy = '''                  if(EnableSweepFadeTrade)
                  {
                     double lot = CalculateLotSize(SweepFadeRiskPercent, slDist);
                     int ticket = OrderSend(Symbol(), OP_BUY, lot, entryPrice, SlippagePoints, sweepSL, sweepTP, "v6.3.4 Sweep Fade BUY", MagicSweepFade, 0, clrGreen);'''

    new_exec_buy = '''                  if(EnableSweepFadeTrade)
                  {
                     double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
                     double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
                     double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
                     if(lotStep <= 0) lotStep = 0.01;
                     double lot = MathFloor(SweepFadeFixedLot / lotStep) * lotStep;
                     if(lot < minLot) lot = minLot;
                     if(lot > maxLot) lot = maxLot;
                     int ticket = OrderSend(Symbol(), OP_BUY, lot, entryPrice, SlippagePoints, sweepSL, sweepTP, "v6.3.4 Sweep Fade BUY", MagicSweepFade, 0, clrGreen);'''

    if old_exec_sell in c:
        c = c.replace(old_exec_sell, new_exec_sell)
    if old_exec_buy in c:
        c = c.replace(old_exec_buy, new_exec_buy)

    # Update OnInit banner line
    old_banner_lot = '''   Print(" Lot Sizing: ", (UseFixedLot ? ("ENFORCED FIXED LOT = " + DoubleToString(FixedLotSize, 2) + " (All Engines)") : "DYNAMIC RISK %"));
   Print(" Liquidity Sweep Fade: ", EnableSweepFadeTrade ? "AUTO-TRADE ACTIVE" : "SIGNAL FEED ONLY", " | Target RR 1:", SweepRR_Multiplier, " | Min Wick: ", DoubleToString(SweepMinWickRatio*100, 0), "%");'''

    new_banner_lot = '''   Print(" Liquidity Sweep Fade: ", EnableSweepFadeTrade ? "AUTO-TRADE ACTIVE" : "SIGNAL FEED ONLY", " | Enforced Fixed Lot: ", DoubleToString(SweepFadeFixedLot, 2), " | Target RR 1:", SweepRR_Multiplier, " | Min Wick: ", DoubleToString(SweepMinWickRatio*100, 0), "%");'''

    if old_banner_lot in c:
        c = c.replace(old_banner_lot, new_banner_lot)

    with open(fp, "w", encoding="utf-8") as f:
        f.write(c)

    ok = compile_mq4(fp)
    print(f"Updated & Compiled {os.path.basename(fp)}: OK = {ok}")

# ==============================================================================
# 3. DEPLOY ALL BINARIES TO MT4 EXPERTS
# ==============================================================================
for f in ["GoldSniper_Bridge_v6_3_4_beta.ex4", "GoldSniper_Bridge_v6_3_4_beta.mq4",
          "GoldSniper_Tester_v6_3_4_beta.ex4", "GoldSniper_Tester_v6_3_4_beta.mq4",
          "GoldSniper_Bridge_v6_3_3.ex4", "GoldSniper_Bridge_v6_3_3.mq4",
          "GoldSniper_Tester_v6_3_3.ex4", "GoldSniper_Tester_v6_3_3.mq4"]:
    src = os.path.join(base_dir, f)
    dst = os.path.join(mt4_experts, f)
    shutil.copy2(src, dst)
    print(f"Deployed -> {f}")

print("\nAll files successfully updated and deployed to MT4!")
