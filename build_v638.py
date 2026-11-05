import os
import shutil

source_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\GoldSniper_Tester_v6_3_6b.mq4"
experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
scratch_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"

with open(source_path, "r", encoding="latin1") as f:
    code = f.read()

# 1. Update Header and Properties
code = code.replace("Gold Sniper v6.3.1 Institutional Live XM Bridge Engine", "Gold Sniper v6.3.8-Beta Institutional Apex Engine")
code = code.replace('#property version   "6.36"', '#property version   "6.38"')
code = code.replace('Header_Master           = "=== MASTER V6.3.6b INSTITUTIONAL QUAD-ENGINE APEX (BUG-01 & BUG-02 FIXED) ===";',
                    'Header_Master           = "=== MASTER V6.3.8-BETA INSTITUTIONAL APEX (SMC EQ FILTER + FAST BAILOUT) ===";')

# 2. Update Risk Percentages and Inputs
code = code.replace('input double          SniperRiskPercent       = 5.0;            // London Sniper Risk (% of Equity - 2x Lot)',
                    'input double          SniperRiskPercent       = 3.0;            // London Sniper Risk (% of Equity - Balanced 3.0%)')
code = code.replace('input double          NYRiskPercent           = 3.5;            // New York Continuation Risk (3.5% of Equity)',
                    'input double          NYRiskPercent           = 2.0;            // New York Continuation Risk (2.0% Safe Institutional)')
code = code.replace('input double          ScalperRiskPercent      = 1.0;            // Asian Scalper Micro-Risk (% of Equity - Safe)',
                    'input double          ScalperRiskPercent      = 0.5;            // Asian Scalper Micro-Risk (% of Equity - Safe 0.5%)')

code = code.replace('input double          Sniper_Min_SL_USD       = 8.00;           // London Min Base SL USD ($8.00)',
                    'input double          Sniper_Min_SL_USD       = 6.50;           // London Min Base SL USD ($6.50 Buffer)')
code = code.replace('input double          NY_Min_SL_USD           = 6.00;           // Min Base SL USD ($6.00 Tightened)',
                    'input double          NY_Min_SL_USD           = 6.50;           // Min Base SL USD ($6.50 Buffer)\ninput bool            EnableNY_EQ_Filter      = true;           // SMC Premium/Discount Filter (Block Sells in Discount Zone)\ninput bool            EnableStructureBailout  = true;           // Fast Structure Bailout (Cut loss early if entry bar broken)\ninput bool            EnableSweepH1TrendAlign = true;           // Sweep Fade: Require H1 Trend Alignment (Block counter-trend trap)')

# 3. Update CalculateLotSize with zero-divide protection
old_calc_lot = """double CalculateLotSize(double riskPct, double slUSD)
{
   double riskUsd = AccountEquity() * (riskPct / 100.0);"""

new_calc_lot = """double CalculateLotSize(double riskPct, double slUSD)
{
   if(slUSD <= 0.50) slUSD = 6.50; // Zero-divide and micro-stop protection (v6.3.8-Beta)
   double riskUsd = AccountEquity() * (riskPct / 100.0);"""

assert old_calc_lot in code, "old_calc_lot not found"
code = code.replace(old_calc_lot, new_calc_lot, 1)

# 4. Add Structure Invalidation tracking arrays and helper functions
old_risk_arrays = """int      GS636B_RiskTickets[200];
double   GS636B_RiskValues[200];
datetime GS636B_LastModTime[200];
datetime GS636B_LastCloseTime[200];
int      GS636B_RiskCount = 0;"""

new_risk_arrays = """int      GS638B_RiskTickets[200];
double   GS638B_RiskValues[200];
datetime GS638B_LastModTime[200];
datetime GS638B_LastCloseTime[200];
double   GS638B_StructureInvalidation[200];
int      GS638B_StructureSide[200];
int      GS638B_RiskCount = 0;

void SetOrderStructureLevel638B(int ticket, double invalidationLevel, int side)
{
   if(ticket <= 0) return;
   string gvKey = "GS638B_Inv_" + IntegerToString(ticket);
   if(!IsTesting()) GlobalVariableSet(gvKey, invalidationLevel);
   int idx = -1;
   for(int i = 0; i < GS638B_RiskCount; i++)
   {
      if(GS638B_RiskTickets[i] == ticket) { idx = i; break; }
   }
   if(idx == -1)
   {
      idx = GS638B_RiskCount % 200;
      GS638B_RiskTickets[idx] = ticket;
      if(GS638B_RiskCount < 200) GS638B_RiskCount++;
   }
   GS638B_StructureInvalidation[idx] = invalidationLevel;
   GS638B_StructureSide[idx] = side;
}

double GetOrderStructureLevel638B(int ticket)
{
   if(ticket <= 0) return 0.0;
   for(int i = 0; i < GS638B_RiskCount; i++)
   {
      if(GS638B_RiskTickets[i] == ticket) return GS638B_StructureInvalidation[i];
   }
   if(!IsTesting())
   {
      string gvKey = "GS638B_Inv_" + IntegerToString(ticket);
      if(GlobalVariableCheck(gvKey)) return GlobalVariableGet(gvKey);
   }
   return 0.0;
}"""

