# -*- coding: utf-8 -*-
"""
Dispatches the CPI News Cleared & Directional Macro Evaluation Briefing to Discord.
"""
import os
import json
import urllib.request
from datetime import datetime, timezone

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

webhook_orders = config.get("discord_webhook_url")
webhook_briefing = config.get("discord_webhook_briefing") or webhook_orders

embed = {
    "title": "🛡️ [MACRO NEWS SENTINEL CLEARED] ปลดล็อกระบบ Auto-Stand Down — สภาวะเทรดปกติ 100%!",
    "description": (
        "✅ **ช่วงเวลาความผันผวนของตัวเลขเงินเฟ้อสหรัฐฯ (US CPI & Core CPI) ผ่านพ้นไปแล้ว (+15 นาทีหลังประกาศข่าว)**\n\n"
        "ระบบ **AI Sentinel** ได้ทำการปลดล็อกระบบคำสั่งใน MT4 เรียบร้อยแล้ว สเปรดบีบตัวกลับสู่ระดับปกติ "
        "เครื่องยนต์เทรดทุกระบบ (**London Sniper, New York Trend-Rider, Asian Scalper**) กลับมาทำงานเต็มรูปแบบ 100%"
    ),
    "color": 0x2ecc71,  # Emerald Green
    "fields": [
        {
            "name": "📊 1. ข้อมูลตัวเลขเงินเฟ้อที่ประกาศ (US CPI Inflation Focus)",
            "value": (
                "• **Core CPI m/m:** คาดการณ์ `0.2%` │ ก่อนหน้า `0.3%`\n"
                "• **Core CPI y/y:** คาดการณ์ `2.5%` │ ก่อนหน้า `2.4%`\n"
                "• **CPI m/m:** คาดการณ์ `0.6%` │ ก่อนหน้า `0.4%`\n"
                "• **CPI y/y:** คาดการณ์ `3.6%` │ ก่อนหน้า `3.4%`"
            ),
            "inline": False
        },
        {
            "name": "🧭 2. คู่มือประเมินทิศทางกระทบตลาดทองคำ & ดอลลาร์ (Directional Matrix)",
            "value": (
                "📈 **กรณีตัวเลขจริงออกมามากกว่าคาด (Actual > Forecast):**\n"
                "• 💵 **ดอลลาร์ (DXY):** แข็งค่าขึ้น 🟢 *(Fed มีแนวโน้มคงดอกเบี้ยสูงนาน / Hawkish, Bond Yield พุ่ง)*\n"
                "• 🪙 **ทองคำ (XAUUSD):** ย่อตัวลง / มีแรงเทขายทำกำไร 🔴\n\n"
                "📉 **กรณีตัวเลขจริงออกมาน้อยกว่าคาด (Actual < Forecast):**\n"
                "• 💵 **ดอลลาร์ (DXY):** อ่อนค่าลง 🔴 *(เงินเฟ้อชะลอตัว / เพิ่มน้ำหนัก Fed ผ่อนคลายนโยบาย)*\n"
                "• 🪙 **ทองคำ (XAUUSD):** ปรับตัวขึ้น / บินต่อ 🟢 *(ดอลลาร์อ่อนและ Yield ลดลง หนุนแรงซื้อทองคำ)*\n\n"
                "⚪ **กรณีตัวเลขจริงออกมาเท่ากับหรือใกล้เคียงคาด (In-line):**\n"
                "• 🪙 **ทองคำ (XAUUSD):** แกว่งตัวผันผวนในกรอบเทคนิค Sideway รอโมเมนตัมรอบเซสชันใหญ่"
            ),
            "inline": False
        },
        {
            "name": "🏹 3. แท็กติกและคำแนะนำสำหรับระบบ Gold Sniper",
            "value": (
                "• **สเปรดตลาด:** กลับสู่ระดับปกติ (Safe Execution Window)\n"
                "• **คำแนะนำ:** เฝ้าระวังแท่งเทียน M15 จบแท่งแรกหลังข่าว เพื่อดูการสร้างฐาน Support/Resistance ก่อนพิจารณาเข้าตามเทรนด์\n"
                "• **สถานะพอร์ต:** `Normal Trading Active (Green Light 🟢)`"
            ),
            "inline": False
        }
    ],
    "footer": {"text": "Gold Sniper AI Co-Pilot v6.3.3 | Live Macro Sentinel & Trade Clearance"},
    "timestamp": datetime.now(timezone.utc).isoformat()
}

payload = json.dumps({"embeds": [embed]}).encode("utf-8")
headers = {
    "Content-Type": "application/json",
    "User-Agent": "GoldSniperBot/6.3.1"
}

# Dispatch to Orders channel
if webhook_orders:
    req = urllib.request.Request(webhook_orders, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as r:
        print(f"[+] Dispatched to Orders channel: HTTP {r.getcode()}")

# Dispatch to Briefing channel if distinct
if webhook_briefing and webhook_briefing != webhook_orders:
    req = urllib.request.Request(webhook_briefing, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as r:
        print(f"[+] Dispatched to Briefing channel: HTTP {r.getcode()}")

print("\nCPI Cleared & Directional Advisory successfully sent to Discord!")
