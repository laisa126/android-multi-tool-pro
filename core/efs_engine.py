"""
Android Multi-Tool Pro - EFS / NVRAM / Baseband Backup & Restore Engine
Safeguards critical cellular modem calibration partitions to prevent
'No Service' and 'Baseband Unknown' corruption during flashing.
"""

import os


class EFSEngine:
    def __init__(self, adb_engine, fastboot_engine):
        self.adb = adb_engine
        self.fastboot = fastboot_engine

    def detect_efs_partitions(self) -> list[str]:
        """Detects whether device uses Qualcomm (modemst1/2), MTK (nvram/nvdata), or Samsung (efs)."""
        # Read partition list via ADB
        code, out, _ = self.adb.run_cmd(["shell", "ls", "-l", "/dev/block/by-name/"])
        detected = []
        target_keys = ["efs", "sec_efs", "nvram", "nvdata", "modemst1", "modemst2", "fsg", "fsc", "persist"]

        if code == 0:
            for line in out.splitlines():
                for k in target_keys:
                    if k in line and k not in detected:
                        detected.append(k)

        if not detected:
            # Standard default fallback
            detected = ["modemst1", "modemst2", "fsg", "nvram", "nvdata", "efs"]

        return detected

    def backup_partition(self, partition: str, destination_folder: str) -> tuple[bool, str]:
        """Dumps raw block image of the partition to PC via ADB."""
        os.makedirs(destination_folder, exist_ok=True)
        local_file = os.path.join(destination_folder, f"{partition}_backup.img")
        remote_file = f"/sdcard/{partition}_tmp.img"

        # dd dump on phone
        code, _, err = self.adb.run_cmd([
            "shell", "su", "-c",
            f"dd if=/dev/block/by-name/{partition} of={remote_file} bs=4096"
        ])

        if code != 0:
            # Try without su if rooted via recovery
            code, _, err = self.adb.run_cmd([
                "shell",
                f"dd if=/dev/block/by-name/{partition} of={remote_file} bs=4096"
            ])

        if code != 0:
            return False, f"Dump failed: {err}"

        # Pull to PC
        p_code, _, p_err = self.adb.run_cmd(["pull", remote_file, local_file])
        self.adb.run_cmd(["shell", "rm", remote_file])

        if p_code == 0 and os.path.isfile(local_file):
            return True, f"Backup saved: {local_file}"
        return False, f"Failed transferring {partition}: {p_err}"

    def restore_partition_fastboot(self, partition: str, image_path: str) -> tuple[bool, str]:
        """Restores modem partition via Fastboot."""
        if not os.path.isfile(image_path):
            return False, f"File not found: {image_path}"
        return self.fastboot.flash_partition(partition, image_path)
