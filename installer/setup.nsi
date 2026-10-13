; Единый установщик русификатора доп. режимов Danganronpa V3
Unicode true
ManifestDPIAware true
SetCompressor /SOLID lzma
RequestExecutionLevel admin

!ifndef VERSION
  !define VERSION "2.2"
!endif
!define APPNAME "Русификатор доп. режимов Danganronpa V3"
!define UNKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\DRV3_RusExtra"
!define PSEXE '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File'

Name "${APPNAME}"
Caption "${APPNAME} ${VERSION}"
OutFile "${OUTFILE}"
InstallDir "$PROGRAMFILES32\Steam\steamapps\common\Danganronpa V3 Killing Harmony"
BrandingText "Нейросетевой перевод · lolik-lolikov · v${VERSION}"
ShowInstDetails show
ShowUninstDetails show
InstProgressFlags smooth
SpaceTexts none

VIProductVersion "${VERSION}.0.0"
VIAddVersionKey /LANG=1049 "ProductName" "${APPNAME}"
VIAddVersionKey /LANG=1049 "FileDescription" "${APPNAME}"
VIAddVersionKey /LANG=1049 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1049 "CompanyName" "lolik-lolikov"
VIAddVersionKey /LANG=1049 "LegalCopyright" "Фанатский некоммерческий нейросетевой перевод · lolik-lolikov"

!include MUI2.nsh
!include LogicLib.nsh

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!define MUI_WELCOMEPAGE_TITLE "Русификатор дополнительных режимов$\r$\nDanganronpa V3: Killing Harmony"
!define MUI_WELCOMEPAGE_TEXT "Переводятся: «Любовь через Вселенную» (Salmon Team), «План развития Абсолютных Талантов», «Подземелье Отчаяния», Автомат и Карты Смерти, казино.$\r$\n$\r$\nПеревод полностью нейросетевой (Claude, Anthropic). Автор сборки: lolik-lolikov (steamcommunity.com/id/lolikovski).$\r$\n$\r$\nОсновной русификатор не нужен. Если его нет, установщик распакует файлы игры (нужно около 10,5 ГБ свободного места), основная игра останется на английском. Если он есть, перевод встанет поверх него. При удалении всё возвращается как было.$\r$\n$\r$\nЗакройте игру и нажмите «Далее»."
!insertmacro MUI_PAGE_WELCOME

!define MUI_PAGE_HEADER_TEXT "Информация"
!define MUI_PAGE_HEADER_SUBTEXT "Что входит в перевод и как его удалить"
!define MUI_LICENSEPAGE_TEXT_TOP "Прочитайте, пожалуйста:"
!define MUI_LICENSEPAGE_BUTTON "Далее >"
!define MUI_LICENSEPAGE_TEXT_BOTTOM " "
!insertmacro MUI_PAGE_LICENSE "readme_utf16.txt"

!define MUI_PAGE_HEADER_TEXT "Папка игры"
!define MUI_PAGE_HEADER_SUBTEXT "Укажите, где установлена Danganronpa V3"
!define MUI_DIRECTORYPAGE_TEXT_TOP "Папка игры определена автоматически. Если она указана неверно, нажмите «Обзор» и выберите папку, в которой находится Dangan3Win.exe.$\r$\n$\r$\nЕсли основной русификатор не установлен, на диске с игрой нужно около 10,5 ГБ свободного места: установщик распакует файлы игры из двух архивов."
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Папка Danganronpa V3 Killing Harmony"
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE DirLeave
!insertmacro MUI_PAGE_DIRECTORY

!define MUI_INSTFILESPAGE_FINISHHEADER_TEXT "Готово"
!define MUI_INSTFILESPAGE_FINISHHEADER_SUBTEXT "Русификатор установлен"
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_TITLE "Перевод установлен!"
!define MUI_FINISHPAGE_TEXT "Дополнительные режимы Danganronpa V3 теперь на русском.$\r$\n$\r$\nЕсли Steam обновит игру или вы проверите целостность файлов, перевод пропадёт — просто запустите установщик ещё раз.$\r$\n$\r$\nУдалить перевод: «Параметры → Приложения» (${APPNAME}) или Uninstall_RusExtra.exe в папке игры\_rus_extra_backup.$\r$\n$\r$\nПеревод полностью нейросетевой. Автор сборки — lolik-lolikov (steamcommunity.com/id/lolikovski). Нашли ошибку — напишите в Steam.$\r$\n$\r$\nПриятной игры!"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Russian"

Var PsCmd
Var PsRc
Var PsSI
Var PsPI
Var PsH
Var PsT
Var PsW
Var PsWait
Var LogPos
Var F
Var S1
Var S2

