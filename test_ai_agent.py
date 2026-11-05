# -*- coding: utf-8 -*-
"""
Quick Diagnostics & Live Test for Gold Sniper AI Agent v6.3.1 (cp1252 safe)
"""
import os
import sys
import json
import time

script_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
sys.path.append(script_dir)

from gold_ai_agent import (
    load_config,
    fetch_economic_calendar,
    get_today_high_impact_events,
    check_active_live_news_now,
    send_discord_morning_news_briefing,
    send_discord_order_opened_alert,
    safe_print,
    post_discord_embed
)

def run_ai_live_test():
    safe_print("============================================================")
    safe_print("   [*] STARTING GOLD SNIPER AI AGENT v6.3.1 LIVE TEST")
    safe_print("============================================================")

    # 1. Test Config
    config = load_config()
    webhook_url = config.get("discord_webhook_url")
    gemini_key = config.get("gemini_api_key")
    safe_print("[1] Config Loaded:")
    safe_print(f"    - System Version: {config.get('system_version')}")
    safe_print(f"    - MT4 Files Dir: {config.get('mt4_files_dir')}")
    safe_print(f"    - Discord Webhook: {'Configured [OK]' if webhook_url else 'Missing [X]'}")
    safe_print(f"    - Gemini API Key: {'Configured [OK]' if gemini_key else 'Missing [X]'}")

    # 2. Test Live ForexFactory Feed
    safe_print("\n[2] Testing Live Macro News Feed (FairEconomy / ForexFactory)...")
    events = fetch_economic_calendar()
    safe_print(f"    - Total High-Impact USD Events Cached this week: {len(events)} events")
    
    today_events = get_today_high_impact_events()
    safe_print(f"    - High-Impact Events Scheduled Today (Thai Time): {len(today_events)}")
    for ev in today_events:
        safe_print(f"      [!] {ev['time_th']} - {ev['title']} (Forecast: {ev['forecast']}, Prev: {ev['previous']})")

    # 3. Test Active News Stand-Down Sentinel
    safe_print("\n[3] Testing Live Stand-Down Detection (Now)...")
    active_now = check_active_live_news_now()
    if active_now:
        safe_print(f"    - [WARN] ACTIVE NEWS RIGHT NOW: {len(active_now)} event(s)!")
        for ev in active_now:
            safe_print(f"      [RED FOLDER] {ev['title']} ({ev['diff_mins']}m from release)")
    else:
        safe_print("    - [CLEAR] Market Skies Clear: No active red folders in +-15m window.")

    # 4. Trigger Daily Morning Macro Briefing via Gemini Flash -> Discord
    safe_print("\n[4] Triggering Live Gemini 3 Flash Macro Briefing to Discord...")
    send_discord_morning_news_briefing(webhook_url, gemini_key)

    # 5. Trigger Simulated Live Order Execution Alert -> Discord
    safe_print("\n[5] Triggering Test Order Execution Notification to Discord...")
    sim_order = {
        "ticket": 999631,
        "type": 0, # BUY
        "lots": 0.08,
        "open_price": 4195.50,
        "sl": 4187.50,
        "tp": 4223.50,
        "engine": "Sniper"
    }
    sim_state = {
        "equity": 1000.0,
        "spread_points": 18,
        "bid": 4195.50,
        "ask": 4195.68
    }
    send_discord_order_opened_alert(webhook_url, sim_order, sim_state, gemini_key)

    # 6. Check MT4 Bridge Sync File
    mt4_dir = config.get("mt4_files_dir")
    sentinel_file = os.path.join(mt4_dir, "ai_sentinel.json")
    safe_print("\n[6] Testing Writing ai_sentinel.json for MT4 Bridge...")
    sentinel_payload = {
        "timestamp": time.time(),
        "stand_down": False,
        "reason": "Diagnostics Health Check Passed",
        "active_news_count": 0
    }
    with open(sentinel_file, "w", encoding="utf-8") as f:
        json.dump(sentinel_payload, f, indent=2)
    safe_print(f"    - Written ai_sentinel.json to: {sentinel_file} [OK]")

    safe_print("\n============================================================")
    safe_print("   [+] ALL TESTS COMPLETED! Check your Discord channel now!")
    safe_print("============================================================")

if __name__ == "__main__":
    run_ai_live_test()
