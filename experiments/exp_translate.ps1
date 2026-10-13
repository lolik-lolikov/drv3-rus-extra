# ОПЫТ 2: наложить перевод доп. режимов (и шрифт с кириллицей) на распакованные файлы
param([string]$GamePath = "", [string]$Payload = "", [switch]$NoFont)
. (Join-Path $PSScriptRoot "common.ps1")
if (-not $Payload) { $Payload = Join-Path (Split-Path -Parent $PSScriptRoot) "pkg\payload" }
Write-Host "Папка игры: $GamePath"
Write-Host "Перевод: $Payload"
Check-NotRunning
foreach ($k in $archNames.Keys) {
    if (Test-Path -LiteralPath (Join-Path $win $archNames[$k])) { Write-Host "Внимание: архив $($archNames[$k]) лежит в data\win — игра не увидит перевод." -ForegroundColor Yellow }
}
$created = @{}
if (Test-Path -LiteralPath $createdList) { foreach ($l in [IO.File]::ReadAllLines($createdList, $utf8)) { if ($l) { $created[$l] = 1 } } }
# оглавления архивов (для поиска файлов по имени и чтения оригиналов)
$entries = @(); $byPath = @{}
foreach ($k in @("us", "res")) {
    $a = Arch-Path $k
    if (-not $a) { Write-Host "Не найден архив $($archNames[$k]) ни в data\win, ни в _drv3_exp\cpk" -ForegroundColor Red; Done 2 }
    $c = [Cpk]::Open($a)
    foreach ($e in $c.Entries) { $entries += $e; $byPath[$e.Path] = $e }
}
function Resolve-Targets($target) {
    $res = @()
    if ($target.StartsWith("BYNAME:")) {
        $parts = $target.Substring(7) -split "/"
        $name = $parts[-1]
        $parent = $(if ($parts.Count -gt 1) { ($parts[0..($parts.Count - 2)] -join "/") } else { "" })
        foreach ($e in $entries) {
            if ($e.Name -ieq $name -and (-not $parent -or $e.Dir -ieq $parent -or ("" + $e.Dir).ToLowerInvariant().EndsWith("/" + $parent.ToLowerInvariant()))) { $res += $e.Path }
        }
        return $res
    }
    $rel = $target -replace "^data/win/", ""
    if ($byPath.ContainsKey($rel)) { $res += $byPath[$rel].Path }
    return $res
}
$tl = Join-Path $exp "translated.txt"
$lw = New-Object IO.StreamWriter($tl, $true, $utf8); $lw.AutoFlush = $true
$ok = 0; $already = 0; $skipped = @(); $notCreated = 0
$lines = @([IO.File]::ReadAllLines((Join-Path $Payload "manifest.txt"), $utf8) | Where-Object { $_ })
$i = 0
foreach ($line in $lines) {
    $i++
    $kind, $file, $target = $line -split "`t"
    if ($NoFont -and $kind -eq "PATCHA") { $skipped += "$target (шрифт отключён ключом -NoFont)"; continue }
    $pf = Join-Path $Payload ($file -replace "/", "\")
    $targets = @(Resolve-Targets $target)
    if ($targets.Count -eq 0) { $skipped += "$target (нет в архивах)"; continue }
    $pbytes = [IO.File]::ReadAllBytes($pf)
    foreach ($t in $targets) {
        $full = Win-Path $t
        if (-not [IO.File]::Exists($full)) { $skipped += "$t (не распакован)"; continue }
        if (-not $created.ContainsKey($t)) { $notCreated++ }
        if ($kind -eq "FULL") { $data = $pbytes }
        else {
            $cur = [IO.File]::ReadAllBytes($full)
            if ([DrvPatch]::Sha1($cur) -eq [DrvPatch]::NewSha($pbytes)) { $already++; continue }
            $data = [DrvPatch]::Apply($cur, $pbytes)
            if ($null -eq $data) { $data = [DrvPatch]::Apply($byPath[$t].Owner.Read($byPath[$t]), $pbytes) }
            if ($null -eq $data) { $skipped += "$t (версия файла отличается)"; continue }
        }
        $tmp = $full + ".rus_tmp"
        [IO.File]::WriteAllBytes($tmp, $data)
        Move-Item -LiteralPath $tmp -Destination $full -Force
        $lw.WriteLine("$kind`t$t")
        $ok++
        Write-Host ("[{0}/{1}] {2} {3}" -f $i, $lines.Count, $kind, $t)
    }
}
$lw.Close()
foreach ($e in $entries) { $e.Owner.Dispose() }
Write-Host ""
Write-Host "Установлено файлов: $ok"
if ($already) { Write-Host "Уже были установлены: $already" }
if ($notCreated) { Write-Host "Внимание: $notCreated файлов не из списка распакованных — откат их не удалит." -ForegroundColor Yellow }
if ($skipped.Count) { Write-Host "Пропущено: $($skipped.Count)" -ForegroundColor Yellow; $skipped | ForEach-Object { Write-Host "   $_" } }
Done 0
