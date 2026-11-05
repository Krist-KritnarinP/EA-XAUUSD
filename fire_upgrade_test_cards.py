import os
import sys
import json

sys.path.insert(0, r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4")
import gold_ai_agent_poi_v3_5 as agent

cfg = agent.load_poi_config()
mt4_dir = cfg.get("mt4_files_dir")
with open(os.path.join(mt4_dir, "market_state.json"), "r", encoding="utf-8") as f:
    st = json.load(f)

wh_hb = cfg.get("discord_webhook_heartbeat")
wh_q = cfg.get("discord_webhook_quant_5sciences")
api_key = cfg.get("gemini_api_key")

agent.send_poi_heartbeat_report(wh_hb, st, api_key)
qd = agent.base_agent.compute_5_sciences_quant(mt4_dir, "GOLD", st, float(st.get("bid", 3900.0)))
agent.send_poi_quant_briefing(wh_q, "16:18 (US ELECTION & MACRO UPGRADE)", st, qd, api_key)
print("[OK] Dispatched upgraded Heartbeat & Quant 5-Sciences cards to Discord!")