Function .onInit
  InitPluginsDir
  File /oname=$PLUGINSDIR\install.ps1 "install.ps1"
  nsExec::Exec '${PSEXE} "$PLUGINSDIR\install.ps1" -DetectOnly -OutFile "$PLUGINSDIR\game.txt"'
  Pop $0
  ClearErrors
  FileOpen $1 "$PLUGINSDIR\game.txt" r
  ${IfNot} ${Errors}
    FileSeek $1 2 SET
    FileReadUTF16LE $1 $2
    FileClose $1
    ${If} $2 != ""
      StrCpy $INSTDIR $2
    ${EndIf}
  ${EndIf}
FunctionEnd

Function DirLeave
  ${IfNot} ${FileExists} "$INSTDIR\Dangan3Win.exe"
  ${AndIfNot} ${FileExists} "$INSTDIR\data\win\partition_data_win.cpk"
    MessageBox MB_ICONEXCLAMATION|MB_OK "В этой папке не найдена игра Danganronpa V3 (нет Dangan3Win.exe).$\r$\nУкажите папку, в которую установлена игра."
    Abort
  ${EndIf}
FunctionEnd

; Запуск install.ps1 без окна консоли. Пока он работает, установщик читает файлы
; status.txt (проценты и текст — в полосу хода и строку состояния) и log.txt (новые строки — в список).
; Вход: $PsCmd — командная строка. Выход: $PsRc — код возврата (-1 — не удалось запустить).
!macro RUNPS_FUNCS UN
Function ${UN}PollPS
  ClearErrors
  FileOpen $F "$PLUGINSDIR\status.txt" r
  ${IfNot} ${Errors}
    FileSeek $F 2 SET
    FileReadUTF16LE $F $S1
    FileReadUTF16LE $F $S2
    FileClose $F
    StrCpy $PsW $S2 2 -2
    ${If} $PsW == "$\r$\n"
      StrCpy $S2 $S2 -2
    ${EndIf}
    ${If} $S1 != ""
      IntOp $S1 $S1 * 300
      FindWindow $PsW "#32770" "" $HWNDPARENT
      GetDlgItem $PsW $PsW 1004
      SendMessage $PsW ${PBM_SETPOS} $S1 0
    ${EndIf}
    ${If} $S2 != ""
      SetDetailsPrint textonly
      DetailPrint "$S2"
      SetDetailsPrint both
    ${EndIf}
  ${EndIf}
  ClearErrors
  FileOpen $F "$PLUGINSDIR\log.txt" r
  ${IfNot} ${Errors}
    FileSeek $F $LogPos SET
    ${Do}
      ClearErrors
      FileReadUTF16LE $F $S1
      ${If} ${Errors}
        ${ExitDo}
      ${EndIf}
      StrCpy $PsW $S1 2 -2
      ${If} $PsW != "$\r$\n"
        ${ExitDo}
      ${EndIf}
      FileSeek $F 0 CUR $LogPos
      StrCpy $S1 $S1 -2
      SetDetailsPrint listonly
      DetailPrint "$S1"
      SetDetailsPrint both
    ${Loop}
    FileClose $F
  ${EndIf}
FunctionEnd

Function ${UN}RunPS
  StrCpy $LogPos 2
  StrCpy $PsRc -1
  Delete "$PLUGINSDIR\status.txt"
  Delete "$PLUGINSDIR\log.txt"
  ; полоса хода — с нуля (дальше её двигает PollPS по status.txt)
  FindWindow $PsW "#32770" "" $HWNDPARENT
  GetDlgItem $PsW $PsW 1004
  SendMessage $PsW ${PBM_SETPOS} 0 0
  ; STARTUPINFOW (68 байт, cb = 68) и PROCESS_INFORMATION (16 байт)
  System::Call '*(i 68, i 0, i 0, i 0, i 0, i 0, i 0, i 0, i 0, i 0, i 0, i 0, i 0, i 0, i 0, i 0, i 0) p .s'
  Pop $PsSI
  System::Call '*(i 0, i 0, i 0, i 0) p .s'
  Pop $PsPI
  Push $PsCmd
  ; CREATE_NO_WINDOW = 0x08000000
  System::Call 'kernel32::CreateProcessW(p 0, w s, p 0, p 0, i 0, i 0x08000000, p 0, p 0, p $PsSI, p $PsPI) i .s'
  Pop $PsW
  ${If} $PsW != 0
    System::Call '*$PsPI(p .s)'
    Pop $PsH
    System::Call '*$PsPI(p, p .s)'
    Pop $PsT
    System::Call 'kernel32::CloseHandle(p $PsT)'
    ; ждём завершения; WAIT_TIMEOUT = 258, WAIT_OBJECT_0 = 0
    ; (результат — в отдельной переменной $PsWait: PollPS её не трогает)
    ${Do}
      System::Call 'kernel32::WaitForSingleObject(p $PsH, i 250) i .s'
      Pop $PsWait
      Call ${UN}PollPS
      ${IfNot} $PsWait == 258
        ${ExitDo}
      ${EndIf}
    ${Loop}
    ${If} $PsWait != 0
      ; на всякий случай: никогда не бросаем работающий процесс
      System::Call 'kernel32::WaitForSingleObject(p $PsH, i -1) i .s'
      Pop $PsWait
    ${EndIf}
    System::Call 'kernel32::GetExitCodeProcess(p $PsH, *i .s)'
    Pop $PsRc
    System::Call 'kernel32::CloseHandle(p $PsH)'
    Call ${UN}PollPS
  ${Else}
    DetailPrint "Не удалось запустить PowerShell."
  ${EndIf}
  System::Free $PsSI
  System::Free $PsPI
