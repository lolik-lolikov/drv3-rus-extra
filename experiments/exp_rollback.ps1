# ОТКАТ опытов: удалить распакованные файлы (только из списка created.txt) и вернуть архивы
param([string]$GamePath = "")
. (Join-Path $PSScriptRoot "common.ps1")
Write-Host "Папка игры: $GamePath"
Check-NotRunning
$n = 0; $dirs = @{}
if (Test-Path -LiteralPath $createdList) {
    $lines = [IO.File]::ReadAllLines($createdList, $utf8)
    $i = 0
    foreach ($rel in $lines) {
        $i++
        if (-not $rel) { continue }
        $p = Win-Path $rel
        if ([IO.File]::Exists($p)) { [IO.File]::Delete($p); $n++ }
        $d = [IO.Path]::GetDirectoryName($p)
        while ($d -and $d.Length -gt $win.Length) { $dirs[$d] = 1; $d = [IO.Path]::GetDirectoryName($d) }
        if ($i % 50 -eq 0) { Write-Progress -Activity "Удаление распакованных файлов" -Status "$i из $($lines.Count)" -PercentComplete (100 * $i / $lines.Count) }
    }
    Write-Progress -Activity "Удаление распакованных файлов" -Completed
}
Write-Host "Удалено файлов: $n"
foreach ($d in ($dirs.Keys | Sort-Object -Property Length -Descending)) {
    if ([IO.Directory]::Exists($d) -and -not [IO.Directory]::EnumerateFileSystemEntries($d).GetEnumerator().MoveNext()) { [IO.Directory]::Delete($d) }
}
foreach ($k in $archNames.Keys) {
    $src = Join-Path $expCpk $archNames[$k]; $dst = Join-Path $win $archNames[$k]
    if (Test-Path -LiteralPath $src) {
        if (Test-Path -LiteralPath $dst) { Write-Host "В data\win уже есть $($archNames[$k]) — резервная копия оставлена в $expCpk" -ForegroundColor Yellow }
        else { Move-Item -LiteralPath $src -Destination $dst; Write-Host "Архив возвращён: $($archNames[$k])" }
    }
}
if (Test-Path -LiteralPath $createdList) { Remove-Item -LiteralPath $createdList }
foreach ($f in @("translated.txt")) { $p = Join-Path $exp $f; if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p } }
if ((Test-Path -LiteralPath $expCpk) -and -not (Get-ChildItem -LiteralPath $expCpk -Force)) { Remove-Item -LiteralPath $expCpk }
if ((Test-Path -LiteralPath $exp) -and -not (Get-ChildItem -LiteralPath $exp -Force)) { Remove-Item -LiteralPath $exp }
$left = @(Get-ChildItem -LiteralPath $win -Force | Where-Object { $_.Name -notlike "*.cpk" })
if ($left.Count) { Write-Host "В data\win остались посторонние элементы:" -ForegroundColor Yellow; $left | ForEach-Object { Write-Host "   $($_.Name)" } }
Get-ChildItem -LiteralPath $win -Filter *.cpk | ForEach-Object { Write-Host ("  {0}  {1:N0} байт" -f $_.Name, $_.Length) }
Done 0
