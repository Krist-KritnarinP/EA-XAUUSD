import os
import json
import shutil

base_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
mt4_experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"

# ---------------------------------------------------------
# 1 & 2. Update MQL4 EAs (Master_v3_5 & Tester_v3_5)
# ---------------------------------------------------------
for fname in ["Gold_POI_Sniper_Master_v3_5.mq4", "Gold_POI_Sniper_Tester_v3_5.mq4"]:
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        code = f.read()

    # Remove unused spreadOffset in ManageLondonRatchet and ManageSweepFadeRatchet
    code = code.replace("   double spreadOffset = (MarketInfo(Symbol(), MODE_SPREAD) * Point);\r\n", "")
    code = code.replace("   double spreadOffset = (MarketInfo(Symbol(), MODE_SPREAD) * Point);\n", "")

    # Upgrade ReadAISentinel colon parsing
    old_sentinel_parse = """   // 2. Parse AI Risk Multiplier
   int pos = StringFind(content, "ai_risk_multiplier\\":");
   if(pos >= 0)
   {
      int start = pos + 21;
      string numStr = "";
      for(int i = start; i < start + 10 && i < StringLen(content); i++)"""

    new_sentinel_parse = """   // 2. Parse AI Risk Multiplier
   int pos = StringFind(content, "ai_risk_multiplier");
   if(pos >= 0)
   {
      int colon = StringFind(content, ":", pos);
      int start = (colon >= 0) ? (colon + 1) : (pos + 21);
      string numStr = "";
      for(int i = start; i < start + 12 && i < StringLen(content); i++)"""

    code = code.replace(old_sentinel_parse.replace("\n", "\r\n"), new_sentinel_parse.replace("\n", "\r\n"))
    code = code.replace(old_sentinel_parse, new_sentinel_parse)

    # Upgrade ExportMarketState with 1-second throttle + force option
    old_export_sig = """void ExportMarketState()
{
   if(IsTesting()) return;"""

    new_export_sig = """void ExportMarketState(bool force = false)
{
   if(IsTesting()) return;
   static datetime s_lastExport = 0;
   if(!force && TimeCurrent() == s_lastExport) return;
   s_lastExport = TimeCurrent();"""

    code = code.replace(old_export_sig.replace("\n", "\r\n"), new_export_sig.replace("\n", "\r\n"))
    code = code.replace(old_export_sig, new_export_sig)

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(code)
    shutil.copy2(fpath, os.path.join(mt4_experts_dir, fname))
    print(f"[OK] Updated and synced {fname}")

# ---------------------------------------------------------
# 3 & 4. Update Python Agent Files
# ---------------------------------------------------------
# Update gold_ai_agent.py (Fix #3 compute_5_sciences_quant keys & Fix #4 Breaking News Prompt)
agent_base_path = os.path.join(base_dir, "gold_ai_agent.py")
with open(agent_base_path, "r", encoding="utf-8") as f:
    py_base = f.read()

# Fix #4: Update Breaking News Prompt version name
py_base = py_base.replace(
    "You are the Chief Institutional Macro & Breaking News Analyst for Gold Sniper v6.3.8-BetaB (XAUUSD).",
    "You are the Chief Institutional Macro & Breaking News Analyst for Gold POI Sniper v3.5 (XAUUSD)."
)

# Fix #3: Add prev_high, prev_low, elliott_wave to compute_5_sciences_quant return dict
old_return_block = """        "buy_rr": buy_rr_str,
        "sell_rr": sell_rr_str
    }"""

new_return_block = """        "buy_rr": buy_rr_str,
        "sell_rr": sell_rr_str,
        "prev_high": float(state.get("pdh", 0.0) or (prev_bar["high"] if total_bars >= 50 else live_price + 20.0)),
        "prev_low": float(state.get("pdl", 0.0) or (prev_bar["low"] if total_bars >= 50 else live_price - 20.0)),
        "elliott_wave": f"Impulse Span ${w_impulse:.2f} ({'Bullish Wave iii/v' if 'BULLISH' in d1_trend else 'Corrective Wave A-B-C'})"
    }"""

py_base = py_base.replace(old_return_block.replace("\n", "\r\n"), new_return_block.replace("\n", "\r\n"))
py_base = py_base.replace(old_return_block, new_return_block)

with open(agent_base_path, "w", encoding="utf-8") as f:
    f.write(py_base)
print("[OK] Updated gold_ai_agent.py")

# Update gold_ai_agent_poi_v3_5.py & gold_ai_agent_poi_v2_5.py (ensure fallback to state['pdh']/'pdl' in send_poi_quant_briefing)
for p_name in ["gold_ai_agent_poi_v3_5.py", "gold_ai_agent_poi_v2_5.py"]:
    p_path = os.path.join(base_dir, p_name)
    with open(p_path, "r", encoding="utf-8") as f:
        p_code = f.read()

    old_quant_fields = """                "name": "📐 1. Dow Theory & Market Structure (D1 / H4 / H1)",
                "value": f"• **โครงสร้าง D1:** `{quant_data.get('d1_trend')}`\\n"
                         f"• **Previous Day High (PDH):** `${quant_data.get('prev_high', 0.0):.2f}`\\n"
                         f"• **Previous Day Low (PDL):** `${quant_data.get('prev_low', 0.0):.2f}`","""

    new_quant_fields = """                "name": "📐 1. Dow Theory & Market Structure (D1 / H4 / H1)",
                "value": f"• **โครงสร้าง D1:** `{quant_data.get('d1_trend')}`\\n"
                         f"• **Previous Day High (PDH):** `${(quant_data.get('prev_high') or state.get('pdh', 0.0)):.2f}`\\n"
                         f"• **Previous Day Low (PDL):** `${(quant_data.get('prev_low') or state.get('pdl', 0.0)):.2f}`","""

    p_code = p_code.replace(old_quant_fields.replace("\n", "\r\n"), new_quant_fields.replace("\n", "\r\n"))
    p_code = p_code.replace(old_quant_fields, new_quant_fields)

    with open(p_path, "w", encoding="utf-8") as f:
        f.write(p_code)
    print(f"[OK] Updated {p_name}")

# ---------------------------------------------------------
# 5. Update config.json (30 mins before & 30 mins after news)
# ---------------------------------------------------------
cfg_path = os.path.join(base_dir, "config.json")
with open(cfg_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

cfg["news_stand_down_mins_before"] = 30
cfg["news_stand_down_mins_after"] = 30

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print("[OK] Updated config.json (news_stand_down_mins_before=30, news_stand_down_mins_after=30)")