FunctionEnd
!macroend
!insertmacro RUNPS_FUNCS ""
!insertmacro RUNPS_FUNCS "un."

Section "Перевод" SecMain
  SectionIn RO
  DetailPrint "Распаковка файлов перевода..."
  SetDetailsPrint listonly
  SetOutPath "$PLUGINSDIR\payload"
  File /r "payload\*.*"
  SetDetailsPrint both
  DetailPrint "Проверка игры..."
  StrCpy $PsCmd '${PSEXE} "$PLUGINSDIR\install.ps1" -GamePath "$INSTDIR" -Payload "$PLUGINSDIR\payload" -NoPause -Log "$PLUGINSDIR\log.txt" -Status "$PLUGINSDIR\status.txt" -Version "${VERSION}"'
  Call RunPS
  ${If} $PsRc != 0
    ${IfNot} ${FileExists} "$INSTDIR\_rus_extra_backup\installed.txt"
      DeleteRegKey HKLM "${UNKEY}"
    ${EndIf}
    ${If} $PsRc == 4
      MessageBox MB_ICONSTOP|MB_OK "Игра запущена. Закройте её и запустите установщик ещё раз."
    ${ElseIf} $PsRc == 8
      MessageBox MB_ICONSTOP|MB_OK "Недостаточно места на диске с игрой. Сколько нужно освободить — написано в списке на экране установщика.$\r$\nИгра не изменена."
    ${Else}
      MessageBox MB_ICONSTOP|MB_OK "Установка не выполнена (код $PsRc). Подробности — в списке на экране установщика."
    ${EndIf}
    Abort "Установка прервана"
  ${EndIf}
  SetDetailsPrint none
  SetOutPath "$INSTDIR\_rus_extra_backup"
  File "install.ps1"
  WriteUninstaller "$INSTDIR\_rus_extra_backup\Uninstall_RusExtra.exe"
  SetDetailsPrint both
  WriteRegStr HKLM "${UNKEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "${UNKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "${UNKEY}" "Publisher" "lolik-lolikov"
  WriteRegStr HKLM "${UNKEY}" "URLInfoAbout" "https://steamcommunity.com/id/lolikovski/"
  WriteRegStr HKLM "${UNKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNKEY}" "UninstallString" '"$INSTDIR\_rus_extra_backup\Uninstall_RusExtra.exe"'
  WriteRegDWORD HKLM "${UNKEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNKEY}" "NoRepair" 1
  DetailPrint "Готово."
SectionEnd

Section "Uninstall"
  InitPluginsDir
  File /oname=$PLUGINSDIR\install.ps1 "install.ps1"
  DetailPrint "Восстановление оригинальных файлов игры..."
  StrCpy $PsCmd '${PSEXE} "$PLUGINSDIR\install.ps1" -Uninstall -GamePath "$INSTDIR\.." -NoPause -Log "$PLUGINSDIR\log.txt" -Status "$PLUGINSDIR\status.txt"'
  Call un.RunPS
  ${If} $PsRc == 4
    MessageBox MB_ICONSTOP|MB_OK "Игра запущена. Закройте её и запустите удаление ещё раз."
    Abort "Удаление прервано"
  ${ElseIf} $PsRc != 0
  ${AndIf} $PsRc != 1
    MessageBox MB_ICONEXCLAMATION|MB_OK "Удаление завершилось с ошибкой (код $PsRc). Подробности — в списке на экране.$\r$\nЕсли игра не запускается — проверьте целостность файлов игры в Steam."
  ${EndIf}
  DeleteRegKey HKLM "${UNKEY}"
  ; на случай, если что-то осталось
  Delete "$INSTDIR\Uninstall_RusExtra.exe"
  Delete "$INSTDIR\install.ps1"
  RMDir "$INSTDIR"
SectionEnd
