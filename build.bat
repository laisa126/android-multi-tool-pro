@echo off
title Android Multi-Tool Pro Builder
color 0b

echo =======================================================
echo          ANDROID MULTI-TOOL PRO - BUILD SCRIPT
echo =======================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please download and install Python from https://www.python.org/
    echo (Make sure to check "Add Python to PATH" during installation)
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
python -m pip install --upgrade pip
python -m pip install pyinstaller

echo.
echo [2/3] Verifying platform-tools (adb.exe, fastboot.exe)...
python download_windows_binaries.py

echo.
echo [3/3] Compiling into standalone Windows Executable...
python -m PyInstaller --clean --noconfirm AndroidMultiTool.spec

echo.
if exist "dist\AndroidMultiTool.exe" (
    echo =======================================================
    echo [SUCCESS] AndroidMultiTool.exe created successfully!
    echo Location: %CD%\dist\AndroidMultiTool.exe
    echo =======================================================
) else (
    echo [ERROR] Build failed! Check log messages above.
)

pause
