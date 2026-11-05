import subprocess
import os
import json
import sys

def run_cmd(cmd):
    try:
        res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return res.decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8', errors='ignore')

print("============================================================")
print("  PC PERFORMANCE & RESOURCE DIAGNOSTICS REPORT")
print("============================================================")

# 1. System Memory (via WMIC / CimInstance)
ps_script = """
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
$proc = Get-CimInstance Win32_Processor

$totalRam = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
$freeRam  = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
$usedRam  = [math]::Round($totalRam - $freeRam, 2)
$pct      = [math]::Round(($usedRam / $totalRam) * 100, 1)

[PSCustomObject]@{
    CPU = $proc.Name
    Cores = $proc.NumberOfCores
    Threads = $proc.NumberOfLogicalProcessors
    TotalRAM_GB = $totalRam
    UsedRAM_GB = $usedRam
    FreeRAM_GB = $freeRam
    RAM_Usage_Pct = $pct
} | ConvertTo-Json
"""

with open("sys_check.ps1", "w", encoding="utf-8") as f:
    f.write(ps_script)

res = run_cmd("powershell -ExecutionPolicy Bypass -File sys_check.ps1")
try:
    data = json.loads(res)
    print(f"* CPU Model:       {data.get('CPU')}")
    print(f"* Cores / Threads: {data.get('Cores')} Cores / {data.get('Threads')} Threads")
    print(f"* Total RAM:       {data.get('TotalRAM_GB')} GB")
    print(f"* Used RAM:        {data.get('UsedRAM_GB')} GB ({data.get('RAM_Usage_Pct')}%)")
    print(f"* Available RAM:   {data.get('FreeRAM_GB')} GB")
except Exception as e:
    print(res)

if os.path.exists("sys_check.ps1"):
    os.remove("sys_check.ps1")

# 2. Disk Storage Check
print("\n--- DISK DRIVES & FREE SPACE ---")
ps_disk = """
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    [PSCustomObject]@{
        Drive = $_.DeviceID
        Total_GB = [math]::Round($_.Size / 1GB, 1)
        Free_GB = [math]::Round($_.FreeSpace / 1GB, 1)
        Used_GB = [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 1)
        Free_Pct = [math]::Round(($_.FreeSpace / $_.Size) * 100, 1)
    }
} | ConvertTo-Json
"""
with open("disk_check.ps1", "w", encoding="utf-8") as f:
    f.write(ps_disk)
res_disk = run_cmd("powershell -ExecutionPolicy Bypass -File disk_check.ps1")
try:
    d_data = json.loads(res_disk)
    if isinstance(d_data, dict):
        d_data = [d_data]
    for d in d_data:
        print(f"* Drive {d['Drive']} : Total {d['Total_GB']} GB | Free {d['Free_GB']} GB ({d['Free_Pct']}% free) | Used {d['Used_GB']} GB")
except Exception as e:
    print(res_disk)
if os.path.exists("disk_check.ps1"):
    os.remove("disk_check.ps1")

# 3. Top 15 RAM Hogging Processes
print("\n--- TOP 15 RAM-CONSUMING PROCESSES ---")
ps_top_ram = """
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15 | ForEach-Object {
    [PSCustomObject]@{
        Id = $_.Id
        ProcessName = $_.ProcessName
        RAM_MB = [math]::Round($_.WorkingSet64 / 1MB, 1)
        CPU_Sec = [math]::Round($_.CPU, 1)
    }
} | ConvertTo-Json
"""
with open("ram_check.ps1", "w", encoding="utf-8") as f:
    f.write(ps_top_ram)
res_ram = run_cmd("powershell -ExecutionPolicy Bypass -File ram_check.ps1")
try:
    r_data = json.loads(res_ram)
    for idx, p in enumerate(r_data, 1):
        print(f"{idx:2d}. {p['ProcessName']:25} (PID: {p['Id']:6d}) -> RAM: {p['RAM_MB']:8.1f} MB | CPU Time: {p['CPU_Sec']}s")
except Exception as e:
    print(res_ram)
if os.path.exists("ram_check.ps1"):
    os.remove("ram_check.ps1")

# 4. Check for Orphaned / Multiple Background Trading Processes
print("\n--- TRADING & BACKGROUND INSTANCES AUDIT ---")
ps_trading = """
Get-Process | Where-Object { $_.ProcessName -match "terminal|python|cmd|powershell|metaeditor" } | ForEach-Object {
    [PSCustomObject]@{
        Id = $_.Id
        ProcessName = $_.ProcessName
        RAM_MB = [math]::Round($_.WorkingSet64 / 1MB, 1)
        CPU_Sec = [math]::Round($_.CPU, 1)
    }
} | ConvertTo-Json
"""
with open("trading_check.ps1", "w", encoding="utf-8") as f:
    f.write(ps_trading)
res_tr = run_cmd("powershell -ExecutionPolicy Bypass -File trading_check.ps1")
try:
    t_data = json.loads(res_tr)
    if isinstance(t_data, dict):
        t_data = [t_data]
    for p in t_data:
        print(f"* {p['ProcessName']:15} PID: {p['Id']:6d} | RAM: {p['RAM_MB']:7.1f} MB | CPU: {p['CPU_Sec']}s")
except Exception as e:
    print(res_tr)
if os.path.exists("trading_check.ps1"):
    os.remove("trading_check.ps1")

print("\n" + "="*60)
