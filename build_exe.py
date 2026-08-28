"""
PyInstaller Build Script for Android Multi-Tool Pro
Compiles the application into a standalone Windows .exe with bundled ADB & Fastboot.
"""

import os
import sys
import subprocess
import shutil

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")
    spec_file = os.path.join(base_dir, "AndroidMultiTool.spec")

    print("==================================================")
    print("      BUILDING ANDROID MULTI-TOOL PRO .EXE        ")
    print("==================================================")

    # Check if pyinstaller is installed
    try:
        import PyInstaller
        print(f"[✓] PyInstaller {PyInstaller.__version__} detected.")
    except ImportError:
        print("[!] PyInstaller not found. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Ensure windows binaries exist in bin
    bin_dir = os.path.join(base_dir, "bin")
    needed_win_files = ["adb.exe", "fastboot.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"]
    missing = [f for f in needed_win_files if not os.path.isfile(os.path.join(bin_dir, f))]
    if missing:
        print(f"[!] Missing Windows binaries: {missing}. Downloading now...")
        from download_windows_binaries import download_windows_tools
        download_windows_tools(bin_dir)

    print("[*] Running PyInstaller build...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        spec_file
    ]

    res = subprocess.run(cmd, cwd=base_dir)
    if res.returncode == 0:
        print("\n==================================================")
        print(" [✓] BUILD SUCCESSFUL!")
        print(f" Standalone executable generated at:\n {os.path.join(dist_dir, 'AndroidMultiTool.exe')}")
        print("==================================================")
    else:
        print(f"\n[X] Build failed with code {res.returncode}")

if __name__ == "__main__":
    build()
