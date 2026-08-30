"""
Android Multi-Tool Pro — Windows driver self-installer (MediaTek USB VCOM + ADB).

Runs the REAL driver installation steps directly (no .bat needed):
  1. Stages the MediaTek USB VCOM driver (bin/drivers/cdc-acm.inf), which binds
     the inbox usbser.sys to the MTK Preloader (VID_0E8D&PID_2000), BROM
     (PID_0003) and DA (PID_2001) ports.
  2. Stages the Android WinUSB driver (bin/drivers/android_winusb.inf) for
     Transsion (0x2E04) / MediaTek (0x0E8D) / Google (0x18D1) ADB interfaces.
  3. Detects a currently-connected MediaTek / Tecno device and re-scans the bus
     so Windows binds the fresh driver.
  4. Registers the vendor IDs in %USERPROFILE%\\.android\\adb_usb.ini and
     restarts the ADB daemon.

Elevation: the installer relaunches the current executable with
"--install-drivers-elevated" via ShellExecuteW("runas"), so the user sees a
single UAC prompt. All progress is written to a log file that the GUI / web
suite tails live.

Honesty: the bundled INFs are unsigned. On stock Windows 11 with driver
signature enforcement ON, pnputil may refuse them — the installer detects that
exact failure and prints the remediation (Test Mode / Device Manager path)
instead of pretending it worked.
"""

import ctypes
import os
import re
import sys
import time
import platform
import subprocess
import tempfile
from typing import List, Tuple, Optional

LOG_TAG = "amt_pro_driver_install.log"
SENTINEL = "__RESULT__:"


def default_log_path() -> str:
    return os.path.join(tempfile.gettempdir(), LOG_TAG)


