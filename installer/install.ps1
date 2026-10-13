# Русификатор дополнительных режимов Danganronpa V3: Killing Harmony
# Установка / удаление / поиск игры. Вызывается из установщика (Setup.exe) или вручную.
#
# Режимы установки (выбираются автоматически):
#   UNPACK — основного русификатора нет (чистая игра из Steam): все файлы архивов
#            partition_data_win_us.cpk и partition_resident_win.cpk распаковываются в data\win
#            (около 10 ГБ), поверх накладывается перевод и шрифт с кириллицей, а сами архивы
#            переносятся в _rus_extra_backup\cpk. Пока эти архивы лежат в data\win, игра
#            читает файлы только из них, поэтому другого способа нет: правка архивов ломает игру.
#   LOOSE  — основной русификатор установлен (его файлы уже лежат в data\win): патчатся
#            распакованные файлы (оригиналы — в резервную копию); если архивы _us и resident
#            ещё не убраны, а все их файлы распакованы, архивы переносятся в резервную копию.
#
# Журнал установки _rus_extra_backup\installed.txt (пишется по ходу, поэтому откат работает
# даже после сбоя). Строки: <тип><TAB><путь от папки игры>
#   MODE  UNPACK|LOOSE    режим
#   X     data\win\...    файл создан распаковкой — при удалении стирается
#   P     data\win\...    файл лежал в data\win до установки — перенесён в _rus_extra_backup\data\win\...
#   R     data\win\...    файл изменён переводом — копия оригинала в _rus_extra_backup\data\win\...
#   T     data\win\...    файл переведён
#   M     data\win\*.cpk  архив перенесён в _rus_extra_backup\cpk\
# Формат совместим с журналами версий 1.x (R и M).
param([switch]$Uninstall, [switch]$DetectOnly, [switch]$NoPause, [string]$GamePath = "", [string]$Payload = "",
      [string]$Log = "", [string]$Status = "", [string]$OutFile = "", [string]$Version = "",
      [double]$TestFreeSpace = -1, [int]$TestFailAt = 0)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Payload) { $Payload = Join-Path $here "payload" }
$backupName = "_rus_extra_backup"
$usName = "partition_data_win_us.cpk"
$resName = "partition_resident_win.cpk"
$archives = @($usName, $resName)
$utf8 = New-Object System.Text.UTF8Encoding($false)
$sep = [IO.Path]::DirectorySeparatorChar

function Say($t) {
    Write-Host $t
    if ($Log) {
        for ($k = 0; $k -lt 20; $k++) {
            try { [IO.File]::AppendAllText($Log, $t + "`r`n", [Text.Encoding]::Unicode); break } catch { Start-Sleep -Milliseconds 50 }
        }
    }
}
$script:lastPct = -1; $script:lastT = [DateTime]::MinValue
# ход работы для окна установщика: файл status (строка 1 — проценты, строка 2 — текст)
function Progress($pct, $text, [switch]$Force) {
    $now = [DateTime]::UtcNow
    if (-not $Force -and $pct -eq $script:lastPct -and ($now - $script:lastT).TotalMilliseconds -lt 400) { return }
    $script:lastPct = $pct; $script:lastT = $now
    if ($Status) { try { [IO.File]::WriteAllText($Status, "$pct`r`n$text`r`n", [Text.Encoding]::Unicode) } catch {} }
    elseif ($NoPause) { } else { Write-Progress -Activity "Русификатор доп. режимов" -Status $text -PercentComplete $pct }
}
function Finish($code) {
    if (-not $NoPause) { Write-Host ""; Read-Host "Нажмите Enter, чтобы закрыть окно" | Out-Null }
    exit $code
}
function Gb($b) { return ("{0:N1}" -f ($b / 1GB)) }

function Test-Game($p) {
    if (-not $p) { return $false }
    return (Test-Path -LiteralPath (Join-Path $p "data\win")) -and ((Test-Path -LiteralPath (Join-Path $p "Dangan3Win.exe")) -or (Test-Path -LiteralPath (Join-Path $p "data\win\partition_data_win.cpk")))
}