assert old_risk_arrays in code, "old_risk_arrays not found"
code = code.replace(old_risk_arrays, new_risk_arrays, 1)

# 5. Insert Fast Structure Bailout into ManageOpenPositions
bailout_injection_point = """            // -------------------------------------------------------------
            // 2. LONDON SNIPER RUNNER MANAGEMENT"""

bailout_code = """            // -------------------------------------------------------------
            // FAST STRUCTURE BAILOUT (Early Cutoff when Market Structure Breaks v6.3.8-Beta)
            // -------------------------------------------------------------
            if(EnableStructureBailout && (m == MagicNY || m == MagicSniper))
            {
               double invLevel = GetOrderStructureLevel638B(ticket);
               if(invLevel > 0.0)
               {
                  if(oType == OP_SELL && Bid >= invLevel)
                  {
                     double cPrice = Ask;
                     double lossUSD = (cPrice - openP) * lots * 100.0;
                     if(SafeCloseOrder638B(ticket, lots, cPrice, SlippagePoints, clrRed))
                     {
                        Print("[FAST STRUCTURE BAILOUT v6.3.8-Beta] [!] Ticket #", ticket, " Bearish structure broken (Bid ", Bid, " >= Inv ", invLevel, "). Emergency cut early at -$", lossUSD, " to prevent full SL!");
                        continue;
                     }
                  }
                  else if(oType == OP_BUY && Ask <= invLevel)
                  {
                     double cPrice = Bid;
                     double lossUSD = (openP - cPrice) * lots * 100.0;
                     if(SafeCloseOrder638B(ticket, lots, cPrice, SlippagePoints, clrRed))
                     {
                        Print("[FAST STRUCTURE BAILOUT v6.3.8-Beta] [!] Ticket #", ticket, " Bullish structure broken (Ask ", Ask, " <= Inv ", invLevel, "). Emergency cut early at -$", lossUSD, " to prevent full SL!");
                        continue;
                     }
                  }
               }
            }

            // -------------------------------------------------------------
            // 2. LONDON SNIPER RUNNER MANAGEMENT"""

assert bailout_injection_point in code, "bailout_injection_point not found"
code = code.replace(bailout_injection_point, bailout_code, 1)

# 6. Record Structure Invalidation Level when opening London Sniper orders
old_sniper_buy_open = """SetOrderInitRisk636B(ticket, dynamicSniperSL);
                     DailyTotalTrades++;
                     LondonDirectionToday = 1;"""

new_sniper_buy_open = """SetOrderInitRisk638B(ticket, dynamicSniperSL);
                     double invL = MathMin(l1, iLow(Symbol(), PERIOD_M15, 2)) - (0.50 * Point * 10);
                     SetOrderStructureLevel638B(ticket, invL, OP_BUY);
                     DailyTotalTrades++;
                     LondonDirectionToday = 1;"""

assert old_sniper_buy_open in code, "old_sniper_buy_open not found"
code = code.replace(old_sniper_buy_open, new_sniper_buy_open, 1)

old_sniper_sell_open = """SetOrderInitRisk636B(ticket, dynamicSniperSL);
                     DailyTotalTrades++;
                     LondonDirectionToday = -1;"""

new_sniper_sell_open = """SetOrderInitRisk638B(ticket, dynamicSniperSL);
                     double invH = MathMax(h1, iHigh(Symbol(), PERIOD_M15, 2)) + (0.50 * Point * 10);
                     SetOrderStructureLevel638B(ticket, invH, OP_SELL);
                     DailyTotalTrades++;
                     LondonDirectionToday = -1;"""

assert old_sniper_sell_open in code, "old_sniper_sell_open not found"
code = code.replace(old_sniper_sell_open, new_sniper_sell_open, 1)