def is_admin() -> bool:
    if platform.system() != "Windows":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _log(path: str, line: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {line}"
    try:
        with open(path, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
            f.flush()
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass


def _run(cmd: List[str], log_path: str, timeout: int = 180) -> Tuple[int, str]:
    _log(log_path, "$ " + " ".join(cmd))
    try:
        p = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace", timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except FileNotFoundError:
        _log(log_path, "  [!] command not found: " + cmd[0])
        return 127, ""
    except subprocess.TimeoutExpired:
        _log(log_path, "  [!] timed out")
        return 124, ""
    out = p.stdout or ""
    for ln in out.splitlines():
        if ln.strip():
            _log(log_path, "   " + ln.strip())
    _log(log_path, f"   -> exit code {p.returncode}")
    return p.returncode, out


def _find_pnputil() -> Optional[str]:
    sysroot = os.environ.get("SystemRoot") or r"C:\Windows"
    for cand in (
        os.path.join(sysroot, "System32", "pnputil.exe"),
        os.path.join(sysroot, "Sysnative", "pnputil.exe"),
    ):
        if os.path.isfile(cand):
            return cand
    return None


def _app_base() -> str:
    """Repo root in dev, or the PyInstaller extraction dir when frozen."""
    base = getattr(sys, "_MEIPASS", None)
    if base and os.path.isdir(base):
        return base
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _stage_driver(inf_path: str, log_path: str, pnputil: str) -> bool:
    """pnputil /add-driver <inf> /install — stage + auto-bind present devices."""
    if not os.path.isfile(inf_path):
        _log(log_path, f"[!] INF not found: {inf_path}")
        return False
    code, out = _run([pnputil, "/add-driver", inf_path, "/install"], log_path)
    if code == 0:
        _log(log_path, f"[OK] Staged + installed: {os.path.basename(inf_path)}")
        return True
    # Older pnputil builds don't accept /install — retry plain staging.
    if re.search(r"invalid|unknown|usage|not recognized|incorrect", out, re.I):
        code, out = _run([pnputil, "/add-driver", inf_path], log_path)
        if code == 0:
            _log(log_path, f"[OK] Staged (no auto-bind on this build): {os.path.basename(inf_path)}")
            return True
    if re.search(r"signature|0x800b0100|0xe0000242|not signed", out, re.I):
        _log(log_path, f"[!] {os.path.basename(inf_path)}: blocked — Windows requires a signed driver (this INF is unsigned).")
    else:
        _log(log_path, f"[!] {os.path.basename(inf_path)}: pnputil failed (exit {code}).")
    return False


def _enum_connected_devices(log_path: str, pnputil: str) -> List[str]:
    """Return human-readable lines for connected MediaTek (0E8D) / Tecno (2E04) devices."""
    code, out = _run([pnputil, "/enum-devices", "/connected"], log_path, timeout=60)
    if code != 0:
        _log(log_path, "[!] pnputil /enum-devices not supported on this Windows build.")
        return []
    blocks, block, cur_key = [], {}, None

    def flush(b):
        if b:
            blocks.append(b)

    for raw in out.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(block)
            block, cur_key = {}, None
            continue
        m = re.match(r"^\s*([A-Za-z ]+):\s+(.*)$", line)
        if m:
            cur_key = m.group(1).strip()
            block[cur_key] = m.group(2).strip()
        elif cur_key:
            block[cur_key] = block.get(cur_key, "") + " " + line.strip()
    flush(block)

    lines = []
    for b in blocks:
        iid = b.get("Instance ID", "")
        if "VID_0E8D" in iid.upper() or "VID_2E04" in iid.upper():
            lines.append(
                f"{iid} | {b.get('Device Description','?')} | "
                f"class={b.get('Class Name','?')} | status={b.get('Status','?')} | "
                f"driver={b.get('Driver Name','?')}"
            )
    return lines


def run_driver_install(log_path: str, testsigning: bool = False) -> None:
    """The full privileged install procedure. Writes progress + a __RESULT__ sentinel."""
    _log(log_path, "=" * 66)
    _log(log_path, " AMT PRO — Windows driver installer (elevated)")
    _log(log_path, "=" * 66)

    if platform.system() != "Windows":
        _log(log_path, "[!] This installer only runs on Windows.")
        _log(log_path, SENTINEL + "ERROR")
        return
    if not is_admin():
        _log(log_path, "[!] Not running with Administrator rights.")
        _log(log_path, SENTINEL + "ERROR")
        return

    base = _app_base()
    pnputil = _find_pnputil()
    if not pnputil:
        _log(log_path, "[!] pnputil.exe not found — cannot install drivers.")
        _log(log_path, SENTINEL + "ERROR")
        return
    _log(log_path, f"pnputil : {pnputil}")
    _log(log_path, f"app dir : {base}")

    drivers_dir = os.path.join(base, "bin", "drivers")

    _log(log_path, "")
    _log(log_path, "[1/5] Installing MediaTek USB VCOM driver (Preloader / BROM / DA)...")
    vcom_ok = _stage_driver(os.path.join(drivers_dir, "cdc-acm.inf"), log_path, pnputil)

    _log(log_path, "")
    _log(log_path, "[2/5] Installing Android WinUSB (ADB / fastboot) driver...")
    adb_ok = _stage_driver(os.path.join(drivers_dir, "android_winusb.inf"), log_path, pnputil)

    _log(log_path, "")
    _log(log_path, "[3/5] Looking for a connected MediaTek / Tecno device...")
    devices = _enum_connected_devices(log_path, pnputil)
    if devices:
        for ln in devices:
            _log(log_path, "  device: " + ln)
    else:
        _log(log_path, "  No MediaTek (0E8D) / Tecno (2E04) device connected right now.")
        _log(log_path, "  Tip: put the phone in Preloader/BROM mode (power OFF -> plug USB, no buttons) and run this again.")

    _log(log_path, "")
    _log(log_path, "[4/5] Re-scanning the device bus so Windows binds the new driver...")
    _run([pnputil, "/scan-devices"], log_path, timeout=60)
    if vcom_ok:
        _log(log_path, "  VCOM staged OK. A connected phone should now show as 'MediaTek Preloader USB VCOM' / 'MediaTek BootROM USB Port' under Ports (COM & LPT).")
    else:
        _log(log_path, "  [!] VCOM driver was NOT staged (typically the unsigned-INF signature block).")
        _log(log_path, "  Remediation (pick one):")
        _log(log_path, "    1) Click 'Force-Install (Test Mode)' in the app, then REBOOT and run Install Tools & Drivers again.")
        _log(log_path, "    2) Or: Shift+Restart -> Troubleshoot -> Advanced -> Startup Settings -> 7 (disable signature enforcement), then run this again.")
        _log(log_path, "    3) Or manual: Device Manager -> the unknown 'MT65xx/MediaTek' device -> Update driver -> Browse -> Let me pick -> Ports -> MediaTek USB VCOM.")

    if testsigning:
        _log(log_path, "")
        _log(log_path, "[*] Test Mode requested — enabling testsigning (REBOOT required)...")
        code, out = _run(["bcdedit", "/set", "testsigning", "on"], log_path)
        if code == 0:
            _log(log_path, "[OK] Test signing enabled. REBOOT, then run 'Install Tools & Drivers' again.")
            _log(log_path, "     (undo later: bcdedit /set testsigning off)")
        else:
            _log(log_path, f"[!] bcdedit failed (exit {code}). You may need to run it manually from an admin prompt.")

    _log(log_path, "")
    _log(log_path, "[5/5] Registering vendor IDs + restarting ADB...")
    adb_ini = os.path.join(os.path.expanduser("~"), ".android", "adb_usb.ini")
    try:
        os.makedirs(os.path.dirname(adb_ini), exist_ok=True)
        ids = set()
        if os.path.isfile(adb_ini):
            with open(adb_ini, "r", encoding="utf-8", errors="replace") as f:
                ids = {ln.strip() for ln in f if ln.strip()}
        for vid in ("0x2e04", "0x0e8d", "0x18d1"):
            if vid not in ids:
                ids.add(vid)
                _log(log_path, f"  registered {vid} in adb_usb.ini")
        with open(adb_ini, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(ids)) + "\n")
    except Exception as e:
        _log(log_path, f"  [!] adb_usb.ini update failed: {e}")

    adb_exe = os.path.join(base, "bin", "adb.exe")
    if not os.path.isfile(adb_exe):
        adb_exe = os.path.join(base, "bin", "adb")
    if os.path.isfile(adb_exe):
        _run([adb_exe, "kill-server"], log_path, timeout=30)
        _run([adb_exe, "start-server"], log_path, timeout=30)
    else:
        _log(log_path, "  (adb binary not found — skipped daemon restart)")

    _log(log_path, "")
    if vcom_ok and adb_ok:
        _log(log_path, "[OK] Both drivers installed successfully.")
        _log(log_path, SENTINEL + "OK")
    elif vcom_ok or adb_ok:
        _log(log_path, "[!] Partial success — see the messages above.")
        _log(log_path, SENTINEL + "OK_WARN")
    else:
        _log(log_path, "[!] Driver install did not complete — see the messages above.")
        _log(log_path, SENTINEL + "ERROR")


def launch_elevated(log_path: str, testsigning: bool = False) -> Tuple[bool, str]:
    """Relaunch the current app elevated via UAC to run the installer."""
    if platform.system() != "Windows":
        return False, "Driver installer only runs on Windows."
    if is_admin():
        return True, "already-admin"
    exe = sys.executable
    script = os.path.abspath(sys.argv[0]) if sys.argv else ""
    params = f'--install-drivers-elevated "{log_path}"'
    if testsigning:
        params += " --testsigning"
    # Dev mode: relaunching python.exe needs the script path as the first argument.
    if script and not getattr(sys, "frozen", False):
        params = f'"{script}" ' + params
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
    except Exception as e:
        return False, f"Elevation failed: {e}"
    if rc > 32:
        return True, "Driver installer launched — accept the UAC prompt, then watch the console."
    return False, "Driver install cancelled (UAC declined) or elevation failed."


def start_driver_install(log_path: Optional[str] = None, testsigning: bool = False) -> Tuple[bool, str]:
    """Entry point for the GUI / web suite. Elevates if needed, then installs."""
    log_path = log_path or default_log_path()
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
    except Exception:
        pass
    if platform.system() != "Windows":
        return False, "The automatic driver installer is Windows-only."
    if is_admin():
        # Already elevated: run synchronously so the caller can report the result.
        run_driver_install(log_path, testsigning)
        return True, "Driver install finished — see the console log for the result."
    return launch_elevated(log_path, testsigning)


def handle_elevated_invocation(argv: List[str]) -> bool:
    """If this process was (re)launched to run the elevated installer, run it and return True.

    The GUI calls this at startup, before building the Tk window, so the UAC
    relaunch never shows a second UI.
    """
    if "--install-drivers-elevated" not in argv:
        return False
    try:
        idx = argv.index("--install-drivers-elevated")
        log_path = argv[idx + 1] if idx + 1 < len(argv) else default_log_path()
    except (ValueError, IndexError):
        log_path = default_log_path()
    run_driver_install(log_path, testsigning="--testsigning" in argv)
    return True
