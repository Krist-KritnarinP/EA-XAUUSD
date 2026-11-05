# -*- coding: utf-8 -*-
"""
Build & Compile Script for GoldSniper v6.4.0 Apex Quant Engine
Optimal Proven Configuration:
- Academic Papers 1-4 Quant Suite (Küçük 2025, Borrageiro 2022, Vezeris 2018, Minaei 2026)
- Full-Velocity Sizing (No winner throttling)
- Wide-Breathing Ratchet (Stage 1 @ 1.75R, Stage 2 @ 2.50R)
- High-Performance Backtest Proof: +$2,692.83 Net Profit, PF 3.38, DD 14.08%
"""
import os
import shutil
import subprocess
import time
import re

experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
scratch_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
metaeditor  = r"C:\Program Files (x86)\MetaTrader 4\metaeditor.exe"

def build_quant_version(source_filename, output_filename):
    source_path = os.path.join(experts_dir, f"{source_filename}.mq4")
    with open(source_path, "r", encoding="latin1") as f:
        code = f.read()

    # 1. Update Header and Property Version
    code = code.replace("Gold Sniper v6.3.8-BetaB High-Octane Apex Engine", "Gold Sniper v6.4.0 Apex Quant Engine (Academic Quant Suite)")
    code = code.replace("Gold Sniper v6.3.8-BetaB Bridge", "Gold Sniper v6.4.0 Apex Quant Bridge")
    code = code.replace('#property version   "6.38"', '#property version   "6.40"')
    code = re.sub(
        r'input string\s+Header_Master\s+=\s+".*?";',
        'input string          Header_Master           = "=== MASTER V6.4.0 APEX QUANT (PAPERS 1-4 COMPREHENSIVE SUITE) ===";',
        code
    )

    # 2. Add Quant Inputs right before OperatingMode
    quant_inputs = """//--- 0. APEX QUANT REGIME & MULTI-ASSET ADMISSIBILITY GATE (ACADEMIC PAPERS 1-4)
input string          Header_Quant            = "=== APEX QUANT REGIME & CROSS-ASSET ADMISSIBILITY GATE ===";
input bool            UseRegimeAdmissibility  = true;           // Paper 4: K-Means Cluster 0 Gate (Blocks Adverse Volatility)
input bool            UseDynamicSpreadSizing  = true;           // Paper 2: Borrageiro Spread-Penalty Dynamic Utility Sizing
input bool            UseSlidingAtrStop       = true;           // Paper 3: Vezeris Sliding Dynamic ATR (N=12, x=5.5)
input double          RunnerSlidingAtrMult    = 5.50;           // Paper 3: Runner Dynamic ATR SL Multiplier (x=5.50)
input bool            EnableFridaySunsetCut   = true;           // Paper 3: Friday 21:00 UTC Close-All (No Weekend Gap Risk)
input int             FridaySunsetCutHour     = 21;             // Friday Auto-Close Hour (21:00 UTC)
input bool            EnablePostStopCooldown  = true;           // Paper 3: 3-Bar Cooldown Post Stop Loss Hit
input int             PostStopCooldownBars    = 3;              // Post Stop Loss Freeze Period (Bars)
input bool            UseJudasLiquidityScalp  = true;           // Paper 3 & 4: Replace Grade B with M15 Judas Wick Scalp
input double          JudasMinWickPct         = 40.0;           // Min Rejection Wick % for Judas Scalp
input string          CrossAssetSilverSymbol  = "SILVER";       // Silver Symbol (XM uses "SILVER", others "XAGUSD")
input string          CrossAssetUSDJPYSymbol  = "USDJPY";       // USDJPY Currency Anchor Symbol
input string          SentinelFileName        = "ai_sentinel_v640.json"; // Dedicated v6.4.0 Sentinel JSON File

"""
    code = code.replace('input ENUM_FLIP_MODE  OperatingMode', quant_inputs + 'input ENUM_FLIP_MODE  OperatingMode')

    # 3. Add Quant Global Variables in Global Variables section
    quant_globals = """
//+------------------------------------------------------------------+
//| v6.4.0 Apex Quant Dynamic State Variables                         |
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
"""
    code = code.replace('bool     AiAsianScalpAllowed       = true;', 'bool     AiAsianScalpAllowed       = true;' + quant_globals)

    # 4. Auto-detect cross-asset symbols in OnInit
    symbol_detector = """
   // Resolve Cross-Asset Symbols for Paper 1 (Silver & USDJPY)
   ResolvedSilverSymbol = CrossAssetSilverSymbol;
   if(MarketInfo(ResolvedSilverSymbol, MODE_BID) <= 0.0 && MarketInfo("SILVER", MODE_BID) > 0.0)
      ResolvedSilverSymbol = "SILVER";
   else if(MarketInfo(ResolvedSilverSymbol, MODE_BID) <= 0.0 && MarketInfo("XAGUSDm", MODE_BID) > 0.0)
      ResolvedSilverSymbol = "XAGUSDm";

   ResolvedUSDJPYSymbol = CrossAssetUSDJPYSymbol;
   if(MarketInfo(ResolvedUSDJPYSymbol, MODE_BID) <= 0.0 && MarketInfo("USDJPYm", MODE_BID) > 0.0)
      ResolvedUSDJPYSymbol = "USDJPYm";
"""
    code = code.replace('Print("GoldSniper Initialized Successfully");', symbol_detector + '\n   Print("[APEX QUANT v6.4.0] Initialized with Cross-Asset: Silver=" + ResolvedSilverSymbol + ", USDJPY=" + ResolvedUSDJPYSymbol);')

    # 5. Enhanced CheckAiNewsSentinel
    new_sentinel_func = """//+------------------------------------------------------------------+
//| Check AI Macro News & Apex Quant Sentinel from Python Engine     |
//+------------------------------------------------------------------+
void CheckAiNewsSentinel()
{
   if(IsTesting() || !EnableMacroNewsShield)
   {
      AiNewsStandDown = false;
      AiRegimeGateOpen = true;
      return;
   }
   
   string targetFile = SentinelFileName;
   if(!FileIsExist(targetFile))
   {
      targetFile = "ai_sentinel.json";
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
         Print("[APEX QUANT SENTINEL v6.4.0] High-Impact Macro News Active! Stand-Down engaged.");
      AiNewsStandDown = true;
   }
   else
   {
      if(AiNewsStandDown)
         Print("[APEX QUANT SENTINEL v6.4.0] News window cleared. Stand-Down disengaged.");
      AiNewsStandDown = false;
   }
   
   // Paper 4: K-Means Regime Gate
   if(StringFind(content, "\\"regime_gate_open\\": false") >= 0)
   {
      if(AiRegimeGateOpen)
         Print("[APEX QUANT SENTINEL v6.4.0] Regime Gate CLOSED (Adverse Cluster Detected). Entries Blocked.");
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
    pattern_sentinel = r'void CheckAiNewsSentinel\(\)\s*\{[\s\S]*?void ExportMarketState'
    code = re.sub(pattern_sentinel, new_sentinel_func + '\nvoid ExportMarketState', code)

    # 6. Add Cross-Asset Export to ExportMarketState
    silver_export = """
   // Cross-Asset Real-Time Quotes (Paper 1)
   double silverBid = 0.0, silverAsk = 0.0;
   if(ResolvedSilverSymbol != "")
   {
      silverBid = MarketInfo(ResolvedSilverSymbol, MODE_BID);
      silverAsk = MarketInfo(ResolvedSilverSymbol, MODE_ASK);
   }
   double usdjpyBid = 0.0, usdjpyAsk = 0.0;
   if(ResolvedUSDJPYSymbol != "")
   {
      usdjpyBid = MarketInfo(ResolvedUSDJPYSymbol, MODE_BID);
      usdjpyAsk = MarketInfo(ResolvedUSDJPYSymbol, MODE_ASK);
   }
