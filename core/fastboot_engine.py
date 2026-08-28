"""
Android Multi-Tool Pro - Fastboot Core Engine
Handles low-level Fastboot partition flashing, bootloader unlocking/locking,
and bootloader variables inspection.
"""

import subprocess
import os
import shutil
import platform
from typing import Dict, List, Optional, Tuple

class FastbootEngine:
    def __init__(self, custom_fastboot_path: Optional[str] = None):
        self.fastboot_path = custom_fastboot_path or self._find_fastboot()
        self.connected_device = None

    def _find_fastboot(self) -> str:
        local_bin = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bin")
        ext = ".exe" if platform.system() == "Windows" else ""
        bundled = os.path.join(local_bin, f"fastboot{ext}")
        if os.path.isfile(bundled) and os.access(bundled, os.X_OK):
            return bundled

        system_fb = shutil.which("fastboot")
        if system_fb:
            return system_fb

        return f"fastboot{ext}"

    def run_cmd(self, args: List[str], timeout: int = 60) -> Tuple[int, str, str]:
        cmd = [self.fastboot_path]
        if self.connected_device and args and args[0] != "devices":
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
            # Fastboot frequently outputs info to stderr
            combined = (res.stdout + "\n" + res.stderr).strip()
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except FileNotFoundError:
            return -1, "", f"Fastboot executable not found at '{self.fastboot_path}'."
        except subprocess.TimeoutExpired:
            return -2, "", f"Fastboot command timed out after {timeout} seconds."
        except Exception as e:
            return -3, "", str(e)

    def get_devices(self) -> List[Dict[str, str]]:
        code, out, err = self.run_cmd(["devices"])
        devices = []
        combined = (out + "\n" + err).strip()
        for line in combined.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1].lower() in ["fastboot", "fastbootd"]:
                devices.append({
                    "serial": parts[0],
                    "mode": parts[1]
                })
        return devices

    def set_active_device(self, serial: str):
        self.connected_device = serial

    def get_device_vars(self) -> Dict[str, str]:
        code, out, err = self.run_cmd(["getvar", "all"], timeout=15)
        raw = out + "\n" + err
        vars_dict = {}
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("(bootloader)"):
                line = line.replace("(bootloader)", "").strip()
            if ":" in line:
                k, v = line.split(":", 1)
                vars_dict[k.strip()] = v.strip()
        return vars_dict

    def flash_partition(self, partition: str, image_path: str) -> Tuple[bool, str]:
        if not os.path.isfile(image_path):
            return False, f"Image file not found: {image_path}"

        code, out, err = self.run_cmd(["flash", partition, image_path], timeout=180)
        output = f"{out}\n{err}".strip()
        if "OKAY" in output:
            return True, f"Successfully flashed {partition} with {os.path.basename(image_path)}"
        return False, f"Flashing {partition} failed: {output}"

    def erase_partition(self, partition: str) -> Tuple[bool, str]:
        code, out, err = self.run_cmd(["erase", partition], timeout=60)
        output = f"{out}\n{err}".strip()
        if "OKAY" in output:
            return True, f"Successfully erased {partition}"
        return False, f"Erase failed: {output}"

    def unlock_bootloader(self) -> Tuple[bool, str]:
        # Try modern Android standard first
        code, out, err = self.run_cmd(["flashing", "unlock"], timeout=30)
        output = f"{out}\n{err}".strip()
        if "OKAY" in output:
            return True, "Flashing unlock command accepted. Confirm on device screen!"

        # Fallback to legacy oem unlock
        code2, out2, err2 = self.run_cmd(["oem", "unlock"], timeout=30)
        output2 = f"{out2}\n{err2}".strip()
        if "OKAY" in output2:
            return True, "OEM unlock command accepted. Confirm on device screen!"

        return False, f"Bootloader unlock failed: {output2 or output}"

    def lock_bootloader(self) -> Tuple[bool, str]:
        code, out, err = self.run_cmd(["flashing", "lock"], timeout=30)
        output = f"{out}\n{err}".strip()
        if "OKAY" in output:
            return True, "Lock command sent. Confirm on device screen!"

        code2, out2, err2 = self.run_cmd(["oem", "lock"], timeout=30)
        output2 = f"{out2}\n{err2}".strip()
        if "OKAY" in output2:
            return True, "OEM lock command sent. Confirm on device screen!"

        return False, f"Lock failed: {output2 or output}"

    def reboot(self, target: str = "") -> Tuple[bool, str]:
        args = ["reboot"]
        if target:
            args.append(target)
        code, out, err = self.run_cmd(args)
        if "OKAY" in (out + err):
            return True, f"Rebooted to {target or 'system'}"
        return False, f"Reboot failed: {err or out}"
