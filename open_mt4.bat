@echo off
taskkill /F /IM terminal.exe >nul 2>&1
start "" "C:\Program Files (x86)\MetaTrader 4\terminal.exe"
exit
