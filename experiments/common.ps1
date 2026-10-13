# Общие функции для опытов (подключается через точку)
$ErrorActionPreference = "Stop"
if (-not $GamePath) { $GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Danganronpa V3 Killing Harmony" }
Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PSScriptRoot "cpklib.cs")))
$win = Join-Path $GamePath "data\win"
$exp = Join-Path $GamePath "_drv3_exp"
$expCpk = Join-Path $exp "cpk"
$createdList = Join-Path $exp "created.txt"
$archNames = @{ us = "partition_data_win_us.cpk"; res = "partition_resident_win.cpk" }
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Done($code) { Write-Host ""; if ($code -eq 0) { Write-Host "ГОТОВО." -ForegroundColor Green } else { Write-Host "ОШИБКА, код $code" -ForegroundColor Red }; exit $code }
function Check-NotRunning {
    if (Get-Process -Name "Dangan3Win" -ErrorAction SilentlyContinue) { Write-Host "Игра запущена — закройте её и повторите." -ForegroundColor Red; Done 4 }
}
function Win-Path($rel) { return [IO.Path]::Combine($win, ($rel -replace "/", [IO.Path]::DirectorySeparatorChar)) }
function Gb($b) { return ("{0:N2}" -f ($b / 1GB)) }
# путь к архиву: в data\win или в резервной копии опыта
function Arch-Path($key) {
    $a = Join-Path $win $archNames[$key]
    if (Test-Path -LiteralPath $a) { return $a }
    $b = Join-Path $expCpk $archNames[$key]
    if (Test-Path -LiteralPath $b) { return $b }
    return $null
}
