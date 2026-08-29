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

    if callback:
        for ok, msg in report:
            callback(f"[{'OK' if ok else 'WARN'}] {msg}")
    return report


def driver_install_guidance() -> str:
    if platform.system() == "Windows":
        return (
            "Windows driver install: run install_drivers.bat AS ADMIN. If the Tecno/MTK "
            "driver is still rejected, temporarily disable Memory Integrity (Core Isolation) "
            "and reboot with driver signature enforcement off, then re-run it."
        )
    if platform.system() == "Linux":
        return (
            "Linux: create /etc/udev/rules.d/51-android.rules with your device VID, then run "
            "'sudo udevadm control --reload-rules && sudo udevadm trigger'."
        )
    return "macOS: no driver install needed — adb uses the system USB stack."


def run_windows_driver_installer(base_dir: str) -> Tuple[bool, str]:
    """Launch install_drivers.bat elevated on Windows (UAC prompt)."""
    if platform.system() != "Windows":
        return False, "Driver installer only runs on Windows."
    bat = os.path.join(base_dir, "install_drivers.bat")
    if not os.path.isfile(bat):
        return False, f"Driver installer not found: {bat}"
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
             f"Start-Process -FilePath '{bat}' -Verb RunAs"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return True, "Driver installer launched — accept the UAC prompt to continue."
    except Exception as e:
        return False, f"Could not launch driver installer: {e}"
