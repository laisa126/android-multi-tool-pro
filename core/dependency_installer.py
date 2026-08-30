"""
Android Multi-Tool Pro - Runtime Dependency Installer
-----------------------------------------------------
Self-healing setup: ensures the app has everything it needs to talk to a
device (adb/fastboot binaries, pyserial for MTK/Samsung serial work, and the
Windows driver INF installer) and reports exactly what it did.

Used by both the desktop GUI (startup + "Install Tools & Drivers" button) and
the web suite (/api/install_tools).
"""

import os
import sys
import platform
import shutil
import subprocess
from typing import Callable, List, Tuple, Optional

from .downloader import ensure_binaries


def ensure_pyserial(callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Ensure pyserial is importable; pip-install it if missing."""
    try:
        import serial  # noqa: F401
        return True, f"pyserial {serial.VERSION} available"
    except Exception:
        pass
    if callback:
        callback("pyserial not found — installing via pip...")
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "pyserial"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300
        )
        if r.returncode == 0:
            return True, "pyserial installed successfully"
        return False, f"pip install pyserial failed (code {r.returncode})"
    except Exception as e:
        return False, f"Could not install pyserial: {e}"


def mtkclient_status() -> Tuple[bool, str]:
    """Check whether the real mtkclient CLI is installed and importable."""
    try:
        import mtkclient  # noqa: F401
        return True, f"mtkclient {getattr(mtkclient, '__version__', '(importable)')}"
    except Exception:
        pass
    exe = shutil.which("mtk") or shutil.which("mtkclient")
    if exe:
        return True, f"mtkclient CLI at {exe}"
    return False, "mtkclient is NOT installed"


def install_mtkclient(callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Ensure the real mtkclient CLI is installed (pip install if missing).

    mtkclient is the free tool that performs the actual MediaTek exploit for
    every MTK deep-service operation (backup / flash / FRP wipe / seccfg unlock).
    Best-effort: if pip fails (offline, no compiler, etc.) we return the honest
    failure so the caller can fall back to manual instructions.
    """
    ok, msg = mtkclient_status()
    if ok:
        if callback:
            callback(f"mtkclient already available: {msg}")
        return True, msg
    if callback:
        callback("mtkclient not found — installing via pip (needs internet, can take a few minutes)...")
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", "mtkclient"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=900
        )
    except Exception as e:
        return False, f"Could not install mtkclient: {e}"
    ok2, msg2 = mtkclient_status()
    if ok2:
        return True, "mtkclient installed — " + msg2
    return False, f"pip install mtkclient failed (code {r.returncode}). " \
                  "Install manually: pip install mtkclient  (or clone https://github.com/bkerler/mtkclient)"


def ensure_runtime_dependencies(base_dir: str, callback: Optional[Callable[[str], None]] = None) -> List[Tuple[bool, str]]:
    """Ensure adb/fastboot binaries + pyserial. Returns a list of (ok, message)."""
    report: List[Tuple[bool, str]] = []

    if callback:
        callback("Verifying adb & fastboot platform-tools binaries...")
    try:
        ok = ensure_binaries(base_dir, callback)
        report.append((ok, "ADB / Fastboot binaries ready" if ok else "Platform-tools unavailable (will fall back to system PATH)"))
    except Exception as e:
        report.append((False, f"Platform-tools check error: {e}"))

    ok_ser, msg = ensure_pyserial(callback)
    report.append((ok_ser, msg))

    # Check-only at startup: mtkclient is installed on demand by
    # "Install Tools & Drivers" (it's heavy), but we always report its status.
    ok_mtk, msg_mtk = mtkclient_status()
    report.append((ok_mtk, msg_mtk))

    if callback:
        for ok, msg in report:
            callback(f"[{'OK' if ok else 'WARN'}] {msg}")
    return report


def driver_install_guidance() -> str:
    if platform.system() == "Windows":
        return (
            "Windows driver install: use the in-app 'Install Tools & Drivers' button — it auto-installs the "
            "MediaTek VCOM + ADB drivers (pnputil, UAC). If Windows still blocks the unsigned "
            "VCOM INF, use 'Force-Install VCOM (Test Mode)' (needs a reboot) or Device Manager."
        )
    if platform.system() == "Linux":
        return (
            "Linux: create /etc/udev/rules.d/51-android.rules with your device VID, then run "
            "'sudo udevadm control --reload-rules && sudo udevadm trigger'."
        )
    return "macOS: no driver install needed — adb uses the system USB stack."


def run_windows_driver_installer(base_dir: str) -> Tuple[bool, str]:
    """Self-install the MediaTek VCOM + Android ADB drivers (Python-native, UAC).

    Delegates to core.driver_installer, which stages bin/drivers/*.inf via
    pnputil, binds any connected MTK/Tecno device, registers ADB vendor IDs and
    restarts the daemon — relaunching itself elevated if needed.
    """
    if platform.system() != "Windows":
        return False, "Driver installer only runs on Windows."
    try:
        from . import driver_installer
    except Exception as e:
        return False, f"Could not load driver installer: {e}"
    log_path = driver_installer.default_log_path()
    return driver_installer.start_driver_install(log_path)
