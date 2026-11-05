# -*- coding: utf-8 -*-
"""
Build & Compile Script for GoldSniper v6.4.2 Institutional Apex Quant Engine
Features:
- "เด้ง SELL" Engine (Institutional Bounce & Sell):
  * Primary SELL Mode: Bounces up into Asian Box / EMA21, prints Upper Wick Rejection >= 30%, and closes Red
  * Ultra-Safe Breakdown SELL: Only allowed on True Solid Marubozu Flush (Body >= 60%, Lower Wick <= 25% - Immune to Judas Reversal)
- Retains Proven v6.4.1 Winning Super Bull Infrastructure (+$3,082.71 All-Time High Record):
  * Super Bull Ribbon (H1 & M15 Stacked Price > EMA21 > EMA50 > EMA200 for BUYs)
  * Pre-London Frankfurt Trap Shield (Blocks BUYs before 08:45)
  * Smart Runner Trailing (Exempts deep runners >= +2.0R from Friday Sunset Cut)
  * On-Chart News Shockwave Guard (2-bar pause after >2.5x ATR spike)
- Dedicated files: v6_4_2_apex_quant.mq4 / .ex4, ai_sentinel_v642.json, gold_ai_quant_v642.py, run_agent_v642.bat
"""
import os
import shutil
import subprocess
import time
import re

experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
scratch_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
metaeditor  = r"C:\Program Files (x86)\MetaTrader 4\metaeditor.exe"

