
Get-Counter '\Process(*)\% Processor Time' | Select-Object -ExpandProperty CounterSamples | Where-Object { .CookedValue -gt 1 -and .InstanceName -notmatch '^_total|idle' } | Sort-Object CookedValue -Descending | Select-Object -First 8 | ForEach-Object {
    [PSCustomObject]@{
        Name = .InstanceName
        CPU_Pct = [math]::Round(.CookedValue / [Environment]::ProcessorCount, 1)
    }
} | ConvertTo-Json
