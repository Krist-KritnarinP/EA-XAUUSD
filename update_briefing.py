# -*- coding: utf-8 -*-
"""
Script to update gold_ai_agent.py with the new robust Python 3.6 date parser and full Gemini Morning Macro Briefing
"""
import os

agent_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py"
with open(agent_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Replace parse_event_time_thai
old_parse = """def parse_event_time_thai(iso_str):
    \"\"\"Converts ISO 8601 date string to Thai Local Time string (UTC+7)\"\"\"
    try:
        dt = datetime.fromisoformat(iso_str)
        thai_tz = timezone(timedelta(hours=7))
        dt_thai = dt.astimezone(thai_tz)
        return dt_thai
    except Exception:
        return None"""

new_parse = """def parse_event_time_thai(iso_str):
    \"\"\"Converts ISO 8601 date string to Thai Local Time string (UTC+7) - Python 3.6 Compatible\"\"\"
    try:
        if not iso_str:
            return None
        main_part = iso_str[:19]
        dt = datetime.strptime(main_part, "%Y-%m-%dT%H:%M:%S")
        tz_part = iso_str[19:]
        if tz_part.endswith("Z"):
            offset_hours, offset_minutes = 0, 0
        elif len(tz_part) == 6:
            sign = 1 if tz_part[0] == '+' else -1
            offset_hours = sign * int(tz_part[1:3])
            offset_minutes = sign * int(tz_part[4:6])
        else:
            offset_hours, offset_minutes = 0, 0
        event_tz = timezone(timedelta(hours=offset_hours, minutes=offset_minutes))
        dt_with_tz = dt.replace(tzinfo=event_tz)
        thai_tz = timezone(timedelta(hours=7))
        return dt_with_tz.astimezone(thai_tz)
    except Exception:
        return None"""

code = code.replace(old_parse, new_parse)

# 2. Replace send_discord_morning_news_briefing with full Gemini macro briefing
# Find function boundaries
start_idx = code.find("def send_discord_morning_news_briefing")
end_idx = code.find("# ==============================================================================\n# DISCORD REAL-TIME ALERTS")

new_briefing = """def send_discord_morning_news_briefing(webhook_url, api_key, state=None):
    \"\"\"Generates and dispatches daily 07:00 AM morning macro overview via Gemini Flash\"\"\"
    if not webhook_url:
        return

    now_thai = datetime.now(timezone(timedelta(hours=7)))
    date_display = now_thai.strftime("%d/%m/%Y")
    time_display = now_thai.strftime("%H:%M:%S")

    # Get state info
    if state is None:
        state = {}
    gold_price = state.get("bid", 0.0)
    equity = state.get("equity", 1000.0)
    price_str = f"${gold_price:,.2f}" if gold_price > 0 else "N/A"

    today_events = get_today_high_impact_events()
    week_events = fetch_economic_calendar()

    events_summary = []
    for ev in week_events[:10]:
        dt = parse_event_time_thai(ev.get("date", ""))
        time_str = dt.strftime("%a %d/%m %H:%M น.") if dt else "N/A"
        events_summary.append({
            "title": ev.get("title", ""),
            "time_thai": time_str,
            "forecast": ev.get("forecast") or "N/A",
            "previous": ev.get("previous") or "N/A"
        })

    prompt_text = f\"\"\"คุณคือหัวหน้านักวิเคราะห์เศรษฐกิจมหภาคและทองคำระดับสถาบันการเงิน (Chief Macro Strategist) ประจำระบบ Gold Sniper v6.3.1
กรุณาจัดทำ "Daily Morning Macro Briefing" (บทวิเคราะห์ภาพรวมตลาดทองคำภาคเช้า ประจำวันที่ {date_display}) ส่งเข้า Discord ห้องเทรดเดอร์

ข้อมูลสดจากตลาดขณะนี้:
- ราคาทองคำปัจจุบัน: {price_str}
- พอร์ต Equity: ${equity:,.2f}
- ปฏิทินข่าวสัปดาห์นี้:
{json.dumps(events_summary, ensure_ascii=False, indent=2)}

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
}}\"\"\"

    ai_data = None
    if api_key:
        for model_name in ["models/gemini-flash-latest", "models/gemini-flash-lite-latest"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
                payload = json.dumps({
                    "contents": [{"parts": [{"text": prompt_text}]}],
                    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
                }).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    ai_data = json.loads(raw_text)
                    if ai_data:
                        break
            except Exception as e:
                safe_print(f"    [Gemini {model_name} Fallback] {e}")

    macro_sent = ai_data.get("macro_sentiment") if ai_data else "ตลาดทองคำเคลื่อนไหวในกรอบสะสมพลัง จับตาทิศทางค่าเงินดอลลาร์สหรัฐฯ และความเห็นเจ้าหน้าที่เฟด"
    gold_bias = ai_data.get("gold_bias") if ai_data else "ทิศทางแกว่งตัวรอปัจจัยหนุนใหม่ แนะนำเทรดตามกรอบ Tri-Session อย่างเคร่งครัด"
    key_news = ai_data.get("key_news_focus") if ai_data else "สัปดาห์นี้มีข่าวสำคัญ Core CPI และ PPI จับตาช่วงข่าวเพื่อหลีกเลี่ยงสเปรดถ่าง"
    trade_plan = ai_data.get("trade_plan") if ai_data else "Asian Squeeze เก็บกระแสเงินสดรอบเช้า, London ดัก Judas Breakout, NY ดัก Reversal ตามระเบียบ"

    embed = {
        "title": f"🌅 [DAILY MORNING MACRO BRIEFING] Gold Sniper v6.3.1 ({date_display})",
        "description": f"**รายงานสรุปภาพรวมตลาดทองคำและเศรษฐกิจมหภาคประจำวัน**\\nวิเคราะห์โดย **Gemini AI Macro Engine** ร่วมกับระบบ **Gold Sniper v6.3.1**\\n\\n🪙 **ราคาทองคำสด:** `{price_str}` | 💰 **พอร์ต Equity:** `${equity:,.2f}`",
        "color": 0xf39c12,  # Morning Golden Orange
        "fields": [
            {"name": "🌍 1. ภาพรวมเศรษฐกิจมหภาค (Macro Sentiment)", "value": macro_sent, "inline": False},
            {"name": "⚖️ 2. ทิศทางแนวโน้มทองคำวันนี้ (Daily Gold Bias)", "value": gold_bias, "inline": False},
            {"name": "🔴 3. โฟกัสข่าวสำคัญ & ข่าวกล่องแดงสัปดาห์นี้", "value": key_news, "inline": False},
            {"name": "🎯 4. แผนกลยุทธ์ระบบ Gold Sniper v6.3.1 ประจำวัน", "value": trade_plan, "inline": False}
        ],
        "footer": {"text": f"Gold Sniper AI Co-Pilot v6.3.1 | Morning Briefing ส่งทุกเช้า 07:00 น. (รายงาน ณ {time_display} น.)"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if post_discord_embed(webhook_url, embed):
        safe_print(f"\\n    [📅 DISCORD NOTIFIED] Full Morning Macro briefing successfully sent to Discord! ({time_display})")
"""

if start_idx != -1 and end_idx != -1:
    code = code[:start_idx] + new_briefing + "\n" + code[end_idx:]

# 3. Update main loop trigger for morning briefing:
# Trigger at >= 07:00 AM Thai time
old_trigger = """            # 2. Daily Morning Macro Briefing Trigger (Sent once per day in morning)
            today_thai_str = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")
            if alerted_morning_briefing_day != today_thai_str:
                send_discord_morning_news_briefing(webhook_url, gemini_key)
                alerted_morning_briefing_day = today_thai_str"""

new_trigger = """            # 2. Daily Morning Macro Briefing Trigger (Sent at 07:00 AM Thai Time)
            now_thai = datetime.now(timezone(timedelta(hours=7)))
            today_thai_str = now_thai.strftime("%Y-%m-%d")
            if now_thai.hour >= 7 and alerted_morning_briefing_day != today_thai_str:
                send_discord_morning_news_briefing(webhook_url, gemini_key, state)
                alerted_morning_briefing_day = today_thai_str"""

code = code.replace(old_trigger, new_trigger)

with open(agent_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully updated gold_ai_agent.py with robust Morning Briefing!")