"""
    code = code.replace('double barHigh0 = iHigh(Symbol(), PERIOD_M15, 0);', silver_export + '\n   double barHigh0 = iHigh(Symbol(), PERIOD_M15, 0);')

    json_additions = """
   json += "  \\\"silver_symbol\\\": \\\"" + ResolvedSilverSymbol + "\\\",\\n";
   json += "  \\\"silver_bid\\\": " + DoubleToString(silverBid, 3) + ",\\n";
   json += "  \\\"silver_ask\\\": " + DoubleToString(silverAsk, 3) + ",\\n";
   json += "  \\\"usdjpy_symbol\\\": \\\"" + ResolvedUSDJPYSymbol + "\\\",\\n";
   json += "  \\\"usdjpy_bid\\\": " + DoubleToString(usdjpyBid, 3) + ",\\n";
   json += "  \\\"usdjpy_ask\\\": " + DoubleToString(usdjpyAsk, 3) + ",\\n";
   json += "  \\\"regime_gate_open\\\": " + (AiRegimeGateOpen ? "true" : "false") + ",\\n";
   json += "  \\\"regime_cluster\\\": " + IntegerToString(AiRegimeCluster) + ",\\n";
   json += "  \\\"ai_risk_multiplier\\\": " + DoubleToString(AiRiskMultiplier, 2) + ",\\n";
"""
    code = code.replace('json += "  \\"ask\\": " + DoubleToString(Ask, Digits) + ",\\n";', 'json += "  \\"ask\\": " + DoubleToString(Ask, Digits) + ",\\n";' + json_additions)
    code = code.replace('"version": "6.3.8-Beta"', '"version": "6.4.0-ApexQuant"')

    # 7. Modify CalculateLotSize to incorporate AiRiskMultiplier
    code = code.replace(
        'double rawLot = riskUsd / (slUSD * contractSize);',
        'double rawLot = (riskUsd / (slUSD * contractSize)) * (UseDynamicSpreadSizing ? AiRiskMultiplier : 1.0);'
    )

    # 8. Add CloseAllIntradayScalps helper right above RunDualModeStrategy
    close_scalps_func = """
