# ОПЫТ: распаковать архивы _us (и resident) в data\win и убрать их в резервную копию _drv3_exp\cpk
param([string]$GamePath = "", [string]$Which = "us,res", [switch]$KeepArchives)
. (Join-Path $PSScriptRoot "common.ps1")
Write-Host "Папка игры: $GamePath"
Check-NotRunning
$keys = $Which -split ","
$cpks = @()
foreach ($k in $keys) {
    $p = Join-Path $win $archNames[$k]
    if (-not (Test-Path -LiteralPath $p)) { Write-Host "Нет архива $($archNames[$k]) в data\win" -ForegroundColor Red; Done 2 }
    $cpks += [Cpk]::Open($p)
}
$jobs = @(); $total = 0
foreach ($c in $cpks) { foreach ($e in $c.Entries) { $jobs += $e; $total += $e.Size } }
Write-Host ("Файлов: {0}, объём: {1} ГБ" -f $jobs.Count, (Gb $total))
$exist = @($jobs | Where-Object { [IO.File]::Exists((Win-Path $_.Path)) })
if ($exist.Count) {
    Write-Host "В data\win уже есть $($exist.Count) файлов из архивов, например:" -ForegroundColor Red
    $exist | Select-Object -First 10 | ForEach-Object { Write-Host "   $($_.Path)" }
    Write-Host "Сначала запустите откат (rollback)."
    Done 3
}
$free = (New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($GamePath))).AvailableFreeSpace
Write-Host ("Свободно на диске: {0} ГБ" -f (Gb $free))
if ($free -lt $total + 1GB) { Write-Host "Недостаточно места." -ForegroundColor Red; Done 5 }

New-Item -ItemType Directory -Force -Path $exp | Out-Null
$lw = New-Object IO.StreamWriter($createdList, $true, $utf8); $lw.AutoFlush = $true
$buf = New-Object byte[] (4MB)
$sw = [Diagnostics.Stopwatch]::StartNew()
$done = 0; $i = 0; $nextPct = 10
try {
    foreach ($e in $jobs) {
        $i++
        $e.Owner.Extract($e, (Win-Path $e.Path), $buf)
        $lw.WriteLine($e.Path)
        $done += $e.Size
        $pct = [int](100 * $done / $total)
        if ($i % 10 -eq 0 -or $i -eq $jobs.Count) {
            $mbs = $done / 1MB / [Math]::Max($sw.Elapsed.TotalSeconds, 0.001)
            Write-Progress -Activity "Распаковка архивов" -Status ("{0} из {1} ГБ ({2}%), {3:N0} МБ/с" -f (Gb $done), (Gb $total), $pct, $mbs) -PercentComplete $pct
        }
        if ($pct -ge $nextPct) { Write-Host ("  {0}%  {1} из {2} ГБ, {3:N0} с" -f $pct, (Gb $done), (Gb $total), $sw.Elapsed.TotalSeconds); $nextPct += 10 }
    }
} catch {
    $lw.Close()
    Write-Host "ОШИБКА распаковки: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Запустите rollback.bat, чтобы убрать распакованное."
    Done 6
}
$lw.Close()
foreach ($c in $cpks) { $c.Dispose() }
Write-Progress -Activity "Распаковка архивов" -Completed
Write-Host ("Распаковано {0} файлов за {1:N0} с" -f $jobs.Count, $sw.Elapsed.TotalSeconds)
if (-not $KeepArchives) {
    New-Item -ItemType Directory -Force -Path $expCpk | Out-Null
    foreach ($c in $cpks) {
        Move-Item -LiteralPath $c.FilePath -Destination (Join-Path $expCpk (Split-Path -Leaf $c.FilePath))
        Write-Host "Архив перенесён в резервную копию: $(Split-Path -Leaf $c.FilePath)"
    }
}
Done 0
