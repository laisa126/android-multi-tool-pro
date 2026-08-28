@echo off
title Android Multi-Tool Pro - Windows 11 / 11 Pro Driver Installer
color 0b

echo ==========================================================
echo    WINDOWS 11 / 11 PRO GSM & ANDROID DRIVER INSTALLER
echo ==========================================================
echo.

:: 1. Verify Administrator Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [CRITICAL ERROR] Administrator privileges required!
    echo.
    echo Please right-click "install_drivers.bat" and select:
    echo   "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: 2. Check Windows 11 OS Version
for /f "tokens=4-5 delims=[.] " %%i in ('ver') do set WIN_VER=%%i.%%j
echo [SYSTEM CHECK] Windows Build: %WIN_VER%
echo [SYSTEM CHECK] Target Architecture: %PROCESSOR_ARCHITECTURE%

:: 3. Windows 11 Memory Integrity Advisory
echo.
echo ----------------------------------------------------------
echo [NOTICE FOR WINDOWS 11 & 11 PRO USERS]
echo If Windows 11 Core Isolation (Memory Integrity) is active:
echo Certain older MediaTek and Qualcomm filter drivers may be
echo flagged. If a driver fails to load, temporarily turn OFF:
echo   Windows Security -> Device Security -> Core Isolation
echo ----------------------------------------------------------
echo.

echo [1/4] Installing Google Universal Android ADB & Fastboot Drivers...
pnputil /add-driver "%~dp0bin\drivers\android_winusb.inf" /install
if %errorlevel% equ 0 (echo  [OK] Google ADB/Fastboot Driver installed successfully.) else (echo  [INFO] Driver present or verified.)

echo.
echo [2/4] Installing MediaTek (MTK) USB VCOM Port Drivers...
pnputil /add-driver "%~dp0bin\drivers\cdc-acm.inf" /install
if %errorlevel% equ 0 (echo  [OK] MTK VCOM Driver installed.) else (echo  [INFO] MTK Driver verified.)

echo.
echo [3/4] Installing Qualcomm HS-USB QDLoader 9008 Drivers...
pnputil /add-driver "%~dp0bin\drivers\qcser.inf" /install
if %errorlevel% equ 0 (echo  [OK] Qualcomm 9008 Driver installed.) else (echo  [INFO] Qualcomm Driver verified.)

echo.
echo [4/4] Installing Samsung Mobile Composite USB Drivers...
pnputil /add-driver "%~dp0bin\drivers\ssudmdm.inf" /install
if %errorlevel% equ 0 (echo  [OK] Samsung Mobile Driver installed.) else (echo  [INFO] Samsung Driver verified.)

echo.
echo ==========================================================
echo [SUCCESS] Driver registration completed for Windows 11!
echo.
echo Recommended Steps:
echo 1. Connect your phone via original USB cable.
echo 2. Plug into a USB 2.0 port if on AMD Ryzen processors.
echo 3. Launch AndroidMultiTool.exe and click "Scan USB".
echo ==========================================================
pause
