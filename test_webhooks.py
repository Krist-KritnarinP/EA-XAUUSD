import json
import urllib.request

config = json.load(open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\config.json"))

webhooks = {
    "1. Morning Macro Briefing": config.get("discord_webhook_morning_briefing"),
    "2. Manual Trades": config.get("discord_webhook_user_trades"),
    "3. POI Orders": config.get("discord_webhook_orders"),
    "4. 5-Sciences Quant": config.get("discord_webhook_quant_5sciences"),
    "5. News Guard": config.get("discord_webhook_news_guard"),
    "6. Heartbeat Check": config.get("discord_webhook_heartbeat")
}

print("=== TESTING DISCORD WEBHOOKS STATUS ===")
for name, url in webhooks.items():
    if not url:
        print(f"[-] {name}: NOT CONFIGURED")
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            channel_id = data.get("channel_id", "N/A")
            hook_name = data.get("name", "N/A").encode("ascii", errors="replace").decode("ascii")
            print(f"[+] {name}: OK! Hook Name: '{hook_name}' | Channel ID: {channel_id}")
    except Exception as e:
        print(f"[!] {name}: Error {e}")
