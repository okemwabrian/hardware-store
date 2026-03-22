!define APP_NAME "Hardware Store"
!define APP_VERSION "1.0"
!define APP_PUBLISHER "Brian Okemwa"
!define APP_EXE "HardwareStore.exe"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "HardwareStore_Setup.exe"
InstallDir "$PROGRAMFILES\HardwareStore"
RequestExecutionLevel admin

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "dist\*.*"
    CreateShortcut "$DESKTOP\Hardware Store.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortcut "$SMPROGRAMS\Hardware Store.lnk" "$INSTDIR\${APP_EXE}"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$DESKTOP\Hardware Store.lnk"
    Delete "$SMPROGRAMS\Hardware Store.lnk"
    RMDir /r "$INSTDIR"
SectionEnd