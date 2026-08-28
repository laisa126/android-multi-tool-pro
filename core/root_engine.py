"""
Android Multi-Tool Pro - Root Engine
Automates Magisk & KernelSU root workflows, vbmeta verification disabling,
and su privilege diagnostics.
"""

import os
from typing import Tuple, List

class RootEngine:
    def __init__(self, adb_engine, fastboot_engine):
        self.adb = adb_engine
        self.fastboot = fastboot_engine

    def check_root_status(self) -> Tuple[bool, str]:
        """Checks if device has working su binary and root privileges."""
        code, out, _ = self.adb.run_cmd(["shell", "id"])
        if code == 0 and "uid=0(root)" in out:
            return True, "Device is Rooted (Direct root shell: uid=0)"

        code2, out2, _ = self.adb.run_cmd(["shell", "which", "su"])
        if code2 == 0 and ("su" in out2):
            return True, f"Su binary detected at {out2.strip()}"

        return False, "Not Rooted (No active su binary detected)"

    def flash_magisk_boot(self, boot_img_path: str, partition: str = "boot") -> Tuple[bool, str]:
        """Flashes Magisk patched boot or init_boot in Fastboot."""
        if not os.path.isfile(boot_img_path):
            return False, f"Image not found: {boot_img_path}"
        return self.fastboot.flash_partition(partition, boot_img_path)

    def flash_vbmeta_disabled(self, vbmeta_img_path: str) -> Tuple[bool, str]:
        """
        Flashes vbmeta image with dm-verity and verification disabled.
        Crucial step on Android 10, 11, 12, 13, 14 to avoid bootloops when rooting.
        """
        if not os.path.isfile(vbmeta_img_path):
            return False, f"VBMeta image not found: {vbmeta_img_path}"

        args = [
            "flash",
            "--disable-verity",
            "--disable-verification",
            "vbmeta",
            vbmeta_img_path
        ]
        code, out, err = self.fastboot.run_cmd(args)
        combined = f"{out}\n{err}".strip()
        if "OKAY" in combined:
            return True, "VBMeta flashed with verification disabled successfully!"
        return False, f"VBMeta flash failed: {combined}"

    def install_magisk_apk(self, apk_path: str) -> Tuple[bool, str]:
        return self.adb.install_apk(apk_path, grant_permissions=True)
