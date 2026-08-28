@echo off
title Android Multi-Tool Pro - USB Driver Installer
color 0a

echo ==========================================================
echo        AUTOMATED GSM & ANDROID USB DRIVER INSTALLER
echo ==========================================================
echo.
echo Installing essential drivers for ADB, Fastboot, MTK, and Qualcomm...
echo.

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This installer requires Administrator rights!
    echo Please right-click install_drivers.bat and select "Run as Administrator".
    pause
    exit /b 1
)

echo [1/4] Installing Google Universal ADB & Fastboot Drivers...
pnputil /add-driver "%~dp0bin\drivers\android_winusb.inf" /install >nul 2>&1
if %errorlevel% equ 0 (echo  -> Google ADB Driver OK) else (echo  -> Google ADB Driver skipped/already present)

echo [2/4] Registering MediaTek (MTK) USB VCOM Port Drivers...
pnputil /add-driver "%~dp0bin\drivers\cdc-acm.inf" /install >nul 2>&1
if %errorlevel% equ 0 (echo  -> MediaTek VCOM Driver OK) else (echo  -> MediaTek Driver skipped/already present)

echo [3/4] Registering Qualcomm HS-USB QDLoader 9008 Drivers...
pnputil /add-driver "%~dp0bin\drivers\qcser.inf" /install >nul 2>&1
if %errorlevel% equ 0 (echo  -> Qualcomm 9008 Driver OK) else (echo  -> Qualcomm Driver skipped/already present)

echo [4/4] Registering Samsung USB Composite Mobile Drivers...
pnputil /add-driver "%~dp0bin\drivers\ssudmdm.inf" /install >nul 2>&1
if %errorlevel% equ 0 (echo  -> Samsung Driver OK) else (echo  -> Samsung Driver skipped/already present)

echo.
echo ==========================================================
echo [SUCCESS] USB Drivers verified and registered!
echo Connect your phone and launch AndroidMultiTool.exe.
echo ==========================================================
pause
