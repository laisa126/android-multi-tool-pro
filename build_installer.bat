@echo off
title Android Multi-Tool Pro — Setup Builder (like Oumse)
color 0a

echo =======================================================
echo   ANDROID MULTI-TOOL PRO — WINDOWS SETUP BUILDER
echo   Clean Setup like Oumse GSM v2.1.0 — installs to
echo   C:\Program Files\AndroidMultiToolPro
echo =======================================================
echo.

:: 1. Check Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Install from https://www.python.org/ (tick Add to PATH)
    pause
    exit /b 1
)

:: 2. Build standalone EXE first (if not already present)
if not exist "dist\AndroidMultiTool.exe" (
    echo [1/3] Building AndroidMultiTool.exe via PyInstaller...
    python -m pip install --upgrade pip
    python -m pip install pyinstaller
    python download_windows_binaries.py
    python -m PyInstaller --clean --noconfirm AndroidMultiTool.spec
    if not exist "dist\AndroidMultiTool.exe" (
        echo [ERROR] PyInstaller build failed — check log above.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Found dist\AndroidMultiTool.exe — skipping PyInstaller build.
)

:: 3. Check Inno Setup 6 (iscc)
where iscc >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo.
    echo [2/3] Inno Setup 6 not found in PATH.
    echo        Download from https://jrsoftware.org/isdl.php and install.
    echo        Default location: C:\Program Files (x86)\Inno Setup 6\iscc.exe
    echo.
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        echo        Found at C:\Program Files (x86)\Inno Setup 6\ISCC.exe — using it.
        set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    ) else (
        echo [ERROR] iscc.exe not found. Install Inno Setup 6 and re-run.
        echo        You can also build portable ZIP via build.bat + install_app_on_pc.bat.
        pause
        exit /b 1
    )
) else (
    set ISCC=iscc
)

echo.
echo [2/3] Compiling Windows Setup with Inno Setup 6...
echo       Source: installer_setup.iss
echo       Output: dist\installer\AndroidMultiTool_Setup_v2.5.exe
echo.

%ISCC% installer_setup.iss
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Inno Setup compilation failed.
    pause
    exit /b 1
)

echo.
if exist "dist\installer\AndroidMultiTool_Setup_v2.5.exe" (
    echo =======================================================
    echo [SUCCESS] Setup built successfully!
    echo Location : %CD%\dist\installer\AndroidMultiTool_Setup_v2.5.exe
    echo Size     : 
    for %%A in ("dist\installer\AndroidMultiTool_Setup_v2.5.exe") do echo %%~zA bytes
    echo Install  : Right-click -^> Run as administrator
    echo           Installs to C:\Program Files\AndroidMultiToolPro
    echo           + Start Menu + Desktop + Uninstall
    echo =======================================================
) else (
    echo [WARN] iscc completed but output not found — check OutputDir in .iss
)

echo.
echo [3/3] Portable fallback also available:
echo       dist\AndroidMultiTool.exe + install_app_on_pc.bat
echo.

pause
