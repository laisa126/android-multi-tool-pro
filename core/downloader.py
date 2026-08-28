"""
Android Multi-Tool Pro - Platform Tools Downloader
Downloads and extracts official Google ADB and Fastboot binaries
so the application is 100% self-sufficient without requiring manual SDK setup.
"""

import os
import sys
import platform
import urllib.request
import zipfile
import shutil

PLATFORM_TOOLS_URLS = {
    "Windows": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
    "Linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
    "Darwin": "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip"
}

def ensure_binaries(target_dir: str, callback=None) -> bool:
    """Ensures adb and fastboot binaries exist in target_dir. Downloads if missing."""
    os.makedirs(target_dir, exist_ok=True)
    system_os = platform.system()
    ext = ".exe" if system_os == "Windows" else ""
    adb_bin = os.path.join(target_dir, f"adb{ext}")
    fastboot_bin = os.path.join(target_dir, f"fastboot{ext}")

    if os.path.isfile(adb_bin) and os.path.isfile(fastboot_bin):
        if callback:
            callback("Platform tools binaries verified OK.")
        return True

    url = PLATFORM_TOOLS_URLS.get(system_os, PLATFORM_TOOLS_URLS["Windows"])
    zip_path = os.path.join(target_dir, "platform-tools.zip")

    if callback:
        callback(f"Downloading official Google Android Platform Tools from {url}...")

    try:
        urllib.request.urlretrieve(url, zip_path)
        if callback:
            callback("Extracting platform tools...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                filename = os.path.basename(member)
                if not filename:
                    continue
                # Extract needed binaries
                needed = ["adb", "fastboot", "adb.exe", "fastboot.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll", "libwinpthread-1.dll"]
                if filename.lower() in [n.lower() for n in needed]:
                    source = zip_ref.open(member)
                    target = open(os.path.join(target_dir, filename), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    if system_os != "Windows":
                        os.chmod(os.path.join(target_dir, filename), 0o755)

        if os.path.isfile(zip_path):
            os.remove(zip_path)

        if callback:
            callback("Platform tools successfully installed!")
        return True
    except Exception as e:
        if callback:
            callback(f"Failed downloading platform-tools: {e}")
        return False

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_folder = os.path.join(base_dir, "bin")
    ensure_binaries(bin_folder, print)