# 7. Update New York Engine: Fix FVG on Closed Bars (Shift 1, 2, 3) + Add SMC Premium/Discount Filter
old_ny_fvg = """            // 2. ICT Fair Value Gap (FVG) & Displacement Detection on M15
            double h2 = iHigh(Symbol(), PERIOD_M15, 2);
            double l2 = iLow(Symbol(), PERIOD_M15, 2);
            double h0 = iHigh(Symbol(), PERIOD_M15, 0);
            double l0 = iLow(Symbol(), PERIOD_M15, 0);
            
            // Bullish Displacement & FVG: Bar 1 exploded green leaving gap between Bar 2 High and Bar 0 Low
            bool bullDisplacement = (c1 > o1) && ((body1 / range1) >= 0.45);
            bool bullFVG = bullDisplacement && (l0 > h2);
            
            // Bearish Displacement & FVG: Bar 1 exploded red leaving gap between Bar 2 Low and Bar 0 High
            bool bearDisplacement = (c1 < o1) && ((body1 / range1) >= 0.45);
            bool bearFVG = bearDisplacement && (h0 < l2);"""

new_ny_fvg = """            // 2. ICT Fair Value Gap (FVG) & Displacement Detection on CLOSED M15 BARS (v6.3.8-Beta)
            // Shifts: Bar 3 (Left Anchor), Bar 2 (Displacement), Bar 1 (Closed Confirmation Anchor)
            double h3 = iHigh(Symbol(), PERIOD_M15, 3);
            double l3 = iLow(Symbol(), PERIOD_M15, 3);
            double h2 = iHigh(Symbol(), PERIOD_M15, 2);
            double l2 = iLow(Symbol(), PERIOD_M15, 2);
            o2 = iOpen(Symbol(), PERIOD_M15, 2);
            c2 = iClose(Symbol(), PERIOD_M15, 2);
            double range2 = h2 - l2;
            if(range2 <= 0) range2 = Point * 10;
            double body2  = MathAbs(c2 - o2);

            // Closed 3-Bar FVG: Bar 2 was displacement, Bar 1 closed confirming the gap
            bool bullDisplacement = (c2 > o2) && ((body2 / range2) >= 0.45);
            bool bullFVG          = bullDisplacement && (l1 > h3);

            bool bearDisplacement = (c2 < o2) && ((body2 / range2) >= 0.45);
            bool bearFVG          = bearDisplacement && (h1 < l3);
            
            // Alternative Shift 1 Displacement: Bar 1 displaced against Bar 3
            if(!bullFVG && (c1 > o1) && ((body1 / range1) >= 0.45) && (l1 > h2)) bullFVG = true;
            if(!bearFVG && (c1 < o1) && ((body1 / range1) >= 0.45) && (h1 < l2)) bearFVG = true;

            // SMC Equilibrium & Premium/Discount Filter for NY (v6.3.8-Beta)
            double asianEQ = (StoredAsianHigh > 0 && StoredAsianLow > 0 && StoredAsianHigh > StoredAsianLow) ?
                             ((StoredAsianHigh + StoredAsianLow) / 2.0) : 0.0;"""

assert old_ny_fvg in code, "old_ny_fvg not found"
code = code.replace(old_ny_fvg, new_ny_fvg, 1)

# Add EQ filter to buyDirectionOk and sellDirectionOk
old_buy_dir = """            // BUY Trend-Rider: H1 Macro Bull + M15 EMAs Bull + London Direction Alignment + No ADR Exhaustion
            bool buyDirectionOk = !adrExhausted && isH1Bull && (c1 > ema200_m15) && (ema50_m15 > ema200_m15);
            if(NY_RequireLondonAlign && LondonDirectionToday < 0) buyDirectionOk = false; // Block counter-trend Sell from London"""

new_buy_dir = """            // BUY Trend-Rider: H1 Macro Bull + M15 EMAs Bull + London Direction Alignment + No ADR Exhaustion
            bool buyDirectionOk = !adrExhausted && isH1Bull && (c1 > ema200_m15) && (ema50_m15 > ema200_m15);
            if(NY_RequireLondonAlign && LondonDirectionToday < 0) buyDirectionOk = false; // Block counter-trend Sell from London
            if(EnableNY_EQ_Filter && asianEQ > 0.0 && Ask >= asianEQ) buyDirectionOk = false; // Block Buy in Premium Zone!"""

