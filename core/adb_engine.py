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

class ADBEngine:
    def __init__(self, custom_adb_path: Optional[str] = None):
        self.adb_path = custom_adb_path or self._find_adb()
        self.connected_device = None

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

    def run_cmd(self, args: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        cmd = [self.adb_path]
        if self.connected_device and args and args[0] not in ["devices", "start-server", "kill-server", "version"]:
            cmd.extend(["-s", self.connected_device])
        cmd.extend(args)

        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                shell=False
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except FileNotFoundError:
            return -1, "", f"ADB executable not found at '{self.adb_path}'. Please install platform-tools."
        except subprocess.TimeoutExpired:
            return -2, "", f"Command timed out after {timeout} seconds."
        except Exception as e:
            return -3, "", str(e)

    def get_devices(self) -> List[Dict[str, str]]:
        code, out, _ = self.run_cmd(["devices", "-l"])
        devices = []
        if code != 0:
            return devices

        lines = out.splitlines()
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                state = parts[1]
                details = " ".join(parts[2:]) if len(parts) > 2 else ""
                devices.append({
                    "serial": serial,
                    "state": state,
                    "details": details
                })
        return devices

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
