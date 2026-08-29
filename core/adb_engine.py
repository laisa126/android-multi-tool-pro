"""
Android Multi-Tool Pro - ADB Core Engine
Handles low-level and high-level ADB operations, device detection, diagnostics,
reboot sequences, and package management.
"""

import subprocess
import os
import sys
import shutil
import re
import platform
from typing import Dict, List, Optional, Tuple

from .connection_guide import classify_adb_state

class ADBEngine:
    def __init__(self, custom_adb_path: Optional[str] = None):
        self.adb_path = custom_adb_path or self._find_adb()
        self.connected_device = None
        self.log_callback = None  # optional: fn(line: str, level: str) for live command echo
        self._ensure_vendor_ids()

    def _emit(self, line: str, level: str = "info"):
        if self.log_callback:
            try:
                self.log_callback(line, level)
            except Exception:
                pass

    def _ensure_vendor_ids(self):
        """Ensures Transsion (Tecno/Infinix) and MediaTek VIDs exist in adb_usb.ini.

        NOTE: adb_usb.ini is only consulted by adb on Linux / macOS.
        On Windows, ADB uses WinUSB drivers and ignores this file entirely —
        the Windows fix is the bundled driver INF (install_drivers.bat).
        """
        if platform.system() == "Windows":
            return
        try:
            home = os.path.expanduser("~")
            android_dir = os.path.join(home, ".android")
            os.makedirs(android_dir, exist_ok=True)
            ini_path = os.path.join(android_dir, "adb_usb.ini")
            existing = ""
            if os.path.isfile(ini_path):
                with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                    existing = f.read()

            vids_to_add = ["0x2e04", "0x0e8d", "0x18d1", "0x04e8", "0x2717"]
            added = False
            for vid in vids_to_add:
                if vid not in existing:
                    existing += f"\n{vid}"
                    added = True

            if added:
                with open(ini_path, "w", encoding="utf-8") as f:
                    f.write(existing.strip() + "\n")
        except Exception:
            pass

    def _find_adb(self) -> str:
        # Check bundled bin folder first
        local_bin = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bin")
        ext = ".exe" if platform.system() == "Windows" else ""
        bundled_adb = os.path.join(local_bin, f"adb{ext}")
        if os.path.isfile(bundled_adb) and os.access(bundled_adb, os.X_OK):
            return bundled_adb

        # Check system PATH
        system_adb = shutil.which("adb")
        if system_adb:
            return system_adb

        # Fallback default name
        return f"adb{ext}"

    def run_cmd(self, args: List[str], timeout: int = 8) -> Tuple[int, str, str]:
        cmd = [self.adb_path]
        if self.connected_device and args and args[0] not in ["devices", "start-server", "kill-server", "version"]:
            cmd.extend(["-s", self.connected_device])
        cmd.extend(args)
        self._emit(f"$ {' '.join(cmd)}", "muted")

        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                shell=False
            )
            self._emit_output(res.stdout, res.returncode, res.stderr)
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except FileNotFoundError:
            msg = f"ADB executable not found at '{self.adb_path}'. Please install platform-tools."
            self._emit(msg, "error")
            return -1, "", msg
        except subprocess.TimeoutExpired:
            msg = f"Command timed out after {timeout} seconds (device not responding or USB disconnected)."
            self._emit(msg, "error")
            return -2, "", msg
        except Exception as e:
            self._emit(str(e), "error")
            return -3, "", str(e)

    def _emit_output(self, stdout: str, returncode: int, stderr: str = "", cap: int = 15):
        """Echo command output to the log callback, capped to avoid flooding."""
        if not self.log_callback:
            return
        out_lines = (stdout or "").splitlines()
        for ln in out_lines[:cap]:
            self._emit(ln, "info")
        if len(out_lines) > cap:
            self._emit(f"... ({len(out_lines) - cap} more output lines suppressed)", "muted")
        if returncode != 0 and stderr and stderr.strip():
            for ln in stderr.strip().splitlines()[:cap]:
                self._emit(ln, "error")

    def get_devices(self) -> List[Dict[str, str]]:
        """Return REAL adb devices only (serial, state, details, kind, guidance).

        Hardware-bus pseudo-serials are NOT merged here anymore — they live in
        get_hardware_usb_devices() and are tagged diagnostic-only, because adb
        cannot address them.
        """
        code, out, err = self.run_cmd(["devices", "-l"], timeout=12)
        devices = []
        if code == 0:
            devices = self._parse_devices_output(out)

        # If the daemon was unreachable, (re)start it once and retry.
        if not devices and self._looks_like_daemon_issue(out, err):
            self._ensure_server()
            code, out, _ = self.run_cmd(["devices", "-l"], timeout=12)
            if code == 0:
                devices = self._parse_devices_output(out)

        for d in devices:
            d["kind"] = "adb"
            d["adb_usable"] = True
            d["guidance"] = classify_adb_state(d.get("state", ""))
        return devices

    def _parse_devices_output(self, out: str) -> List[Dict[str, str]]:
        devices = []
        for line in (out or "").splitlines():
            line = line.strip()
            if not line:
                continue
            low = line.lower()
            if "list of devices" in low or "daemon" in low or line.startswith("*"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            devices.append({
                "serial": parts[0],
                "state": parts[1],
                "details": " ".join(parts[2:]) if len(parts) > 2 else "",
            })
        return devices

    def _looks_like_daemon_issue(self, out: str, err: str) -> bool:
        text = (out + "\n" + err).lower()
        return any(k in text for k in ("daemon", "cannot connect", "connection refused", "adb server"))

    def _ensure_server(self) -> bool:
        code, _, _ = self.run_cmd(["start-server"], timeout=15)
        return code == 0

    def get_adb_version(self) -> str:
        code, out, _ = self.run_cmd(["version"], timeout=8)
        if code == 0 and out:
            return out.splitlines()[0].strip()
        return "unknown"

    def get_hardware_usb_devices(self) -> List[Dict[str, str]]:
        """
        Direct USB physical bus inspection.
        Captures serial numbers for Android 16+ devices even when ADB daemon
        is restricted by OS lockscreen or USB charging mode.
        """
        found = []
        system = platform.system()

        # Known Android & GSM OEM Vendor IDs
        known_vids = {
            "2E04": "Tecno / Infinix (Transsion)",
            "0E8D": "MediaTek (Dimensity / Helio Preloader / BROM)",
            "18D1": "Google / Android AOSP",
            "04E8": "Samsung Electronics",
            "2717": "Xiaomi / Redmi / POCO",
            "22D9": "Oppo / Realme / OnePlus",
            "2A70": "OnePlus",
            "05C6": "Qualcomm HS-USB"
        }

        try:
            if system == "Windows":
                # Method 1: Ultra-fast native Windows Registry inspection (0.002s, ZERO PowerShell lag)
                try:
                    import winreg
                    usb_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\USB")
                    idx = 0
                    while True:
                        try:
                            vid_pid_str = winreg.EnumKey(usb_key, idx)
                            idx += 1
                            m = re.search(r'VID_([0-9A-Fa-f]{4})&PID_([0-9A-Fa-f]{4})', vid_pid_str)
                            if m:
                                vid = m.group(1).upper()
                                if vid in known_vids:
                                    vendor = known_vids[vid]
                                    sub_k = winreg.OpenKey(usb_key, vid_pid_str)
                                    s_idx = 0
                                    while True:
                                        try:
                                            ser_str = winreg.EnumKey(sub_k, s_idx)
                                            s_idx += 1
                                            if ser_str and not ser_str.startswith("&"):
                                                inst_k = winreg.OpenKey(sub_k, ser_str)
                                                try:
                                                    desc, _ = winreg.QueryValueEx(inst_k, "DeviceDesc")
                                                    name = desc.split(";")[-1] if ";" in desc else desc
                                                except Exception:
                                                    name = f"{vendor} Device"
                                                found.append({
                                                    "serial": ser_str,
                                                    "state": "device (USB HW bus)",
                                                    "details": f"{vendor} - {name} [Hardware Bus]",
                                                    "vid": vid,
                                                    "kind": "hardware",
                                                    "adb_usable": False,
                                                })
                                        except OSError:
                                            break
                        except OSError:
                            break
                except Exception:
                    pass

                # Method 2: Fast PowerShell fallback only if winreg yielded nothing (Strict 1.5s timeout)
                if not found:
                    ps_cmd = (
                        "Get-PnpDevice -PresentOnly | "
                        "Where-Object { $_.InstanceId -match 'VID_(2E04|0E8D|18D1|04E8|2717|22D9|2A70|05C6)' } | "
                        "Select-Object -Property InstanceId, FriendlyName, Class | "
                        "ConvertTo-Json -Compress"
                    )
                    res = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_cmd],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=1.5
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        import json
                        try:
                            raw = json.loads(res.stdout.strip())
                            items = raw if isinstance(raw, list) else [raw]
                            for item in items:
                                inst_id = item.get("InstanceId", "")
                                name = item.get("FriendlyName") or "Android 16+ Device"
                                m = re.search(r'VID_([0-9A-Fa-f]{4})&PID_([0-9A-Fa-f]{4})\\([^\\]+)', inst_id)
                                if m:
                                    vid = m.group(1).upper()
                                    serial = m.group(3).strip()
                                    vendor = known_vids.get(vid, "Android Device")
                                    found.append({
                                        "serial": serial,
                                        "state": "device (USB HW bus)",
                                        "details": f"{vendor} - {name} [Hardware Bus]",
                                        "vid": vid,
                                        "kind": "hardware",
                                        "adb_usable": False,
                                    })
                        except Exception:
                            pass

            elif system == "Linux":
                # Direct sysfs USB bus inspection on Linux
                usb_base = "/sys/bus/usb/devices"
                if os.path.isdir(usb_base):
                    for dev_dir in os.listdir(usb_base):
                        p = os.path.join(usb_base, dev_dir)
                        vid_file = os.path.join(p, "idVendor")
                        ser_file = os.path.join(p, "serial")
                        prod_file = os.path.join(p, "product")
                        if os.path.isfile(vid_file) and os.path.isfile(ser_file):
                            try:
                                with open(vid_file, "r") as f:
                                    vid = f.read().strip().upper()
                                with open(ser_file, "r") as f:
                                    ser = f.read().strip()
                                prod = ""
                                if os.path.isfile(prod_file):
                                    with open(prod_file, "r") as f:
                                        prod = f.read().strip()
                                if vid in known_vids and ser:
                                    found.append({
                                        "serial": ser,
                                        "state": "device (USB HW bus)",
                                        "details": f"{known_vids[vid]} {prod} [Direct sysfs]",
                                        "vid": vid,
                                        "kind": "hardware",
                                        "adb_usable": False,
                                    })
                            except Exception:
                                pass
        except Exception:
            pass

        return found

    def set_active_device(self, serial: str):
        self.connected_device = serial

    def get_device_info(self) -> Dict[str, str]:
        """Fetch comprehensive device hardware and OS parameters."""
        info = {
            "model": "Unknown",
            "brand": "Unknown",
            "device": "Unknown",
            "android_version": "Unknown",
            "sdk_level": "Unknown",
            "build_id": "Unknown",
            "security_patch": "Unknown",
            "cpu_abi": "Unknown",
            "battery_level": "Unknown",
            "root_status": "No",
            "serial": self.connected_device or "N/A"
        }

        # Query build properties in a single batch command for speed
        code, out, _ = self.run_cmd(["shell", "getprop"])
        if code == 0:
            props = {}
            for line in out.splitlines():
                m = re.match(r'\[(.*?)\]:\s*\[(.*?)\]', line)
                if m:
                    props[m.group(1)] = m.group(2)

            info["brand"] = props.get("ro.product.brand", props.get("ro.product.manufacturer", "Unknown")).capitalize()
            info["model"] = props.get("ro.product.model", "Unknown")
            info["device"] = props.get("ro.product.device", "Unknown")
            info["android_version"] = props.get("ro.build.version.release", "Unknown")
            info["sdk_level"] = props.get("ro.build.version.sdk", "Unknown")
            info["build_id"] = props.get("ro.build.display.id", props.get("ro.build.id", "Unknown"))
            info["security_patch"] = props.get("ro.build.version.security_patch", "Unknown")
            info["cpu_abi"] = props.get("ro.product.cpu.abi", "Unknown")

        # Battery check
        b_code, b_out, _ = self.run_cmd(["shell", "dumpsys", "battery"])
        if b_code == 0:
            for line in b_out.splitlines():
                if "level:" in line:
                    info["battery_level"] = line.split(":")[-1].strip() + "%"
                    break

        # Root check
        r_code, r_out, _ = self.run_cmd(["shell", "which", "su"])
        if r_code == 0 and ("su" in r_out or "bin" in r_out):
            info["root_status"] = "Yes (su binary found)"

        return info

    def reboot(self, target_mode: str = "") -> Tuple[bool, str]:
        """Reboot device into normal, recovery, bootloader, edl, or download mode."""
        valid_modes = ["", "recovery", "bootloader", "fastboot", "edl", "download", "sideload"]
        target = target_mode.lower().strip()
        if target not in valid_modes:
            return False, f"Invalid target mode: {target_mode}"

        args = ["reboot"]
        if target:
            args.append(target)

        code, out, err = self.run_cmd(args)
        if code == 0:
            msg = f"Device successfully instructed to reboot into: {target_mode or 'normal OS'}"
            return True, msg
        else:
            return False, f"Reboot failed: {err or out}"

    def install_apk(self, apk_path: str, grant_permissions: bool = True) -> Tuple[bool, str]:
        if not os.path.isfile(apk_path):
            return False, f"File not found: {apk_path}"

        args = ["install", "-r"]
        if grant_permissions:
            args.append("-g")
        args.append(apk_path)

        code, out, err = self.run_cmd(args, timeout=120)
        if "Success" in out:
            return True, "APK successfully installed."
        return False, f"Install failed: {out or err}"

    def uninstall_package(self, package_name: str, keep_data: bool = False) -> Tuple[bool, str]:
        args = ["uninstall"]
        if keep_data:
            args.append("-k")
        args.append(package_name)

        code, out, err = self.run_cmd(args)
        if "Success" in out:
            return True, f"Package {package_name} uninstalled."
        return False, f"Failed: {out or err}"

    def disable_package(self, package_name: str) -> Tuple[bool, str]:
        code, out, err = self.run_cmd(["shell", "pm", "disable-user", "--user", "0", package_name])
        if "disabled" in out.lower() or "state" in out.lower():
            return True, f"Disabled {package_name}"
        return False, f"Could not disable: {out or err}"

    def take_screenshot(self, destination_path: str) -> Tuple[bool, str]:
        remote_tmp = "/sdcard/amt_screenshot.png"
        code, _, err = self.run_cmd(["shell", "screencap", "-p", remote_tmp])
        if code != 0:
            return False, f"Failed capturing screen: {err}"

        pull_code, _, pull_err = self.run_cmd(["pull", remote_tmp, destination_path])
        self.run_cmd(["shell", "rm", remote_tmp])

        if pull_code == 0:
            return True, f"Screenshot saved to {destination_path}"
        return False, f"Failed downloading screenshot: {pull_err}"

    def sideload_ota(self, ota_zip: str, progress_cb=None, timeout: int = 600) -> Tuple[bool, str]:
        """Push an OTA zip to a device in recovery 'sideload' mode.

        IMPORTANT: this is the channel that works with USB debugging DISABLED —
        recovery's adbd is authorized by the 'Apply update from ADB' menu item,
        not by Developer Options. Returns (ok, message).
        """
        if not os.path.isfile(ota_zip):
            return False, f"OTA zip not found: {ota_zip}"

        # Confirm the device is actually in sideload mode
        code, out, _ = self.run_cmd(["devices", "-l"], timeout=12)
        sideload_serials = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1].lower() == "sideload":
                sideload_serials.append(parts[0])
        if code != 0 or not sideload_serials:
            return False, (
                "No device in 'sideload' mode. Boot to recovery -> 'Apply update from ADB', "
                "then connect USB. (This needs NO USB debugging.)"
            )

        # Target the sideload serial directly (run_cmd adds -s automatically when
        # connected_device is set, but here we want the exact sideload device).
        if self.connected_device:
            args = ["sideload", ota_zip]
        else:
            args = ["-s", sideload_serials[0], "sideload", ota_zip]
        code, out, err = self.run_cmd(args, timeout=timeout)
        combined = (out + "\n" + err).strip()
        if code == 0 and ("success" in combined.lower() or "100%" in combined or "done" in combined.lower()):
            return True, f"OTA sideload complete: {combined}"
        return False, f"Sideload failed: {combined or 'unknown error'}"
