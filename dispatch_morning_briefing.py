# -*- coding: utf-8 -*-
"""
Generate and dispatch the real Daily Morning Macro Briefing with Gemini Flash
"""
import urllib.request, json, os, sys
from datetime import datetime, timezone, timedelta

script_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
config_path = os.path.join(script_dir, "config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

webhook_url = config.get("discord_webhook_url")
api_key = config.get("gemini_api_key")
state_path = os.path.join(config.get("mt4_files_dir"), "market_state.json")

# Read current MT4 state
try:
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    state = {}

gold_price = state.get("bid", 4205.0)
equity = state.get("equity", 1000.0)

now_thai = datetime.now(timezone(timedelta(hours=7)))
date_display = now_thai.strftime("%d/%m/%Y")
time_display = now_thai.strftime("%H:%M:%S")

# Prompt for Gemini Flash
prompt = f"""คุณคือหัวหน้านักวิเคราะห์เศรษฐกิจมหภาคและทองคำระดับสถาบันการเงิน (Chief Macro Strategist) ประจำระบบ Gold Sniper v6.3.1
กรุณาจัดทำ "Daily Morning Macro Briefing" (บทวิเคราะห์ภาพรวมตลาดทองคำภาคเช้า ประจำวันที่ {date_display}) ส่งเข้า Discord ห้องเทรดเดอร์

ข้อมูลสดจากตลาดขณะนี้:
- ราคาทองคำปัจจุบัน: ${gold_price:,.2f}
- พอร์ต Equity: ${equity:,.2f}
- ปฏิทินข่าวสัปดาห์นี้: มีข่าวสำคัญ Core CPI, CPI y/y, Core PPI, Retail Sales และประธาน Fed แถลง

กรุณาวิเคราะห์และจัดทำเนื้อหาเป็นภาษาไทย สไตล์ Professional Institutional Trader:
1. **ภาพรวมตลาดมหภาค (Macro Sentiment & Key Drivers):** ทิศทางเงินดอลลาร์ (DXY), อัตราดอกเบี้ย Fed, และความเสี่ยงภูมิรัฐศาสตร์
2. **ทิศทางทองคำวันนี้ (Gold Bias & Technical Outlook):** Bullish / Bearish / Range-bound พร้อมกรอบราคาสำคัญ
3. **โฟกัสข่าวสำคัญสัปดาห์นี้:** เตือนวันและเวลาข่าวกล่องแดงที่จะส่งผลต่อสเปรดและ Slippage (เช่น วันพุธ CPI)
4. **แผนการเทรด Gold Sniper v6.3.1 วันนี้:** คำแนะนำสำหรับเซสชัน Asian Squeeze (เช้า), London Sniper (สาย), และ New York Reversal (ค่ำ)

ตอบเป็น JSON strictly โครงสร้าง:
{{
  "macro_sentiment": "สรุปภาพรวมเศรษฐกิจมหภาคสั้นกระชับ ทรงพลัง 2-3 บรรทัด",
  "gold_bias": "ทิศทางทองคำวันนี้ (BULLISH / BEARISH / SIDEWAY) พร้อมเหตุผลและระดับราคา",
  "key_news_focus": "สรุปข่าวกล่องแดงที่ต้องเฝ้าระวังในสัปดาห์นี้ พร้อมคำเตือนมาตรการ AI Sentinel",
  "trade_plan": "แผนกลยุทธ์ของ Gold Sniper สำหรับรอบเอเชีย, ลอนดอน, และนิวยอร์กวันนี้"
}}"""

print("[*] Calling Gemini Flash for Comprehensive Morning Macro Briefing...")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
payload = json.dumps({
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
}).encode("utf-8")
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

ai_data = None
with urllib.request.urlopen(req, timeout=15) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    raw_text = res["candidates"][0]["content"]["parts"][0]["text"].strip()
    ai_data = json.loads(raw_text)

print("[+] Gemini Analysis Received successfully!")

embed = {
    "title": f"🌅 [DAILY MORNING MACRO BRIEFING] Gold Sniper v6.3.1 ({date_display})",
    "description": f"**รายงานสรุปภาพรวมตลาดทองคำและเศรษฐกิจมหภาคประจำวัน**\nวิเคราะห์โดย **Gemini AI Macro Engine** ร่วมกับระบบ **Gold Sniper v6.3.1**\n\n🪙 **ราคาทองคำสด:** `${gold_price:,.2f}` | 💰 **พอร์ต Equity:** `${equity:,.2f}`",
    "color": 0xf39c12,  # Morning Golden Orange
    "fields": [
        {
            "name": "🌍 1. ภาพรวมเศรษฐกิจมหภาค (Macro Sentiment)",
            "value": ai_data.get("macro_sentiment", "N/A"),
            "inline": False
        },
        {
            "name": "⚖️ 2. ทิศทางแนวโน้มทองคำวันนี้ (Daily Gold Bias)",
            "value": ai_data.get("gold_bias", "N/A"),
            "inline": False
        },
        {
            "name": "🔴 3. โฟกัสข่าวสำคัญ & ข่าวกล่องแดงสัปดาห์นี้",
            "value": ai_data.get("key_news_focus", "N/A"),
            "inline": False
        },
        {
            "name": "🎯 4. แผนกลยุทธ์ระบบ Gold Sniper v6.3.1 ประจำวัน",
            "value": ai_data.get("trade_plan", "N/A"),
            "inline": False
        }
    ],
    "footer": {"text": f"Gold Sniper AI Co-Pilot v6.3.1 | Morning Briefing ส่งทุกเช้า 07:00 น. (รายงาน ณ {time_display} น.)"},
    "timestamp": datetime.now(timezone.utc).isoformat()
}

req_dc = urllib.request.Request(
    webhook_url,
    data=json.dumps({"embeds": [embed]}).encode("utf-8"),
    headers={"Content-Type": "application/json", "User-Agent": "GoldSniperBot/6.3.1"}
)
with urllib.request.urlopen(req_dc, timeout=10) as resp:
    print(f"[+] DISCORD SENT SUCCESSFULLY! Code: {resp.getcode()}")
