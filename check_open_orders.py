import json, os

path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Files\market_state.json"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
    print("market_state.json keys:", data.keys())
    print("Balance:", data.get("balance"), "Equity:", data.get("equity"))
    print("Open orders count:", len(data.get("open_orders", [])))
    for o in data.get("open_orders", []):
        print(o)
    print("\nRecent closed orders count:", len(data.get("recent_closed_orders", [])))
    for o in data.get("recent_closed_orders", [])[:5]:
        print(o)

agent_state_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\agent_runtime_state.json"
if os.path.exists(agent_state_path):
    with open(agent_state_path, "r") as f:
        astate = json.load(f)
    print("\nagent_runtime_state open_orders_snapshot:")
    for k, v in astate.get("open_orders_snapshot", {}).items():
        print(f"Ticket {k}: {v}")