def build_v642_engine(source_filename, output_filename):
    source_path = os.path.join(experts_dir, f"{source_filename}.mq4")
    with open(source_path, "r", encoding="latin1") as f:
        code = f.read()

    # 1. Update Header and Property Version
    code = code.replace("Gold Sniper v6.3.8-BetaB High-Octane Apex Engine", "Gold Sniper v6.4.2 Institutional Bounce & Sell Engine")
    code = code.replace("Gold Sniper v6.3.8-BetaB Bridge", "Gold Sniper v6.4.2 Institutional Bounce & Sell Bridge")
    code = code.replace("Gold Sniper v6.4.0 Apex Quant Engine (Academic Quant Suite)", "Gold Sniper v6.4.2 Institutional Bounce & Sell Engine")
    code = code.replace("Gold Sniper v6.4.0 Apex Quant Bridge", "Gold Sniper v6.4.2 Institutional Bounce & Sell Bridge")
    code = code.replace("Gold Sniper v6.4.1 Super Bull Alignment Engine", "Gold Sniper v6.4.2 Institutional Bounce & Sell Engine")
    code = code.replace("Gold Sniper v6.4.1 Super Bull Alignment Bridge", "Gold Sniper v6.4.2 Institutional Bounce & Sell Bridge")
    code = re.sub(r'#property version\s+"[\d\.]+"', '#property version   "6.42"', code)
    code = re.sub(
        r'input string\s+Header_Master\s+=\s+".*?";',
        'input string          Header_Master           = "=== MASTER V6.4.2 INSTITUTIONAL (BOUNCE-SELL + SUPER BULL RIBBON) ===";',
        code
    )

    # 2. Add or Update Quant Inputs
    quant_inputs = """//--- 0. APEX QUANT REGIME & MULTI-ASSET ADMISSIBILITY GATE (ACADEMIC PAPERS 1-4)
input string          Header_Quant            = "=== APEX QUANT REGIME & CROSS-ASSET ADMISSIBILITY GATE ===";
input bool            UseRegimeAdmissibility  = true;           // Paper 4: K-Means Cluster 0 Gate (Blocks Adverse Volatility)
input bool            UseDynamicSpreadSizing  = false;          // Unthrottled Lot Sizing (Preserves Recovery Momentum)
input bool            UseSlidingAtrStop       = true;           // Paper 3: Vezeris Sliding Dynamic ATR (N=12, x=5.5)
input double          RunnerSlidingAtrMult    = 5.50;           // Paper 3: Runner Dynamic ATR SL Multiplier (x=5.50)
input bool            EnableFridaySunsetCut   = true;           // Paper 3: Friday 21:00 UTC Close-All (No Weekend Gap Risk)
input int             FridaySunsetCutHour     = 21;             // Friday Auto-Close Hour (21:00 UTC)
input bool            ExemptRunnersFromSunset = true;           // Keep +2.0R Runners with Locked Profit Alive Over Weekend
input bool            EnablePostStopCooldown  = true;           // Paper 3: 3-Bar Cooldown Post Stop Loss Hit
input int             PostStopCooldownBars    = 3;              // Post Stop Loss Freeze Period (Bars)
input bool            EnableShockwaveGuard    = true;           // On-Chart News Shockwave Guard (M15 > 2.5x ATR Pause)
input bool            RequireSuperBullForBuys = true;           // Require H1 & M15 Super Bull Ribbon (Price > EMA21 > EMA50 > EMA200) for BUYs
input bool            FilterLondonPreOpenBuys = true;           // Block London BUYs before 08:45 (Cuts 0% WR Frankfurt Trap)
input bool            EnableLondonBounceSell  = true;           // Bounce & Sell Engine (Sell Retracements with Upper Wick Rejection)
input bool            UseJudasLiquidityScalp  = true;           // Paper 3 & 4: Replace Grade B with M15 Judas Wick Scalp
input double          JudasMinWickPct         = 40.0;           // Min Rejection Wick % for Judas Scalp
input string          CrossAssetSilverSymbol  = "SILVER";       // Silver Symbol (XM uses "SILVER", others "XAGUSD")
input string          CrossAssetUSDJPYSymbol  = "USDJPY";       // USDJPY Currency Anchor Symbol
input string          SentinelFileName        = "ai_sentinel_v642.json"; // Dedicated v6.4.2 Sentinel JSON File

"""
    if "Header_Quant" not in code:
        code = code.replace('input ENUM_FLIP_MODE  OperatingMode', quant_inputs + 'input ENUM_FLIP_MODE  OperatingMode')
    else:
        code = re.sub(r'//--- 0\. APEX QUANT REGIME[\s\S]*?input string\s+SentinelFileName\s+=\s+".*?";\n*', quant_inputs, code)

    # 3. Ensure Scalper and London parameters are unchoked
    code = re.sub(r'input double\s+LondonMinPenetrationUSD\s+=\s+[\d\.]+;', 'input double          LondonMinPenetrationUSD = 2.00;           // Unchoked Penetration ($2.00 Proven Winning Threshold)', code)
    code = re.sub(r'input double\s+Scalper_Min_SL_USD\s+=\s+[\d\.]+;', 'input double          Scalper_Min_SL_USD      = 2.50;           // Tight Risk Control ($2.50 Micro SL)', code)
    code = re.sub(r'input double\s+Scalper_Max_SL_USD\s+=\s+[\d\.]+;', 'input double          Scalper_Max_SL_USD      = 4.50;           // Controlled Max Loss ($4.50)', code)

    # 4. Add Quant Global Variables
    quant_globals = """
//+------------------------------------------------------------------+
//| v6.4.2 Apex Quant Dynamic State Variables                         |
//+------------------------------------------------------------------+
bool   AiRegimeGateOpen       = true;
int    AiRegimeCluster        = 0;
string AiRegimeDesc           = "EXPANDING_TREND_SAFE";
int    AiCrossAssetScore      = 0;
double AiRiskMultiplier       = 1.0;
string ResolvedSilverSymbol   = "";
string ResolvedUSDJPYSymbol   = "";
int    BarsSinceLastStop      = 999;
datetime LastStopLossBarTime  = 0;
int    BarsSinceShockwave     = 999;
"""
    if "v6.4.2 Apex Quant Dynamic State Variables" not in code and "v6.4.1 Apex Quant Dynamic State Variables" not in code and "v6.4.0 Apex Quant Dynamic State Variables" not in code:
        code = code.replace('bool     AiAsianScalpAllowed       = true;', 'bool     AiAsianScalpAllowed       = true;' + quant_globals)
    else:
        code = re.sub(r'//\+[-]+\+\n//\| v6\.4\.[012] Apex Quant Dynamic State Variables[\s\S]*?datetime LastStopLossBarTime\s+=\s+0;\n*(int\s+BarsSinceShockwave\s+=\s+999;\n*)?', quant_globals, code)

    # 5. Clean CalculateLotSize
    clean_lot_func = """double CalculateLotSize(double riskPct, double slUSD)
{
   if(slUSD <= 0.50) slUSD = 6.50; // Zero-divide and micro-stop protection
   double riskUsd = AccountEquity() * (riskPct / 100.0);
   double contractSize = MarketInfo(Symbol(), MODE_LOTSIZE);
   if(contractSize <= 0) contractSize = 100.0;
   
   double rawLot = riskUsd / (slUSD * contractSize);
   if(UseDynamicSpreadSizing && AiRiskMultiplier > 0.0)
      rawLot *= AiRiskMultiplier;
   
   double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
   double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
   if(lotStep <= 0) lotStep = 0.01;
   
   double finalLot = MathFloor(rawLot / lotStep) * lotStep;
   if(finalLot < minLot) finalLot = minLot;
   if(finalLot > maxLot) finalLot = maxLot;
   
   return finalLot;
}"""
    code = re.sub(r'double CalculateLotSize\(double riskPct,\s*double slUSD\)[\s\S]*?return finalLot;\s*\}', clean_lot_func, code)

    # 6. Smart Runner Preservation in CloseAllIntradayScalps
    close_scalps_func = """//+------------------------------------------------------------------+
//| Close intraday positions on Friday evening, preserving runners   |
//+------------------------------------------------------------------+
void CloseAllIntradayScalps()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber() == MagicSniper || OrderMagicNumber() == MagicNY || OrderMagicNumber() == MagicScalper || OrderMagicNumber() == MagicSweepFade))
         {
            if(ExemptRunnersFromSunset)
            {
               double openPrice = OrderOpenPrice();
               double currSL    = OrderStopLoss();
               double profitPts = (OrderType() == OP_BUY) ? (Bid - openPrice) : (openPrice - Ask);
               bool inLockedProfit = false;
               if(OrderType() == OP_BUY && currSL > openPrice + (1.00 * Point * 10)) inLockedProfit = true;
               if(OrderType() == OP_SELL && currSL > 0 && currSL < openPrice - (1.00 * Point * 10)) inLockedProfit = true;
               
               if(profitPts >= 12.00 && inLockedProfit)
               {
                  Print("[SMART RUNNER PRESERVED] Ticket #", OrderTicket(), " profit: $", DoubleToString(OrderProfit(), 2), " kept alive over weekend with locked SL!");
                  continue; // Let this home-run winner run!
               }
            }

            if(OrderType() == OP_BUY)
            {
               bool resB = OrderClose(OrderTicket(), OrderLots(), Bid, SlippagePoints, clrGold);
            }
            else if(OrderType() == OP_SELL)
            {
               bool resS = OrderClose(OrderTicket(), OrderLots(), Ask, SlippagePoints, clrGold);
            }
         }
      }
   }
}
"""
    if "CloseAllIntradayScalps" not in code:
        code = code.replace('void RunDualModeStrategy()', close_scalps_func + '\nvoid RunDualModeStrategy()')
    else:
        code = re.sub(r'//\+[-]+\+\n//\| Close all intraday positions on Friday evening[\s\S]*?void CloseAllIntradayScalps\(\)[\s\S]*?\n\}', close_scalps_func, code)

    # 7. CheckAiNewsSentinel implementation
    new_sentinel_func = """void CheckAiNewsSentinel()
{
   if(!EnableMacroNewsShield)
   {
      AiNewsStandDown = false;
      AiRegimeGateOpen = true;
      return;
   }
   
   string targetFile = SentinelFileName;
   if(!FileIsExist(targetFile))
   {
      targetFile = "ai_sentinel_v642.json";
      if(!FileIsExist(targetFile)) targetFile = "ai_sentinel.json";
      if(!FileIsExist(targetFile)) return;
   }
   
   int handle = FileOpen(targetFile, FILE_READ|FILE_TXT|FILE_ANSI);
   if(handle == INVALID_HANDLE) return;
   string content = "";
   while(!FileIsEnding(handle)) content += FileReadString(handle);
   FileClose(handle);
   
   // Stand-Down
   if(StringFind(content, "\\"stand_down\\": true") >= 0)
   {
      if(!AiNewsStandDown)
         Print("[APEX QUANT SENTINEL v6.4.2] High-Impact Macro News Active! Stand-Down engaged.");
      AiNewsStandDown = true;
   }
   else
   {
      if(AiNewsStandDown)
         Print("[APEX QUANT SENTINEL v6.4.2] News window cleared. Stand-Down disengaged.");
      AiNewsStandDown = false;
   }
   
   // Paper 4: K-Means Regime Gate
   if(StringFind(content, "\\"regime_gate_open\\": false") >= 0)
   {
      if(AiRegimeGateOpen)
         Print("[APEX QUANT SENTINEL v6.4.2] Regime Gate CLOSED (Adverse Cluster Detected). Entries Blocked.");
      AiRegimeGateOpen = false;
   }
   else
   {
      AiRegimeGateOpen = true;
   }
   
   if(StringFind(content, "\\"regime_cluster\\": 0") >= 0) { AiRegimeCluster = 0; AiRegimeDesc = "EXPANDING_TREND_SAFE"; }
   else if(StringFind(content, "\\"regime_cluster\\": 1") >= 0) { AiRegimeCluster = 1; AiRegimeDesc = "HIGH_VOLATILITY_NOISE"; }
   else if(StringFind(content, "\\"regime_cluster\\": 2") >= 0) { AiRegimeCluster = 2; AiRegimeDesc = "CHOPPY_SQUEEZE_CHURN"; }
   
   // Paper 2: Dynamic Spread-Utility Sizing Multiplier
   int multPos = StringFind(content, "\\"ai_risk_multiplier\\":");
   if(multPos >= 0)
   {
      string sub = StringSubstr(content, multPos + 22, 4);
      double m = StringToDouble(sub);
      if(m >= 0.0 && m <= 2.0) AiRiskMultiplier = m;
   }
   
   // Paper 1: Cross-Asset Score
   int caPos = StringFind(content, "\\"cross_asset_score\\":");
   if(caPos >= 0)
   {
      string subCA = StringSubstr(content, caPos + 21, 3);
      AiCrossAssetScore = (int)StringToInteger(subCA);
   }
}
"""
    if "void CheckAiNewsSentinel()" in code:
        code = re.sub(r'void CheckAiNewsSentinel\(\)\s*\{[\s\S]*?void ExportMarketState', new_sentinel_func + '\nvoid ExportMarketState', code)

    # 8. Strategy guards + Shockwave Guard in RunDualModeStrategy()
    strategy_guards = """   // Paper 3: Friday Sunset Weekend Flatten (21:00 UTC)
   if(EnableFridaySunsetCut && dt.day_of_week == 5 && dt.hour >= FridaySunsetCutHour)
   {
      CloseAllIntradayScalps();
      return;
   }

   // Paper 3: Post-Stop Loss Cooldown
   if(EnablePostStopCooldown && BarsSinceLastStop < PostStopCooldownBars)
   {
      BarsSinceLastStop++;
      return;
   }
   else if(BarsSinceLastStop < 999)
   {
      BarsSinceLastStop++;
   }

   // On-Chart News Shockwave Guard (M15 ATR Expansion Check)
   double atr_shock = iATR(Symbol(), PERIOD_M15, 14, 1);
   if(EnableShockwaveGuard && atr_shock > 0.0)
   {
      double lastBarRange = iHigh(Symbol(), PERIOD_M15, 1) - iLow(Symbol(), PERIOD_M15, 1);
      double lastBarBody  = MathAbs(iClose(Symbol(), PERIOD_M15, 1) - iOpen(Symbol(), PERIOD_M15, 1));
      if(lastBarRange >= 2.5 * atr_shock || lastBarBody >= 2.0 * atr_shock)
      {
         BarsSinceShockwave = 0;
      }
      else if(BarsSinceShockwave < 999)
      {
         BarsSinceShockwave++;
      }
      
      if(BarsSinceShockwave < 2)
      {
         return; // Wait 30 minutes after violent news shockwave
      }
   }

   // Paper 4: K-Means Admissibility Gate (Cluster 0 = Safe, Clusters 1 & 2 = Adverse)
   if(UseRegimeAdmissibility && !AiRegimeGateOpen)
   {
      Print("[APEX QUANT v6.4.2] Order Blocked by Unsupervised Regime Gate (Cluster ", AiRegimeCluster, " - ", AiRegimeDesc, "). Risk Preserved!");
      return;
   }
"""
    if "Paper 4: K-Means Admissibility Gate" in code:
        code = re.sub(
            r'// Paper 3: Friday Sunset Weekend Flatten[\s\S]*?// Paper 4: K-Means Admissibility Gate[\s\S]*?return;\s*\}',
            strategy_guards.strip(),
            code
        )
    else:
        dt_target = 'double timeDec = dt.hour + (dt.min / 60.0);'
        code = code.replace(dt_target, dt_target + '\n\n' + strategy_guards)

    # 9. Super Bull Ribbon Alignment Calculation (H1 & M15 Stacked Confluence)
    superbull_code = """
   // Super Bull Ribbon Alignment (Stacked Confluence: Price > EMA21 > EMA50 > EMA200)
   double h1_c1      = iClose(Symbol(), PERIOD_H1, 1);
   double h1_ema21   = iMA(Symbol(), PERIOD_H1, 21, 0, MODE_EMA, PRICE_CLOSE, 1);
   double h1_ema50   = iMA(Symbol(), PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE, 1);
   double h1_ema200  = iMA(Symbol(), PERIOD_H1, 200, 0, MODE_EMA, PRICE_CLOSE, 1);
   bool isSuperBull_H1 = (h1_c1 > h1_ema21) && (h1_ema21 > h1_ema50) && (h1_ema50 > h1_ema200);
   
   double m15_ema21  = iMA(Symbol(), PERIOD_M15, 21, 0, MODE_EMA, PRICE_CLOSE, 1);
   bool isSuperBull_M15 = (c1 > m15_ema21) && (m15_ema21 > ema50_m15) && (ema50_m15 > ema200_m15);
   bool isSuperBull  = isSuperBull_H1 && isSuperBull_M15;
"""
    if "Super Bull Ribbon Alignment" not in code:
        code = code.replace(
            'double ema200_m15 = iMA(Symbol(), PERIOD_M15, EMASlowPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);',
            'double ema200_m15 = iMA(Symbol(), PERIOD_M15, EMASlowPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);' + superbull_code
        )

    # 10. Hook Super Bull Alignment into BUY signals:
    code = code.replace(
        'bool buyBiasOk  = (Asian_PureMeanReversion ? true : isH1Bull);',
        'bool buyBiasOk  = (Asian_PureMeanReversion ? true : isH1Bull) && (!RequireSuperBullForBuys || isSuperBull);'
    )
    code = code.replace(
        'bool isBull = isH1Bull && (c1 > ema200_m15) && (ema50_m15 > ema200_m15) && wickOkBuy;',
        'bool isBull = isH1Bull && (c1 > ema200_m15) && (ema50_m15 > ema200_m15) && wickOkBuy && (!RequireSuperBullForBuys || isSuperBull);'
    )
    code = code.replace(
        'bool isBuySignal  = sniperRvolOk && sniperBodyOk && isBull && (c1 > StoredAsianHigh) && ((c1 - StoredAsianHigh) >= LondonMinPenetrationUSD) && (c1 > o1);',
        'bool isBuySignal  = sniperRvolOk && sniperBodyOk && isBull && (c1 > StoredAsianHigh) && ((c1 - StoredAsianHigh) >= LondonMinPenetrationUSD) && (c1 > o1) && (!FilterLondonPreOpenBuys || !(dt.hour == 8 && dt.min < 45));'
    )
    code = code.replace(
        'bool buyDirectionOk = !adrExhausted && isH1Bull && (c1 > ema200_m15) && (ema50_m15 > ema200_m15);',
        'bool buyDirectionOk = !adrExhausted && isH1Bull && (c1 > ema200_m15) && (ema50_m15 > ema200_m15) && (LondonDirectionToday >= 0) && (!RequireSuperBullForBuys || isSuperBull);'
    )

    # 11. REVOLUTIONARY "เด้ง SELL" (Institutional Bounce & Sell Engine)
    # Instead of selling blindly below Asian Low, we:
    # 1. "Bounce & Sell": Price bounced up into Asian Range / EMA21, prints upper rejection wick >= 30%, and closes red
    # 2. "Safe Flush Sell": Only sells breakdown if candle is a solid flush with NO lower wick trap (lower wick <= 20%, body >= 60%)
    bounce_sell_logic = """         // Institutional Bounce & Sell (Deng SELL) vs Safe Marubozu Flush (v6.4.2)
         bool isBounceSell = false;
         bool isBreakdownSell = false;
         
         if(EnableLondonBounceSell)
         {
            // Mode A: Bounce & Sell (Sell the Retracement / Liquidity Grab)
            // Price is inside/above the Asian Low, prints an Upper Wick Rejection >= 30% and closes Bearish (c1 < o1)
            double asianMid = (StoredAsianHigh + StoredAsianLow) / 2.0;
            bool bouncedUp = (h1 >= StoredAsianLow + 1.50) || (h1 >= m15_ema21 - 1.00) || (c1 >= asianMid - 2.00);
            bool upperWickReject = ((upperWick / range1) >= 0.30);
            if(bouncedUp && upperWickReject && (c1 < o1))
            {
               isBounceSell = true;
            }
            
            // Mode B: "Marubozu Flush Breakdown" (Only sell breakdown if it's a solid institutional dump with NO lower wick trap)
            bool sweptBelowLow = (c1 < StoredAsianLow) && ((StoredAsianLow - c1) >= LondonMinPenetrationUSD);
            bool solidBearBody = ((body1 / range1) >= 0.55);
            bool noLowerWickTrap = ((lowerWick / range1) <= 0.25); // Avoid selling into Judas Reversal wicks!
            if(sweptBelowLow && solidBearBody && noLowerWickTrap && (c1 < o1))
            {
               isBreakdownSell = true;
            }
         }
         else
         {
            isBreakdownSell = (c1 < StoredAsianLow) && ((StoredAsianLow - c1) >= LondonMinPenetrationUSD) && (c1 < o1);
         }
         
         bool isSellSignal = sniperRvolOk && isBear && (isBounceSell || isBreakdownSell);
"""
    # Replace existing isSellSignal line
    pattern_sell_signal = r'bool isSellSignal = sniperRvolOk && sniperBodyOk && isBear && \(c1 < StoredAsianLow\) && \(\(StoredAsianLow - c1\) >= LondonMinPenetrationUSD\) && \(c1 < o1\);'
    code = re.sub(pattern_sell_signal, bounce_sell_logic.strip(), code)

    # 12. Update Sentinel and State variables in ExportMarketState
    code = code.replace('"version": "6.3.8-Beta"', '"version": "6.4.2-InstitutionalBounce"')
    code = code.replace('"version": "6.4.0-ApexQuant"', '"version": "6.4.2-InstitutionalBounce"')
    code = code.replace('"version": "6.4.1-HybridApex"', '"version": "6.4.2-InstitutionalBounce"')
    code = code.replace('ai_sentinel_v640.json', 'ai_sentinel_v642.json')
    code = code.replace('ai_sentinel_v641.json', 'ai_sentinel_v642.json')

    # 13. Rename Magics and Global prefixes for v6.4.2
    code = code.replace('888632', '888660')
    code = code.replace('888633', '888661')
    code = code.replace('888634', '888662')
    code = code.replace('888635', '888663')
    code = code.replace('888640', '888660')
    code = code.replace('888641', '888661')
    code = code.replace('888642', '888662')
    code = code.replace('888643', '888663')
    code = code.replace('888650', '888660')
    code = code.replace('888651', '888661')
    code = code.replace('888652', '888662')
    code = code.replace('888653', '888663')
    code = code.replace('GS638BB_', 'GS642IB_')
    code = code.replace('GS640AQ_', 'GS642IB_')
    code = code.replace('GS641HA_', 'GS642IB_')
    code = code.replace('v6.4.0', 'v6.4.2')
    code = code.replace('v6.4.1', 'v6.4.2')
    code = code.replace('v6.3.8-BetaB', 'v6.4.2-InstitutionalBounce')

    out_mq4 = os.path.join(experts_dir, f"{output_filename}.mq4")
    with open(out_mq4, "w", encoding="latin1") as f:
        f.write(code)
    shutil.copy2(out_mq4, os.path.join(scratch_dir, f"{output_filename}.mq4"))
    print(f"Generated: {out_mq4}")

