# EA-XAUUSD

> **Institutional-Grade Quantitative Automated Trading System for Gold (XAUUSD)**  
> Powered by Dual-Engine MetaTrader 4 Architecture & Python AI Sentinel (5-Sciences Quant Confluence).

---

## 🌟 Overview

**EA-XAUUSD (Gold POI Sniper v3.5)** is a hybrid quantitative trading ecosystem designed specifically for the extreme volatility and liquidity dynamics of Gold (XAUUSD). The system fuses deterministic algorithmic execution inside MetaTrader 4 with probabilistic macro intelligence and multi-model quantitative analytics in Python.

### 🏛️ Core Engines

1. **Engine A: London Sniper Runner (Magic `778832`)**
   - **Session Window:** 08:00 – 11:30 Server Time (13:00 – 16:30 Thai Time).
   - **Strategy:** Asian Box Breakout Runner with Relative Volume (RVOL >= 1.1x), M15 candle close confirmation, rejection wick filtering (< 40%), and EMA 50/200 structural alignment.
   - **Target:** 1:3.50+ R:R with dynamic trailing ratchet and sunset profit locking.

2. **Engine B: Judas Sweep Fade (Magic `778834`)**
   - **Session Window:** 08:00 – 11:30 Server Time.
   - **Strategy:** Contrarian Liquidity Trap Hunter. Capitalizes on institutional stop-runs (Judas Swings) beyond the Asian High/Low that fail and re-enter the range with pinbar rejection wicks (>= 40%).
   - **Target:** Asymmetric 1:5.00 R:R with 2-tier partial take-profit (+1.50R).

3. **Engine C: New York POI Prime (Magic `778899`)**
   - **Session Window:** 15:00 – 20:30 Server Time (20:00 – 01:30 Thai Time).
   - **Strategy:** Institutional Points of Interest (POI) targeting Order Blocks, Fair Value Gaps (FVG), and liquidity pools.

4. **Python AI Sentinel & 5-Sciences Quant Briefing**
   - Real-time Macro News Radar & Stand-Down Shield.
   - 24/7 Bayesian Conditional Probability Engine ($P(\text{Pullback})$ vs $P(\text{Runaway})$ based on historical distributions).
   - Multi-room Discord Webhook Dispatcher delivering automated institutional briefings every 3 hours.

---

## 📁 Repository Structure

```text
EA-XAUUSD/
├── Gold_POI_Sniper_Master_v3_5.mq4    # Master Live Production EA for MT4
├── Gold_POI_Sniper_Tester_v3_5.mq4    # High-Performance Strategy Tester EA
├── gold_ai_agent_poi_v3_5.py          # Python AI Co-Pilot & 5-Sciences Quant Agent
├── base_agent.py                      # Core Agent Library (Webhooks, Calculations, News)
├── config.example.json                # Configuration Template (Copy to config.json)
├── macro_event_playbook.json          # Institutional Macro Event Rulebook
├── run_agent_poi_v3_5.bat             # Batch launcher for AI Agent
├── .gitignore                         # Security rules to prevent credentials leakage
└── README.md                          # Project Documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **MetaTrader 4 Terminal** (Build 1420+)
- **Python 3.10+** (with standard libraries: `urllib`, `json`, `datetime`, `math`, `os`, `re`)

### 2. Configuration Setup
1. Copy the example configuration file:
   ```bash
   cp config.example.json config.json
   ```
2. Open `config.json` and configure your local MT4 path, Discord Webhooks, and API keys:
   ```json
   {
     "system_version": "Gold POI Sniper v3.5",
     "mt4_files_dir": "C:/Users/<Username>/AppData/Roaming/MetaQuotes/Terminal/<Instance>/MQL4/Files",
     "symbol": "GOLD",
     "discord_webhook_morning_briefing": "YOUR_WEBHOOK_URL",
     "gemini_api_key": "YOUR_API_KEY"
   }
   ```
   *(Note: `config.json` is protected by `.gitignore` and must never be committed to public repositories).*

### 3. Deploy to MT4
1. Place `Gold_POI_Sniper_Master_v3_5.mq4` into your MT4 directory:
   `MQL4/Experts/`
2. Compile inside MetaEditor.
3. Attach to **GOLD / XAUUSD** on the **M15** timeframe.
4. Enable **"Allow live trading"** and **"Allow DLL imports"** (if applicable).

### 4. Launch the AI Sentinel
Run the batch launcher:
```bat
run_agent_poi_v3_5.bat
```
Or start via Python:
```bash
python -u gold_ai_agent_poi_v3_5.py
```

---

## 🔒 Security & Privacy Notice
All sensitive keys, personal webhook URLs, local directory paths, broker account details, and private runtime logs are strictly quarantined in local ignored files (`config.json`, `.env`). The master repository contains only clean, auditable source code and templates.

---

## ⚖️ License
Proprietary Quantitative Trading Software. All rights reserved.