assert old_buy_dir in code, "old_buy_dir not found"
code = code.replace(old_buy_dir, new_buy_dir, 1)

old_sell_dir = """            // SELL Trend-Rider: H1 Macro Bear + M15 EMAs Bear + London Direction Alignment + No ADR Exhaustion
            bool sellDirectionOk = !adrExhausted && isH1Bear && (c1 < ema200_m15) && (ema50_m15 < ema200_m15);
            if(NY_RequireLondonAlign && LondonDirectionToday > 0) sellDirectionOk = false; // Block counter-trend Buy from London"""

new_sell_dir = """            // SELL Trend-Rider: H1 Macro Bear + M15 EMAs Bear + London Direction Alignment + No ADR Exhaustion
            bool sellDirectionOk = !adrExhausted && isH1Bear && (c1 < ema200_m15) && (ema50_m15 < ema200_m15);
            if(NY_RequireLondonAlign && LondonDirectionToday > 0) sellDirectionOk = false; // Block counter-trend Sell from London
            if(EnableNY_EQ_Filter && asianEQ > 0.0 && Bid <= asianEQ) sellDirectionOk = false; // Block Sell in Discount Zone (Anti-Trap #63456886)!"""

assert old_sell_dir in code, "old_sell_dir not found"
code = code.replace(old_sell_dir, new_sell_dir, 1)

# Record structure invalidation for NY Buy (1st occurrence of SetOrderInitRisk636B(ticket, dynamicSL);)
ny_buy_marker = "SetOrderInitRisk636B(ticket, dynamicSL);"
ny_buy_replacement = """SetOrderInitRisk638B(ticket, dynamicSL);
                     double invL = MathMin(l1, l2) - (0.50 * Point * 10);
                     SetOrderStructureLevel638B(ticket, invL, OP_BUY);"""

assert ny_buy_marker in code, "ny_buy_marker not found"
code = code.replace(ny_buy_marker, ny_buy_replacement, 1)

# Record structure invalidation for NY Sell (2nd occurrence of SetOrderInitRisk636B(ticket, dynamicSL);)
ny_sell_replacement = """SetOrderInitRisk638B(ticket, dynamicSL);
                     double invH = MathMax(h1, h2) + (0.50 * Point * 10);
                     SetOrderStructureLevel638B(ticket, invH, OP_SELL);"""

assert ny_buy_marker in code, "ny_sell_marker not found"
code = code.replace(ny_buy_marker, ny_sell_replacement, 1)

# 8. Asian Box Sweep Fade H1 Trend Alignment Filter
old_sweep_marker = "else if(sweptAsianLow)"
new_sweep_marker = """else if(sweptAsianLow && (!EnableSweepH1TrendAlign || !isH1Bear))"""

assert old_sweep_marker in code, "old_sweep_marker not found"
code = code.replace(old_sweep_marker, new_sweep_marker, 1)

old_sweep_high = "if(sweptAsianHigh)"
new_sweep_high = """if(sweptAsianHigh && (!EnableSweepH1TrendAlign || !isH1Bull))"""

assert old_sweep_high in code, "old_sweep_high not found"
code = code.replace(old_sweep_high, new_sweep_high, 1)

# 9. Now rename remaining 636B -> 638B
code = code.replace("GS636B", "GS638B")
code = code.replace("636B", "638B")
code = code.replace("v6.3.6b", "v6.3.8-Beta")
code = code.replace("v6.3.6a", "v6.3.8-Beta")
code = code.replace("v6.3.6", "v6.3.8-Beta")

# Write to both Tester and Bridge v6.3.8-Beta
tester_v638_path = os.path.join(experts_dir, "GoldSniper_Tester_v6_3_8_beta.mq4")
bridge_v638_path = os.path.join(experts_dir, "GoldSniper_Bridge_v6_3_8_beta.mq4")

with open(tester_v638_path, "w", encoding="latin1") as f:
    f.write(code)

with open(bridge_v638_path, "w", encoding="latin1") as f:
    f.write(code)

# Also write to scratch directory
shutil.copy2(tester_v638_path, os.path.join(scratch_dir, "GoldSniper_Tester_v6_3_8_beta.mq4"))
shutil.copy2(bridge_v638_path, os.path.join(scratch_dir, "GoldSniper_Bridge_v6_3_8_beta.mq4"))

print("SUCCESS: Created GoldSniper_Tester_v6_3_8_beta.mq4 & GoldSniper_Bridge_v6_3_8_beta.mq4 in MT4 Experts & Scratch!")