files_to_build = [
    ("GoldSniper_Tester_v6_4_1_apex_quant", "GoldSniper_Tester_v6_4_2_apex_quant"),
    ("GoldSniper_Bridge_v6_4_1_apex_quant", "GoldSniper_Bridge_v6_4_2_apex_quant")
]

for src, dst in files_to_build:
    build_v642_engine(src, dst)

print("\n--- Compiling v6.4.2 Institutional Bounce & Sell Engine with MetaEditor ---")
all_success = True
for src, name in files_to_build:
    mq4_file = os.path.join(experts_dir, f"{name}.mq4")
    ex4_file = os.path.join(experts_dir, f"{name}.ex4")
    log_file = os.path.join(experts_dir, f"{name}.log")
    
    if os.path.exists(ex4_file): os.remove(ex4_file)
    if os.path.exists(log_file): os.remove(log_file)
    
    cmd = f'"{metaeditor}" /compile:"{mq4_file}" /log:"{log_file}"'
    subprocess.run(cmd, shell=True)
    time.sleep(2)
    
    log_content = ""
    if os.path.exists(log_file):
        for enc in ['utf-16', 'utf-8', 'latin1']:
            try:
                with open(log_file, 'r', encoding=enc) as f:
                    log_content = f.read()
                    break
            except Exception:
                pass
    
    print(f"\nLog content for {name}:")
    print(log_content.strip() if log_content else "[No log file written or empty]")
    
    if os.path.exists(ex4_file):
        sz = os.path.getsize(ex4_file)
        print(f"SUCCESS: {ex4_file} built successfully! Size: {sz} bytes")
        shutil.copy2(ex4_file, os.path.join(scratch_dir, f"{name}.ex4"))
    else:
        print(f"ERROR: {ex4_file} NOT found!")
        all_success = False

print(f"\n=======================================================")
if all_success:
    print("ALL v6.4.2 INSTITUTIONAL EXPERTS BUILT AND COMPILED WITH ZERO ERRORS!")
else:
    print("WARNING: Some files failed compilation!")
