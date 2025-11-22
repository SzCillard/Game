; ================================
; Commanders Arena Installer
; ================================

!define APP_NAME "CommandersArena"
!define APP_EXE "CommandersArena.exe"
!define UNINSTALL_EXE "$INSTDIR\Uninstall.exe"

OutFile "CommandersArenaInstaller.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"

; ---------------------------------
; Pages
; ---------------------------------
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

; ---------------------------------
; Installation Section
; ---------------------------------
Section "Install"
  SetOutPath "$INSTDIR"

  ; Copy game files (recursive)
  File /r "dist_package\*"

  ; Desktop shortcut
  CreateShortcut "$DESKTOP\Commanders Arena.lnk" "$INSTDIR\${APP_EXE}"

  ; Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\Commanders Arena"
  CreateShortcut "$SMPROGRAMS\Commanders Arena\Commanders Arena.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\Commanders Arena\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Register uninstaller with Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "NoRepair" 1

SectionEnd

; ---------------------------------
; Uninstall Section
; ---------------------------------
Section "Uninstall"
  ; Remove shortcuts
  Delete "$DESKTOP\Commanders Arena.lnk"
  RMDir /r "$SMPROGRAMS\Commanders Arena"

  ; Remove installed files
  RMDir /r "$INSTDIR"

  ; Remove registry entry
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

SectionEnd
