"""
Script to download official Google Windows platform-tools (adb.exe, fastboot.exe, etc.)
so they are ready for bundling into the Windows .exe.
"""

import os
import urllib.request
import zipfile
import shutil

WIN_TOOLS_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"

def download_windows_tools(target_dir: str):
    os.makedirs(target_dir, exist_ok=True)
    zip_dest = os.path.join(target_dir, "platform-tools-win.zip")
    print(f"Downloading Windows platform-tools from {WIN_TOOLS_URL}...")
    urllib.request.urlretrieve(WIN_TOOLS_URL, zip_dest)
    print("Extracting Windows binaries (adb.exe, fastboot.exe, AdbWinApi.dll, AdbWinUsbApi.dll)...")

    needed = ["adb.exe", "fastboot.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll", "libwinpthread-1.dll"]
    with zipfile.ZipFile(zip_dest, 'r') as zf:
        for item in zf.namelist():
            fn = os.path.basename(item)
            if fn.lower() in [x.lower() for x in needed]:
                with zf.open(item) as src, open(os.path.join(target_dir, fn), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                print(f"  -> Extracted {fn}")

    if os.path.isfile(zip_dest):
        os.remove(zip_dest)
    print("Done! Windows binaries ready.")

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    bin_folder = os.path.join(base, "bin")
    download_windows_tools(bin_folder)
