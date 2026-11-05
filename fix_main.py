# -*- coding: utf-8 -*-
import os

agent_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py"
with open(agent_path, "r", encoding="utf-8") as f:
    code = f.read()

main_start = code.find("def main():")
if main_start == -1:
    print("def main() not found")
    exit(1)

new_main = """def main():
    config = load_config()
    mt4_dir = config.get("mt4_files_dir", "")
    state_file = os.path.join(mt4_dir, "market_state.json")
    webhook_url = config.get("discord_webhook_url")
    gemini_key = config.get("gemini_api_key")
    jackpot_target = config.get("jackpot_profit_lock_usd", 100.0)

    safe_print("\\n" + "="*70)
    safe_print(" 🏹 GOLD SNIPER AI AGENT v6.3.1 - INSTITUTIONAL SENTINEL & CO-PILOT")
    safe_print(" Architecture: Decoupled Zero-Latency Engine (Native MT4 < 5ms)")
    safe_print(" Intelligence: Live ForexFactory Macro Sentinel + Gemini 3 Flash")
    safe_print("="*70)
    safe_print(f"[*] Target Directory: {mt4_dir}")
    safe_print(f"[*] Macro News Shield: Stand-down +-15 mins during Red Folders")
    safe_print(f"[*] Jackpot Profit Lock: London Bank >= ${jackpot_target:.2f} -> Halts NY Session")
    safe_print(f"[*] Tri-Session Coverage: Asia Squeeze (02:30), London (08:00), NY (15:00)")
    safe_print(f"[*] Discord Webhook: {'CONNECTED' if webhook_url else 'DISABLED'}")
    safe_print(f"[*] Gemini AI Studio: {'ACTIVE (gemini-flash-latest)' if gemini_key else 'STANDBY'}")
    safe_print("="*70)
    safe_print("[+] Synchronizing with MT4 Bridge Engine...\\n")

    # Initial sync of calendar
    fetch_economic_calendar()

    known_tickets = set()
    alerted_jackpot_day = None
    alerted_morning_briefing_day = None
    last_stand_down_state = False
    last_active_day = None
    last_heartbeat_mark = -1
    state = {}

    while True:
        try:
            # 1. Read MT4 Market State FIRST
            if not os.path.exists(state_file):
                safe_print("[!] Waiting for MT4 market_state.json from GoldSniper_Bridge_v6_3_1...")
                time.sleep(2)
                continue

            with open(state_file, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    time.sleep(1)
                    continue
                state = json.loads(content)

            now_thai = datetime.now(timezone(timedelta(hours=7)))
            today_thai_str = now_thai.strftime("%Y-%m-%d")

            server_time_str = state.get("server_time", "")
            current_day = server_time_str.split(" ")[0] if server_time_str else today_thai_str

            if current_day != last_active_day:
                last_active_day = current_day
                alerted_jackpot_day = None
                known_tickets.clear()

            daily_pnl = state.get("daily_pnl", 0.0)
            daily_pnl_pct = state.get("daily_pnl_pct", 0.0)
            sniper_pnl = state.get("daily_sniper_pnl", 0.0)
            jackpot_locked = state.get("jackpot_locked", False)
            daily_trades = state.get("daily_total_trades", 0)
            equity = state.get("equity", 1000.0)
            spread_pts = state.get("spread_points", 0)
            open_orders = state.get("open_orders", [])

            # 2. Macro Calendar Check (Every 10 seconds)
            active_news = check_active_live_news_now(before_mins=15, after_mins=15)
            is_stand_down = len(active_news) > 0

            # Write Sentinel status for MT4
            update_mt4_sentinel_file(mt4_dir, is_stand_down, active_news)

            if is_stand_down and not last_stand_down_state:
                send_discord_stand_down_alert(webhook_url, active_news)
                last_stand_down_state = True
            elif not is_stand_down and last_stand_down_state:
                safe_print("\\n    [🛡️ SENTINEL] News window cleared. Normal trading resumed.")
                last_stand_down_state = False

            # 3. Daily Morning Macro Briefing Trigger (Sent at 07:00 AM Thai Time)
            if now_thai.hour >= 7 and alerted_morning_briefing_day != today_thai_str:
                send_discord_morning_news_briefing(webhook_url, gemini_key, state)
                alerted_morning_briefing_day = today_thai_str

            # 4. Check for New Open Orders to Alert Discord
            for order in open_orders:
                ticket = order.get("ticket", 0)
                if ticket not in known_tickets:
                    known_tickets.add(ticket)
                    send_discord_order_opened_alert(webhook_url, order, state, gemini_key)

            # 5. Check Jackpot Lock Trigger
            if jackpot_locked and alerted_jackpot_day != current_day:
                send_discord_jackpot_lock_alert(webhook_url, state)
                alerted_jackpot_day = current_day

            # 6. Periodic Heartbeat Report (Aligned at :00 and :30, ONLY when NO open orders)
            enable_heartbeat = config.get("enable_periodic_heartbeat", True)
            if enable_heartbeat:
                cur_min = now_thai.minute
                # Trigger at minute 0 and minute 30
                if cur_min in [0, 30] and last_heartbeat_mark != cur_min:
                    if len(open_orders) == 0:
                        send_discord_heartbeat_report(webhook_url, state)
                    else:
                        safe_print("\\n    [⏳ HEARTBEAT SKIPPED] Positions currently open. Muting heartbeat report.")
                    last_heartbeat_mark = cur_min
                elif cur_min not in [0, 30]:
                    last_heartbeat_mark = -1

            # 7. Print Real-Time Console Status Line
            time_disp = server_time_str[-8:] if len(server_time_str) >= 8 else server_time_str
            sentinel_disp = "🔴 NEWS PAUSE" if is_stand_down else "🟢 CLEAR"
            jackpot_disp = "🔒 JACKPOT LOCK" if jackpot_locked else "READY"

            status_line = (f"[{time_disp}] Gold: ${state.get('bid', 0):.2f} | "
                           f"Eq: ${equity:,.2f} | "
                           f"PnL: {daily_pnl_pct:+.1f}% (${daily_pnl:+.2f}) | "
                           f"SniperPnL: ${sniper_pnl:+.2f} | "
                           f"Trades: {daily_trades} | "
                           f"Sentinel: {sentinel_disp} | "
                           f"Status: {jackpot_disp}   ")
            print(status_line, end="\\r", flush=True)

            time.sleep(1)

        except Exception as e:
            safe_print(f"\\n    [Agent Loop Exception] {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
"""

code = code[:main_start] + new_main

with open(agent_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully replaced main() with clean robust loop!")
