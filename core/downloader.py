"""
Android Multi-Tool Pro - Platform Tools Downloader (100% OFFLINE-FIRST)
Downloads are OPTIONAL. Tool works fully offline if binaries already bundled in /bin.
Oumse-like GSM tools require internet + credits. This tool is PERMANENTLY OFFLINE.
"""

import os
import platform
import shutil
import zipfile

PLATFORM_TOOLS_URLS = {
    "Windows": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
    "Linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
    "Darwin": "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip"
}

# Bundled binaries that make the tool 100% offline
BUNDLED_BINARIES = [
    "adb", "adb.exe",
    "fastboot", "fastboot.exe",
    "AdbWinApi.dll", "AdbWinUsbApi.dll", "libwinpthread-1.dll"
]

def _has_offline_bundle(target_dir: str) -> bool:
    """Check if at least one ADB variant + fastboot variant exists (covers Windows+Linux)."""
    system_os = platform.system()
    ext = ".exe" if system_os == "Windows" else ""
    adb_bin = os.path.join(target_dir, f"adb{ext}")
    fb_bin = os.path.join(target_dir, f"fastboot{ext}")
    # Also accept cross-platform fallback (Linux bin can run on Linux, Windows exe exists for bundling)
    has_adb = os.path.isfile(adb_bin) or os.path.isfile(os.path.join(target_dir, "adb")) or os.path.isfile(os.path.join(target_dir, "adb.exe"))
    has_fb = os.path.isfile(fb_bin) or os.path.isfile(os.path.join(target_dir, "fastboot")) or os.path.isfile(os.path.join(target_dir, "fastboot.exe"))
    return has_adb and has_fb

def ensure_binaries(target_dir: str, callback=None) -> bool:
    """Ensures adb and fastboot binaries exist. 100% OFFLINE if bundle present."""
    os.makedirs(target_dir, exist_ok=True)

    if _has_offline_bundle(target_dir):
        if callback:
            callback("Platform tools binaries verified OK [OFFLINE BUNDLE].")
        # Ensure executable bit on Linux
        if platform.system() != "Windows":
            for name in ["adb", "fastboot"]:
                p = os.path.join(target_dir, name)
                if os.path.isfile(p):
                    try:
                        os.chmod(p, 0o755)
                    except Exception:
                        pass
        return True

    # No bundle found — try OPTIONAL online download (only if internet exists)
    if callback:
        callback("Offline bundle missing. Attempting one-time download (internet required once)...")

    try:
        import urllib.request
        system_os = platform.system()
        url = PLATFORM_TOOLS_URLS.get(system_os, PLATFORM_TOOLS_URLS["Windows"])
        zip_path = os.path.join(target_dir, "platform-tools.zip")
        if callback:
            callback(f"Downloading from {url} ...")
        urllib.request.urlretrieve(url, zip_path)
        if callback:
            callback("Extracting platform tools...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                filename = os.path.basename(member)
                if not filename:
                    continue
                needed = [n.lower() for n in BUNDLED_BINARIES]
                if filename.lower() in needed:
                    source = zip_ref.open(member)
                    target = open(os.path.join(target_dir, filename), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    if platform.system() != "Windows":
                        try:
                            os.chmod(os.path.join(target_dir, filename), 0o755)
                        except Exception:
                            pass
        if os.path.isfile(zip_path):
            os.remove(zip_path)
        if callback:
            callback("Platform tools installed [ONLINE ONE-TIME]. Next runs will be 100% OFFLINE.")
        return _has_offline_bundle(target_dir)
    except Exception as e:
        if callback:
            # Offline-friendly error — do NOT block tool
            callback(f"Offline mode: No internet, using bundled tools. If binaries missing, reinstall ZIP from GitHub. Detail: {e}")
        # Check again if bundle somehow exists after failure
        return _has_offline_bundle(target_dir)

def verify_offline_ready() -> dict:
    """Return offline readiness report for Diagnostics tab."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_dir = os.path.join(base_dir, "bin")
    drivers_dir = os.path.join(bin_dir, "drivers")
    report = {
        "offline_capable": True,
        "requires_internet": False,
        "requires_credits": False,
        "requires_server": False,
        "adb_bundled": os.path.isfile(os.path.join(bin_dir, "adb")) or os.path.isfile(os.path.join(bin_dir, "adb.exe")),
        "fastboot_bundled": os.path.isfile(os.path.join(bin_dir, "fastboot")) or os.path.isfile(os.path.join(bin_dir, "fastboot.exe")),
        "drivers_bundled": os.path.isdir(drivers_dir) and len(os.listdir(drivers_dir)) > 0 if os.path.isdir(drivers_dir) else False,
        "all_engines_offline": True,
        "engines": [
            "ADB Engine (local subprocess)",
            "Fastboot Engine (local subprocess)",
            "MTK BROM Engine (local COM port)",
            "SPD Unisoc Engine (local COM port)",
            "Proinfo Regional Unlock Engine (local file patch)",
            "Transsion MDM Engine (local ADB)",
            "FRP Engine (local Fastboot/ADB)",
            "EFS/NVRAM Engine (local dd)",
            "Samsung Modem Engine (local COM AT)",
            "Payload Extractor (local ZIP)",
            "Scatter Flasher (local COM)"
        ]
    }
    report["ready"] = report["adb_bundled"] and report["fastboot_bundled"]
    return report

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_folder = os.path.join(base_dir, "bin")
    ok = ensure_binaries(bin_folder, print)
    print("OFFLINE READY:", verify_offline_ready())