function Find-Game {
    $cands = @()
    $d = $here
    for ($i = 0; $i -lt 4 -and $d; $i++) { $cands += $d; $d = Split-Path -Parent $d }
    $steamRoots = @()
    foreach ($k in @("HKCU:\Software\Valve\Steam", "HKLM:\SOFTWARE\WOW6432Node\Valve\Steam", "HKLM:\SOFTWARE\Valve\Steam")) {
        try {
            $v = Get-ItemProperty -Path $k -ErrorAction Stop
            if ($v.SteamPath) { $steamRoots += ($v.SteamPath -replace "/", "\") }
            if ($v.InstallPath) { $steamRoots += $v.InstallPath }
        } catch {}
    }
    $steamRoots += "C:\Program Files (x86)\Steam", "C:\Program Files\Steam"
    foreach ($drv in (Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
        $steamRoots += (Join-Path $drv.Root "SteamLibrary"), (Join-Path $drv.Root "Steam"), (Join-Path $drv.Root "Games\Steam")
    }
    $libs = @()
    foreach ($r in ($steamRoots | Select-Object -Unique)) {
        $libs += $r
        $vdf = Join-Path $r "steamapps\libraryfolders.vdf"
        if (Test-Path -LiteralPath $vdf) {
            foreach ($m in [regex]::Matches((Get-Content -LiteralPath $vdf -Raw), '"path"\s+"([^"]+)"')) { $libs += ($m.Groups[1].Value -replace "\\\\", "\") }
        }
    }
    foreach ($l in ($libs | Select-Object -Unique)) { $cands += (Join-Path $l "steamapps\common\Danganronpa V3 Killing Harmony") }
    foreach ($c in $cands) { if (Test-Game $c) { return (Resolve-Path -LiteralPath $c).Path } }
    return $null
}

if ($DetectOnly) {
    $g = Find-Game
    if ($OutFile) { if ($g) { [IO.File]::WriteAllText($OutFile, $g, [Text.Encoding]::Unicode) } }
    elseif ($g) { [Console]::Out.Write($g) }
    exit 0
}

# ---------------- чтение архивов CPK и патчи (C#, см. installer/cpklib.cs) ----------------
Add-Type -TypeDefinition @'
#CPKLIB#
'@

if (-not (Test-Game $GamePath)) { $GamePath = Find-Game }
if (-not (Test-Game $GamePath)) { Say "ОШИБКА: папка игры не найдена или указана неверно."; Finish 2 }
$GamePath = (Resolve-Path -LiteralPath $GamePath).Path.TrimEnd("\", "/")
Say "Папка игры: $GamePath"
$backup = Join-Path $GamePath $backupName
$listPath = Join-Path $backup "installed.txt"

# путь от папки игры ("data\win\..." или "data/win/...") -> полный путь
function Full($rel) { return [IO.Path]::Combine($GamePath, ($rel -replace '[\\/]', $sep)) }
function Bak($rel) { return [IO.Path]::Combine($backup, ($rel -replace '[\\/]', $sep)) }
$win = Full "data\win"
# путь внутри архива (через "/") -> путь от папки игры
function WinRel($p) { return "data\win\" + ($p -replace "/", "\") }

function Read-List {
    if (-not (Test-Path -LiteralPath $listPath)) { return @() }
    return @([IO.File]::ReadAllLines($listPath, $utf8) | Where-Object { $_ })
}
$script:jw = $null
function J($kind, $rel) {
    if (-not $script:jw) {
        [void][IO.Directory]::CreateDirectory($backup)
        $script:jw = New-Object IO.StreamWriter($listPath, $true, $utf8)
        $script:jw.AutoFlush = $true
    }
    $script:jw.WriteLine("$kind`t$rel")
}
function J-Close { if ($script:jw) { $script:jw.Close(); $script:jw = $null } }
function Ensure-Dir($file) { $d = [IO.Path]::GetDirectoryName($file); if ($d) { [void][IO.Directory]::CreateDirectory($d) } }

# ---------------- удаление (и откат предыдущей версии перед новой установкой) ----------------
function Undo-Install {
    $lines = @(Read-List)
    if ($lines.Count -eq 0) { return $false }
    J-Close
    $listX = New-Object System.Collections.ArrayList; $listP = @(); $listR = @(); $listM = @(); $nC = 0
    foreach ($line in $lines) {
        $f = $line -split "`t"
        switch ($f[0]) { "X" { [void]$listX.Add($f[1]) } "P" { $listP += $f[1] } "R" { $listR += $f[1] } "M" { $listM += $f[1] } "C" { $nC++ } }
    }
    # 1. оригиналы файлов, изменённых поверх основного русификатора
    $n = 0
    foreach ($rel in ($listR | Select-Object -Unique)) {
        $src = Bak $rel
        if ([IO.File]::Exists($src)) { Copy-Item -LiteralPath $src -Destination (Full $rel) -Force; $n++ }
    }
    if ($n) { Say "Восстановлено оригинальных файлов: $n." }
    # 2. архивы — раньше удаления распакованных файлов: так игра цела на любом шаге
    foreach ($rel in ($listM | Select-Object -Unique)) {
        $leaf = Split-Path -Leaf ($rel -replace '[\\/]', $sep)
        $src = Join-Path $backup ("cpk" + $sep + $leaf)
        $dst = Full $rel
        if (Test-Path -LiteralPath $src) {
            if (Test-Path -LiteralPath $dst) { Say "Архив $leaf уже восстановлен Steam — старая копия больше не нужна." }
            else { Move-Item -LiteralPath $src -Destination $dst; Say "Возвращён архив: $leaf" }
        }
    }
    # 3. файлы, созданные распаковкой
    if ($listX.Count) {
        $dirs = @{}; $i = 0; $del = 0
        foreach ($rel in $listX) {
            $i++
            $fp = Full $rel
            if ([IO.File]::Exists($fp)) { [IO.File]::Delete($fp); $del++ }
            $d = [IO.Path]::GetDirectoryName($fp)
            while ($d -and $d.Length -gt $win.Length) { $dirs[$d] = 1; $d = [IO.Path]::GetDirectoryName($d) }
            if ($i % 25 -eq 0) { Progress ([int](90 * $i / $listX.Count)) ("Удаление распакованных файлов: {0} из {1}" -f $i, $listX.Count) }
        }
        Say "Удалено распакованных файлов: $del."
        # 4. файлы, лежавшие в data\win до установки
        foreach ($rel in ($listP | Select-Object -Unique)) {
            $src = Bak $rel; $dst = Full $rel
            if ([IO.File]::Exists($src) -and -not [IO.File]::Exists($dst)) { Ensure-Dir $dst; Move-Item -LiteralPath $src -Destination $dst }
        }
        # 5. опустевшие папки
        foreach ($d in ($dirs.Keys | Sort-Object -Property Length -Descending)) {
            if ([IO.Directory]::Exists($d) -and -not ([IO.Directory]::EnumerateFileSystemEntries($d) | Select-Object -First 1)) { [IO.Directory]::Delete($d) }
        }
    }
    if ($nC) { Say "Внимание: архивы игры изменялись версией 2.0. Проверьте целостность файлов игры в Steam (Свойства → Установленные файлы)." }
    Remove-Item -LiteralPath $backup -Recurse -Force
    return $true
}

if (Get-Process -Name "Dangan3Win" -ErrorAction SilentlyContinue) { Say "ОШИБКА: игра запущена. Закройте её и повторите."; Finish 4 }

if ($Uninstall) {
    Progress 0 "Восстановление файлов игры..." -Force
    if (-not (Undo-Install)) { Say "Резервная копия не найдена — русификатор не установлен."; Finish 1 }
    Progress 100 "Готово" -Force
    Say "Игра возвращена в исходное состояние."
    Finish 0
}

# ---------------- установка ----------------
$man = Join-Path $Payload "manifest.txt"
if (-not (Test-Path -LiteralPath $man)) { Say "ОШИБКА: не найдены файлы перевода (payload\manifest.txt)."; Finish 3 }

if (-not (Test-Path -LiteralPath (Full "data\win\partition_data_win.cpk"))) {
    Say "ОШИБКА: в data\win нет файла partition_data_win.cpk — без него игра не запускается."
    if (Get-ChildItem -LiteralPath $win -Filter "*.arc" -ErrorAction SilentlyContinue) {
        Say "В папке лежат файлы .arc — это Anniversary Edition, перевод для неё не подходит."
    } else {
        Say "Верните его: Steam → ПКМ по игре → Свойства → Установленные файлы → «Проверить целостность файлов игры»,"
        Say "затем запустите установщик ещё раз."
    }
    Finish 5
}

# предыдущая установка: если игра распакована нашей прошлой версией — только обновляем перевод
$prev = @(Read-List)
$update = $false
if ($prev.Count) {
    $prevMode = ""; $prevM = @()
    foreach ($l in $prev) { $f = $l -split "`t"; if ($f[0] -eq "MODE") { $prevMode = $f[1] }; if ($f[0] -eq "M") { $prevM += (Split-Path -Leaf ($f[1] -replace '[\\/]', $sep)) } }
    $update = ($prevMode -eq "UNPACK") -and ($prevM.Count -gt 0)
    foreach ($a in $prevM) {
        if (-not (Test-Path -LiteralPath (Join-Path $backup ("cpk" + $sep + $a)))) { $update = $false }
        if (Test-Path -LiteralPath (Full ("data\win\" + $a))) { $update = $false }
    }
    if ($update) {
        Say "Найдена предыдущая установка — обновляется только перевод (распакованные файлы остаются)."
        # журнал без старых строк T (они будут записаны заново)
        [IO.File]::WriteAllLines($listPath, [string[]]@($prev | Where-Object { -not $_.StartsWith("T`t") }), $utf8)
    } else {
        Say "Найдена предыдущая установка перевода — она будет удалена и установлена заново."
        Undo-Install | Out-Null
        $prev = @()
    }
}

# архивы: в data\win или (после прошлой установки) в резервной копии
$cpk = @{}
$actions = @{}
try {
    foreach ($n in $archives) {
        $inWin = Full ("data\win\" + $n)
        $inBak = Join-Path $backup ("cpk" + $sep + $n)
        if (Test-Path -LiteralPath $inWin) { $cpk[$n] = [Cpk]::Open($inWin) }
        elseif ($update -and (Test-Path -LiteralPath $inBak)) { $cpk[$n] = [Cpk]::Open($inBak) }
    }
} catch {
    Say "ОШИБКА: не удалось прочитать архив игры: $($_.Exception.Message)"
    Say "Проверьте целостность файлов игры в Steam и запустите установщик ещё раз."
    Finish 6
}

$need = 0
foreach ($n in $archives) {
    if ($update) { $actions[$n] = "DONE"; continue }
    if ($cpk.ContainsKey($n)) {
        $missing = 0
        foreach ($e in $cpk[$n].Entries) { if (-not [IO.File]::Exists((Full (WinRel $e.Path)))) { $missing++ } }
        if ($missing -eq 0) { $actions[$n] = "MOVE" } else { $actions[$n] = "UNPACK"; $need += $cpk[$n].SumSize }
    } else { $actions[$n] = "NONE" }
}
# архив убран, а его файлов нет — игра повреждена
$probe = @{ $usName = "data\win\minigame"; $resName = "data\win\game_resident\game_resident_US.spc" }
foreach ($n in $archives) {
    if ($actions[$n] -eq "NONE" -and -not (Test-Path -LiteralPath (Full $probe[$n]))) {
        Say "ОШИБКА: в data\win нет архива $n, а его файлы не распакованы."
        Say "Верните файлы игры: Steam → ПКМ по игре → Свойства → Установленные файлы → «Проверить целостность файлов игры»,"
        Say "затем запустите установщик ещё раз."
        Finish 5
    }
}
$unpack = ($actions.Values -contains "UNPACK")
if ($update) { $mode = "UNPACK" } elseif ($unpack) { $mode = "UNPACK" } else { $mode = "LOOSE" }

if ($update) { }
elseif ($unpack) {
    Say "Основной русификатор не найден — файлы игры будут распакованы из архивов, поверх ляжет перевод."
    Say "Доп. режимы будут на русском, основная игра останется на английском."
    $free = $(if ($TestFreeSpace -ge 0) { $TestFreeSpace } else { (New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($GamePath))).AvailableFreeSpace })
    $reserve = 300MB
    Say ("Нужно места на диске: {0} ГБ, свободно: {1} ГБ." -f (Gb ($need + $reserve)), (Gb $free))
    if ($free -lt $need + $reserve) {
        Say ""
        Say ("ОШИБКА: недостаточно места на диске {0} — освободите ещё {1} ГБ и запустите установщик снова." -f ([IO.Path]::GetPathRoot($GamePath)), (Gb ($need + $reserve - $free)))
        Say "Игра не изменена."
        foreach ($c in $cpk.Values) { $c.Dispose() }
        Finish 8
    }
} else {
    Say "Найден основной русификатор — перевод доп. режимов ставится поверх него."
}

# указатель файлов: путь в архиве -> запись
$byPath = @{}
$allEntries = New-Object System.Collections.ArrayList
foreach ($n in $archives) { if ($cpk.ContainsKey($n)) { foreach ($e in $cpk[$n].Entries) { if (-not $byPath.ContainsKey($e.Path)) { $byPath[$e.Path] = $e; [void]$allEntries.Add($e) } } } }
# индекс распакованных файлов по имени (нужен, только если архивов нет)
$index = @{}
if ($allEntries.Count -eq 0) {
    Get-ChildItem -LiteralPath $win -Recurse -File | ForEach-Object {
        $k = $_.Name.ToLowerInvariant()
        if (-not $index.ContainsKey($k)) { $index[$k] = New-Object System.Collections.ArrayList }
        [void]$index[$k].Add(($_.FullName.Substring($win.Length + 1) -replace '[\\/]', "/"))
    }
}
function Resolve-Targets($target) {
    $res = @()
    if ($target.StartsWith("BYNAME:")) {
        $parts = ($target.Substring(7) -replace "\\", "/") -split "/"
        $name = $parts[-1]
        $parent = $(if ($parts.Count -gt 1) { ($parts[0..($parts.Count - 2)] -join "/") } else { "" })
        if ($allEntries.Count) {
            foreach ($e in $allEntries) {
                if ($e.Name -ieq $name -and (-not $parent -or $e.Dir -ieq $parent -or ("" + $e.Dir).ToLowerInvariant().EndsWith("/" + $parent.ToLowerInvariant()))) { $res += $e.Path }
            }
        } elseif ($index.ContainsKey($name.ToLowerInvariant())) {
            foreach ($t in $index[$name.ToLowerInvariant()]) {
                if (-not $parent -or $t.ToLowerInvariant().EndsWith(("/" + $parent + "/" + $name).ToLowerInvariant())) { $res += $t }
            }
        }
        return $res
    }
    $rel = ($target -replace "\\", "/") -replace "^data/win/", ""
    if ($byPath.ContainsKey($rel)) { $res += $byPath[$rel].Path }
    elseif ([IO.File]::Exists((Full (WinRel $rel)))) { $res += $rel }
    return $res
}

$ok = 0; $already = 0; $skipped = @(); $extracted = 0; $moved = @()
try {
    if (-not $update) { J "MODE" $mode }
    if ($Version) { J "VER" $Version }
    # файлы, созданные нами (их оригиналы — в архиве)
    $ours = @{}
    foreach ($l in $prev) { $f = $l -split "`t"; if ($f[0] -eq "X") { $ours[$f[1]] = 1 } }

    # 1. распаковка
    if ($update) {
        # вдруг часть распакованных файлов пропала — вернуть их из архивов
        $lost = @($allEntries | Where-Object { $ours.ContainsKey((WinRel $_.Path)) -and -not [IO.File]::Exists((Full (WinRel $_.Path))) })
        if ($lost.Count) {
            Say "Восстанавливаются пропавшие файлы игры: $($lost.Count)."
            $buf = New-Object byte[] (4MB)
            foreach ($e in $lost) { $e.Owner.Extract($e, (Full (WinRel $e.Path)), $buf) }
        }
    } elseif ($unpack) {
        $jobs = @(); $total = 0
        foreach ($n in $archives) { if ($actions[$n] -eq "UNPACK") { foreach ($e in $cpk[$n].Entries) { $jobs += $e; $total += $e.Size } } }
        Say ("Распаковка файлов игры ({1} ГБ, файлов: {0})..." -f $jobs.Count, (Gb $total))
        $buf = New-Object byte[] (4MB)
        $done = 0; $displaced = 0
        $sw = [Diagnostics.Stopwatch]::StartNew()
        foreach ($e in $jobs) {
            $rel = WinRel $e.Path
            $dst = Full $rel
            if ([IO.File]::Exists($dst)) {
                # файл лежал в data\win до установки (игра его не читала, пока был архив) — сохраняем
                J "P" $rel
                $b = Bak $rel; Ensure-Dir $b
                if ([IO.File]::Exists($b)) { [IO.File]::Delete($b) }
                Move-Item -LiteralPath $dst -Destination $b
                $displaced++
            }
            J "X" $rel
            $ours[$rel] = 1
            $e.Owner.Extract($e, $dst, $buf)
            $extracted++
            $done += $e.Size
            if ($TestFailAt -gt 0 -and $extracted -ge $TestFailAt) { throw "тестовый сбой" }
            $pct = [int](92 * $done / [Math]::Max($total, 1))
            Progress $pct ("Распаковка файлов игры: {0} из {1} ГБ" -f (Gb $done), (Gb $total))
        }
        Say ("Распаковано файлов: {0} за {1:N0} с." -f $extracted, $sw.Elapsed.TotalSeconds)
        if ($displaced) { Say "Файлы, лежавшие в data\win до установки, сохранены в резервной копии: $displaced." }
    }

    # 2. перевод
    Progress 93 "Установка перевода..." -Force
    $lines = @([IO.File]::ReadAllLines($man, $utf8) | Where-Object { $_ })
    $haveR = @{}
    foreach ($l in $prev) { $f = $l -split "`t"; if ($f[0] -eq "R") { $haveR[$f[1]] = 1 } }
    $newT = @{}
    $i = 0
    foreach ($line in $lines) {
        $i++
        $kind, $file, $target = $line -split "`t"
        $pf = Join-Path $Payload ($file -replace '[\\/]', $sep)
        $targets = @(Resolve-Targets $target)
        if ($targets.Count -eq 0) { $skipped += "$target (нет в игре)"; continue }
        $pbytes = [IO.File]::ReadAllBytes($pf)
        foreach ($t in $targets) {
            $rel = WinRel $t
            $full = Full $rel
            if (-not [IO.File]::Exists($full)) { $skipped += "$t (нет в игре)"; continue }
            $isOurs = $ours.ContainsKey($rel)
            # PATCHA — основной шрифт с кириллицей: только для оригинального шрифта из архива Steam,
            # у основного русификатора свой шрифт с кириллицей
            if ($kind -eq "PATCHA" -and -not $isOurs) { continue }
            $entry = $null; if ($byPath.ContainsKey($t)) { $entry = $byPath[$t] }
            if ($kind -eq "FULL") { $data = $pbytes }
            else {
                if ($isOurs -and $entry) { $base = $entry.Owner.Read($entry) } else { $base = [IO.File]::ReadAllBytes($full) }
                if (-not $isOurs -and [DrvPatch]::Sha1($base) -eq [DrvPatch]::NewSha($pbytes)) { $already++; $newT[$rel] = 1; J "T" $rel; continue }
                $data = [DrvPatch]::Apply($base, $pbytes)
                if ($null -eq $data -and $entry -and -not $isOurs) { $data = [DrvPatch]::Apply($entry.Owner.Read($entry), $pbytes) }
                if ($null -eq $data) { $skipped += "$t (версия файла отличается)"; continue }
            }
            if (-not $isOurs -and -not $haveR.ContainsKey($rel)) {
                J "R" $rel
                $b = Bak $rel; Ensure-Dir $b
                Copy-Item -LiteralPath $full -Destination $b -Force
                $haveR[$rel] = 1
            }
            $tmp = $full + ".rus_tmp"
            [IO.File]::WriteAllBytes($tmp, $data)
            Move-Item -LiteralPath $tmp -Destination $full -Force
            J "T" $rel
            $newT[$rel] = 1
            $ok++
            Progress (93 + [int](5 * $i / $lines.Count)) ("Установка перевода: {0} из {1}" -f $i, $lines.Count)
        }
    }
    if ($ok -eq 0 -and $already -eq 0) { throw "ни один файл перевода не подошёл к этой версии игры" }
    # при обновлении: файлы, которые прошлая версия переводила, а эта нет, — вернуть к оригиналу
    if ($update) {
        foreach ($l in $prev) {
            $f = $l -split "`t"
            if ($f[0] -eq "T" -and -not $newT.ContainsKey($f[1]) -and $ours.ContainsKey($f[1])) {
                $p = ($f[1] -replace '^data\\win\\', '') -replace '\\', '/'
                if ($byPath.ContainsKey($p)) { [IO.File]::WriteAllBytes((Full $f[1]), $byPath[$p].Owner.Read($byPath[$p])) }
            }
        }
    }
    foreach ($c in $cpk.Values) { $c.Dispose() }

    # 3. архивы — в резервную копию (последним шагом: до этого игра работает по-старому)
    Progress 99 "Перенос архивов в резервную копию..." -Force
    foreach ($n in $archives) {
        if ($actions[$n] -eq "UNPACK" -or $actions[$n] -eq "MOVE") {
            $cdir = Join-Path $backup "cpk"
            [void][IO.Directory]::CreateDirectory($cdir)
            $cdst = Join-Path $cdir $n
            if (Test-Path -LiteralPath $cdst) { Remove-Item -LiteralPath $cdst -Force }
            J "M" ("data\win\" + $n)
            Move-Item -LiteralPath (Full ("data\win\" + $n)) -Destination $cdst
            $moved += $n
        }
    }
    J-Close
    # сжать журнал (без повторов)
    $seen = @{}; $out = New-Object System.Collections.ArrayList
    foreach ($l in (Read-List)) { if (-not $seen.ContainsKey($l)) { $seen[$l] = 1; [void]$out.Add($l) } }
    [IO.File]::WriteAllLines($listPath, [string[]]$out.ToArray(), $utf8)
} catch {
    $msg = $_.Exception.Message
    J-Close
    foreach ($c in $cpk.Values) { try { $c.Dispose() } catch {} }
    Say ""
    Say "ОШИБКА: $msg"
    Say "Отмена изменений..."
    try { Undo-Install | Out-Null; Say "Игра возвращена в исходное состояние. Перевод не установлен." }
    catch { Say "Не удалось всё вернуть: $($_.Exception.Message)"; Say "Проверьте целостность файлов игры в Steam." }
    Finish 7
}

Progress 100 "Готово" -Force
Say ""
Say "Установлено файлов перевода: $ok"
if ($already) { Say "Уже были установлены: $already" }
if ($skipped.Count -gt 0) {
    Say "Пропущено: $($skipped.Count)"
    $skipped | ForEach-Object { Say "   $_" }
}
if ($mode -eq "UNPACK") {
    if ($moved.Count) { Say "Архивы перенесены в резервную копию ($backupName\cpk):"; $moved | ForEach-Object { Say "   $_" } }
    Say "Доп. режимы — на русском, основная игра — на английском."
    Say "Если Steam обновит игру или вы проверите целостность файлов, перевод пропадёт — просто запустите установщик ещё раз."
} elseif ($moved.Count) {
    Say "Архивы CPK перенесены в резервную копию (все их файлы уже распакованы основным русификатором):"
    $moved | ForEach-Object { Say "   $_" }
}
Say "Резервная копия: $backup"
Finish 0
