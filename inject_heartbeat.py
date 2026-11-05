# -*- coding: utf-8 -*-
import os

target_file = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py"
with open(target_file, "r", encoding="utf-8") as f:
    code = f.read()

heartbeat_func = """
def send_discord_heartbeat_report(webhook_url, state):
    \"\"\"Dispatches 30-min heartbeat report when there are no active positions\"\"\"
    if not webhook_url:
        return

    now_thai = datetime.now(timezone(timedelta(hours=7)))
    time_thai_str = now_thai.strftime("%d/%m/%Y %H:%M:%S") + " น."

    equity = state.get("equity", 0.0)
    balance = state.get("balance", 0.0)
    bid = state.get("bid", 0.0)
    gold_price = bid if bid > 0 else state.get("close", 0.0)
    daily_pnl = state.get("daily_pnl", 0.0)
    daily_pnl_pct = state.get("daily_pnl_pct", 0.0)
    server_time = state.get("server_time", "")

    try:
        h = int(server_time.split(" ")[1].split(":")[0])
        m = int(server_time.split(" ")[1].split(":")[1])
    except Exception:
        h, m = 0, 0

    if h >= 2 and (h < 6 or (h == 2 and m >= 30)):
        session_desc = "🌅 Asian Squeeze Sweeper (02:30 - 06:00)"
    elif h >= 8 and (h < 11 or (h == 11 and m <= 30)):
        session_desc = "🇬🇧 London Institutional Sniper (08:00 - 11:30)"
    elif h >= 15 and (h < 17 or (h == 17 and m <= 30)):
        session_desc = "🗽 New York Confirmed Reversal (15:00 - 17:30)"
    else:
        session_desc = "💤 Stand-by / Accumulation Window"

    embed = {
        "title": "💓 [HEARTBEAT REPORT] Gold Sniper AI ยังทำงานปกติดี",
        "description": "🟢 **บอททำงานเชื่อมต่อตลอดเวลา 100%** ขณะนี้ **ยังไม่มีออเดอร์ค้างในพอร์ต** กำลังสแตนด์บายเฝ้าระวังโครงสร้างราคาทองคำตามระบบ Tri-Session และตรวจจับข่าว Macro Sentinel",
        "color": 0x3498db,
        "fields": [
            {"name": "⏰ เวลาตรวจสอบ (เวลาไทย)", "value": f"`{time_thai_str}`", "inline": True},
            {"name": "💰 ยอด Equity ปัจจุบัน", "value": f"`${equity:,.2f}`", "inline": True},
            {"name": "🪙 ราคาทองคำสด (Gold Bid)", "value": f"`${gold_price:,.2f}`", "inline": True},
            {"name": "📊 สถานะการถือครอง", "value": "`ไม่มีออเดอร์ค้าง (0 ไม้)`", "inline": True},
            {"name": "📈 กำไรวันนี้ (Daily PnL)", "value": f"`{daily_pnl_pct:+.1f}% (${daily_pnl:+.2f})`", "inline": True},
            {"name": "🎯 เซสชันตลาดปัจจุบัน", "value": f"`{session_desc}`", "inline": True}
        ],
        "footer": {"text": "Gold Sniper AI Co-Pilot v6.3.1 | รายงานความพร้อมอัตโนมัติทุก 30 นาที"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if post_discord_embed(webhook_url, embed):
        safe_print(f"\\n    [💓 HEARTBEAT NOTIFIED] 30-min heartbeat report sent to Discord! ({time_thai_str})")
"""

target_anchor = "def update_mt4_sentinel_file"
if "def send_discord_heartbeat_report" not in code:
    code = code.replace(target_anchor, heartbeat_func + "\n" + target_anchor)

var_anchor = "last_active_day = None"
new_vars = """last_active_day = None
    enable_heartbeat = config.get("enable_periodic_heartbeat", True)
    heartbeat_interval_sec = config.get("heartbeat_interval_mins", 30) * 60
    last_heartbeat_time = time.time()"""

if "enable_heartbeat =" not in code:
    code = code.replace(var_anchor, new_vars)

loop_check = """            # 6. Periodic Heartbeat Check (Every 30 minutes, ONLY when NO open orders)
            if enable_heartbeat:
                if (time.time() - last_heartbeat_time) >= heartbeat_interval_sec:
                    if len(open_orders) == 0:
                        send_discord_heartbeat_report(webhook_url, state)
                    else:
                        safe_print("\\n    [⏳ HEARTBEAT SKIPPED] Positions currently open. Muting heartbeat report.")
                    last_heartbeat_time = time.time()

            time.sleep(1)"""

if "send_discord_heartbeat_report(webhook_url, state)" not in code:
    idx = code.rfind("time.sleep(1)")
    if idx != -1:
        code = code[:idx] + loop_check + code[idx + len("time.sleep(1)"):]

with open(target_file, "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully injected heartbeat into gold_ai_agent.py!")
