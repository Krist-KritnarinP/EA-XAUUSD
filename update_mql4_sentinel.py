import os

mql4_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v3_5.mq4"
with open(mql4_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Inputs & Globals
target_input = "extern int      InpEMASlowPeriod        = 200;    // Trend Slow EMA\n"
repl_input = """extern int      InpEMASlowPeriod        = 200;    // Trend Slow EMA

//--- 7. AI SENTINEL BRIDGE ---
extern string   SEP_AI_SENTINEL         = "=== AI SENTINEL & NEWS GUARD BRIDGE ===";
extern bool     InpEnableMacroNewsShield = true;   // Stand-Down during High-Impact News / Macro Events
extern bool     InpEnableStreakBreaker   = true;   // Auto-scale risk via AI Streak Breaker multiplier

bool     g_ai_stand_down = false;
double   g_ai_risk_multiplier = 1.0;
datetime g_last_sentinel_read = 0;
"""

# 2. Forward Declarations
target_fwd = "void UpdatePOIs();\n"
repl_fwd = "void ReadAISentinel();\nvoid UpdatePOIs();\n"

# 3. ReadAISentinel implementation
read_ai_func = """//+------------------------------------------------------------------+
//| Read AI Sentinel State (Macro News Stand-Down & Risk Multiplier) |
//+------------------------------------------------------------------+
void ReadAISentinel()
{
   if(IsTesting()) return;
   static datetime lastRead = 0;
   if(TimeCurrent() == lastRead) return;
   lastRead = TimeCurrent();
   
   string targetFile = "ai_sentinel_poi.json";
   if(!FileIsExist(targetFile)) targetFile = "ai_sentinel.json";
   if(!FileIsExist(targetFile)) return;
   
   int handle = FileOpen(targetFile, FILE_READ|FILE_TXT|FILE_ANSI);
   if(handle == INVALID_HANDLE) return;
   string content = "";
   while(!FileIsEnding(handle)) content += FileReadString(handle);
   FileClose(handle);
   
   if(StringLen(content) < 10) return;
   
   // 1. Parse News Stand-Down
   if(StringFind(content, "\"stand_down\": true") >= 0)
   {
      if(!g_ai_stand_down)
         Print("[AI SENTINEL v3.5] High-Impact Macro News / Geopolitical Shock active! Stand-Down engaged.");
      g_ai_stand_down = true;
   }
   else
   {
      if(g_ai_stand_down)
         Print("[AI SENTINEL v3.5] News Stand-Down cleared. Normal trading resumed.");
      g_ai_stand_down = false;
   }
   
   // 2. Parse AI Risk Multiplier
   int pos = StringFind(content, "\"ai_risk_multiplier\":");
   if(pos >= 0)
   {
      int start = pos + 21;
      string numStr = "";
      for(int i = start; i < start + 10 && i < StringLen(content); i++)
      {
         ushort ch = StringGetCharacter(content, i);
         if((ch >= '0' && ch <= '9') || ch == '.')
            numStr += CharToString((uchar)ch);
         else if(StringLen(numStr) > 0)
            break;
      }
      double parsedMult = StringToDouble(numStr);
      if(parsedMult >= 0.05 && parsedMult <= 2.0)
         g_ai_risk_multiplier = parsedMult;
   }
}

"""
target_export = "//+------------------------------------------------------------------+\n//| Export Real-Time Market State for Python AI Sentinel             |\n"

# 4. OnTimer call
target_timer = "   if(!IsTesting())\n   {\n      UpdatePOIs();"
repl_timer = "   if(!IsTesting())\n   {\n      ReadAISentinel();\n      UpdatePOIs();"

# 5. OnTick call
target_tick = "void OnTick()\n{\n   // 1. Tick-level Management"
repl_tick = "void OnTick()\n{\n   ReadAISentinel();\n   // 1. Tick-level Management"

# 6. CalculateLotsCompound
target_lot = "   if(slUSD <= 0.50) slUSD = 3.50;\n   double riskAmount = AccountEquity() * (riskPercent / 100.0);"
repl_lot = """   if(slUSD <= 0.50) slUSD = 3.50;
   double effectiveRisk = riskPercent;
   if(InpEnableStreakBreaker && g_ai_risk_multiplier > 0.05 && g_ai_risk_multiplier <= 2.0)
   {
      effectiveRisk = riskPercent * g_ai_risk_multiplier;
   }
   double riskAmount = AccountEquity() * (effectiveRisk / 100.0);"""

# 7. UpdateHUD
target_hud = '   txt += "  ============================================================\\n";\n   Comment(txt);'
repl_hud = """   txt += StringFormat("  AI Sentinel Bridge: [%s | Risk Mult: %.2fx]\\n", 
                       g_ai_stand_down ? "STAND-DOWN [RED]" : "ACTIVE [GREEN]", g_ai_risk_multiplier);
   txt += "  ============================================================\\n";
   Comment(txt);""".replace("[RED]", chr(0x1F534)).replace("[GREEN]", chr(0x1F7E2))

# 8. Check entries - Judas Sweep
target_entry_sweep = "   if(InpEnableJudasSweepFade && inSweepWindow && CountOpenByMagic(InpMagicSweepFade) == 0)\n   {\n      if(g_stored_asian_high > 0.0"
repl_entry_sweep = """   if(InpEnableJudasSweepFade && inSweepWindow && CountOpenByMagic(InpMagicSweepFade) == 0)
   {
      if(InpEnableMacroNewsShield && g_ai_stand_down)
      {
         // Blocked by AI News Stand Down
      }
      else if(g_stored_asian_high > 0.0"""

# 9. Check entries - London Sniper
target_entry_london = "   if(InpEnableLondonSniper && inLondonWindow && CountOpenByMagic(InpMagicLondonSniper) == 0)\n   {\n      if(g_stored_asian_high > 0.0"
repl_entry_london = """   if(InpEnableLondonSniper && inLondonWindow && CountOpenByMagic(InpMagicLondonSniper) == 0)
   {
      if(InpEnableMacroNewsShield && g_ai_stand_down)
      {
         // Blocked by AI News Stand Down
      }
      else if(g_stored_asian_high > 0.0"""

# 10. Check entries - NY POI
target_entry_ny = "   if(InpEnableNewYorkPOI && inNYWindow && CountOpenByMagic(InpMagicPOISniper) == 0)\n   {\n      // SELL Setup: Resistance Sweep & Rejection"
repl_entry_ny = """   if(InpEnableNewYorkPOI && inNYWindow && CountOpenByMagic(InpMagicPOISniper) == 0)
   {
      if(InpEnableMacroNewsShield && g_ai_stand_down)
      {
         // Blocked by AI News Stand Down
      }
      else
      {
      // SELL Setup: Resistance Sweep & Rejection"""

# Close the else block for NY POI
target_ny_close = "               return;\n            }\n         }\n      }\n   }\n}"
repl_ny_close = "               return;\n            }\n         }\n      }\n      }\n   }\n}"

new_text = text
checks = [
    (target_input, repl_input, "Inputs"),
    (target_fwd, repl_fwd, "Forward Declarations"),
    (target_export, read_ai_func + target_export, "ReadAISentinel"),
    (target_timer, repl_timer, "OnTimer"),
    (target_tick, repl_tick, "OnTick"),
    (target_lot, repl_lot, "CalculateLotsCompound"),
    (target_hud, repl_hud, "UpdateHUD"),
    (target_entry_sweep, repl_entry_sweep, "Judas Sweep Guard"),
    (target_entry_london, repl_entry_london, "London Sniper Guard"),
    (target_entry_ny, repl_entry_ny, "NY POI Guard"),
    (target_ny_close, repl_ny_close, "NY POI Close")
]

for t, r, name in checks:
    if t in new_text:
        new_text = new_text.replace(t, r, 1)
        print(f"Match: {name}")
    else:
        print(f"MISMATCH: {name}")

with open(mql4_path, "w", encoding="utf-8") as f:
    f.write(new_text)
print("Successfully written updated MQL4 file!")