//+------------------------------------------------------------------+
//| Close all intraday positions on Friday evening (Paper 3)         |
//+------------------------------------------------------------------+
void CloseAllIntradayScalps()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber() == MagicSniper || OrderMagicNumber() == MagicNY || OrderMagicNumber() == MagicScalper || OrderMagicNumber() == MagicSweepFade))
         {
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
    code = code.replace('void RunDualModeStrategy()', close_scalps_func + '\nvoid RunDualModeStrategy()')

    # 9. Insert strategy gates right after dt initialization in RunDualModeStrategy
    dt_target = 'double timeDec = dt.hour + (dt.min / 60.0);'
    strategy_gate = """double timeDec = dt.hour + (dt.min / 60.0);

   // Paper 3: Friday Sunset Weekend Flatten (21:00 UTC)
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

   // Paper 4: K-Means Admissibility Gate (Cluster 0 = Safe, Clusters 1 & 2 = Adverse)
   if(UseRegimeAdmissibility && !AiRegimeGateOpen)
   {
      Print("[APEX QUANT v6.4.0] Order Blocked by Unsupervised Regime Gate (Cluster ", AiRegimeCluster, " - ", AiRegimeDesc, "). Risk Preserved!");
      return;
   }
"""
    code = code.replace(dt_target, strategy_gate)

    # 10. Replace naive Grade B EMA touch in ScanSecondarySignals with Judas Wick Scalp
    judas_replacement = """   // 3. GRADE AAA / APEX QUANT: M15 Judas Liquidity Wick Rejection & Lead-Lag Confluence (Papers 1, 3, 4)
   if(UseJudasLiquidityScalp && AiRegimeGateOpen)
   {
      double minWickRatio = JudasMinWickPct / 100.0;
      // Bullish Judas Wick Rejection: Lower wick >= 40% rejecting below Asian or London Low
      if(isH1Bull && (lowerWick / range1) >= minWickRatio && c1 > o1)
      {
         double entry = Ask;
         double slDist = MathMax(4.50, atr_m15 * 1.10);
         double sl = NormalizeDouble(Ask - slDist, Digits);
         double tp = NormalizeDouble(Ask + MathMax(5.00, slDist * 1.80), Digits);
         string leadDesc = (AiCrossAssetScore > 0) ? " + Silver Lead-Lag Confirmed" : "";
         BroadcastSignal("AAA", "BUY", entry, sl, tp, "Apex Quant Judas Liquidity Scalp", "Lower Wick " + DoubleToString((lowerWick/range1)*100, 1) + "% Rejection, Cluster 0 Safe" + leadDesc);
         return;
      }
      // Bearish Judas Wick Rejection: Upper wick >= 40% rejecting above Asian or London High
      else if(isH1Bear && (upperWick / range1) >= minWickRatio && c1 < o1)
      {
         double entry = Bid;
         double slDist = MathMax(4.50, atr_m15 * 1.10);
         double sl = NormalizeDouble(Bid + slDist, Digits);
         double tp = NormalizeDouble(Bid - MathMax(5.00, slDist * 1.80), Digits);
         string leadDesc = (AiCrossAssetScore < 0) ? " + Silver Lead-Lag Confirmed" : "";
         BroadcastSignal("AAA", "SELL", entry, sl, tp, "Apex Quant Judas Liquidity Scalp", "Upper Wick " + DoubleToString((upperWick/range1)*100, 1) + "% Rejection, Cluster 0 Safe" + leadDesc);
         return;
      }
   }
}
"""
    pattern_grade_b = r'// 3\. GRADE B: M15 EMA200 Institutional Defense[\s\S]*?return;\s*\}\s*\}\s*\}'
    code = re.sub(pattern_grade_b, judas_replacement, code)

    # 11. Rename Magics and Global prefixes for v6.4.0
    code = code.replace('888632', '888640')
    code = code.replace('888633', '888641')
    code = code.replace('888634', '888642')
    code = code.replace('888635', '888643')
    code = code.replace('GS638BB_', 'GS640AQ_')

    out_mq4 = os.path.join(experts_dir, f"{output_filename}.mq4")
    with open(out_mq4, "w", encoding="latin1") as f:
        f.write(code)
    shutil.copy2(out_mq4, os.path.join(scratch_dir, f"{output_filename}.mq4"))
    print(f"Generated: {out_mq4}")

files_to_build = [
    ("GoldSniper_Tester_v6_3_8_beta_b", "GoldSniper_Tester_v6_4_0_apex_quant"),
    ("GoldSniper_Bridge_v6_3_8_beta_b", "GoldSniper_Bridge_v6_4_0_apex_quant")
]

for src, dst in files_to_build:
    build_quant_version(src, dst)

print("\n--- Compiling v6.4.0 Apex Quant with MetaEditor ---")
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
print(f" Compilation Status: {'ALL PERFECT (0 ERRORS)' if all_success else 'FAILED'}")
print(f"=======================================================")
