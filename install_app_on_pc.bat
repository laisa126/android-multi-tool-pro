@echo off
title Android Multi-Tool Pro - PC Application Installer
color 0f

echo ==========================================================
echo       ANDROID MULTI-TOOL PRO - WINDOWS APP INSTALLER
echo   Tecno Camon 50 Pro (CN5c) & Universal Technician Edition
echo ==========================================================
echo.

set "APP_NAME=Android Multi-Tool Pro"
set "APP_VER=2.5.0"
set "INSTALL_DIR=%LOCALAPPDATA%\Programs\AndroidMultiToolPro"

echo [1/5] Setting up application directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\bin" mkdir "%INSTALL_DIR%\bin"

echo [2/5] Installing application binaries and engines...
if exist "%~dp0AndroidMultiTool.exe" (
    copy /y "%~dp0AndroidMultiTool.exe" "%INSTALL_DIR%\" >nul
    echo  [OK] Copied AndroidMultiTool.exe
) else if exist "%~dp0dist\AndroidMultiTool.exe" (
    copy /y "%~dp0dist\AndroidMultiTool.exe" "%INSTALL_DIR%\" >nul
    echo  [OK] Copied AndroidMultiTool.exe from dist
) else (
    echo  [WARN] Standalone EXE not found in current folder. If running from source, app will use python launcher.
)

if exist "%~dp0bin" (
    xcopy /e /i /y "%~dp0bin\*" "%INSTALL_DIR%\bin\" >nul
    echo  [OK] Installed platform-tools (adb.exe, fastboot.exe, DLLs)
)

if exist "%~dp0install_drivers.bat" (
    copy /y "%~dp0install_drivers.bat" "%INSTALL_DIR%\" >nul
    echo  [OK] Bundled Windows 11 driver installer
)

if exist "%~dp0README.md" (
    copy /y "%~dp0README.md" "%INSTALL_DIR%\" >nul
)

echo [3/5] Creating Windows Desktop and Start Menu Shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$shortcut = $ws.CreateShortcut([System.IO.Path]::Combine($desktop, 'Android Multi-Tool Pro.lnk')); " ^
  "$shortcut.TargetPath = '%INSTALL_DIR%\AndroidMultiTool.exe'; " ^
  "$shortcut.WorkingDirectory = '%INSTALL_DIR%'; " ^
  "$shortcut.Description = 'Android Multi-Tool Pro - Hardware & Firmware GSM Suite'; " ^
  "$shortcut.Save()"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$startMenu = [System.IO.Path]::Combine([Environment]::GetFolderPath('StartMenu'), 'Programs'); " ^
  "if (-not (Test-Path $startMenu)) { New-Item -ItemType Directory -Path $startMenu | Out-Null }; " ^
  "$shortcut = $ws.CreateShortcut([System.IO.Path]::Combine($startMenu, 'Android Multi-Tool Pro.lnk')); " ^
  "$shortcut.TargetPath = '%INSTALL_DIR%\AndroidMultiTool.exe'; " ^
  "$shortcut.WorkingDirectory = '%INSTALL_DIR%'; " ^
  "$shortcut.Description = 'Android Multi-Tool Pro'; " ^
  "$shortcut.Save()"
echo  [OK] Desktop Shortcut created!
echo  [OK] Windows Start Menu entry added!

echo [4/5] Registering in Windows Installed Apps...
set "REG_KEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\AndroidMultiToolPro"
reg add "%REG_KEY%" /v "DisplayName" /t REG_SZ /d "Android Multi-Tool Pro" /f >nul
reg add "%REG_KEY%" /v "DisplayVersion" /t REG_SZ /d "%APP_VER%" /f >nul
reg add "%REG_KEY%" /v "Publisher" /t REG_SZ /d "GSM Technician Solutions" /f >nul
reg add "%REG_KEY%" /v "InstallLocation" /t REG_SZ /d "%INSTALL_DIR%" /f >nul
reg add "%REG_KEY%" /v "DisplayIcon" /t REG_SZ /d "%INSTALL_DIR%\AndroidMultiTool.exe" /f >nul
reg add "%REG_KEY%" /v "UninstallString" /t REG_SZ /d "cmd.exe /c rmdir /s /q \"%INSTALL_DIR%\"" /f >nul
echo  [OK] Registered in Windows Settings / Control Panel

echo [5/5] Configuring Transsion (Tecno / Infinix) ADB Vendor ID...
if not exist "%USERPROFILE%\.android" mkdir "%USERPROFILE%\.android"
findstr /C:"0x2e04" "%USERPROFILE%\.android\adb_usb.ini" >nul 2>&1
if %errorlevel% neq 0 (
    echo 0x2e04>> "%USERPROFILE%\.android\adb_usb.ini"
)
findstr /C:"0x0e8d" "%USERPROFILE%\.android\adb_usb.ini" >nul 2>&1
if %errorlevel% neq 0 (
    echo 0x0e8d>> "%USERPROFILE%\.android\adb_usb.ini"
)
echo  [OK] Transsion VID 0x2E04 registered.

echo.
echo ==========================================================
echo [SUCCESS] Android Multi-Tool Pro is now installed on your PC!
echo.
echo - Desktop Icon: "Android Multi-Tool Pro"
echo - Start Menu: Search "Android Multi-Tool" in Windows search
echo - Installed Path: %INSTALL_DIR%
echo ==========================================================
echo.

set /p LAUNCH="Would you like to launch Android Multi-Tool Pro now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    start "" "%INSTALL_DIR%\AndroidMultiTool.exe"
)

exit /b 0
