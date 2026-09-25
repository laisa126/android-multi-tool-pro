"""
Android Multi-Tool Pro - MediaTek Scatter File Flasher Engine
Specifically designed for Transsion Tecno Camon 50 Pro (MT6878 / MT6897 / MT6789).
Parses scatter.txt, maps UFS partition offsets, and orchestrates multi-partition flashing.
"""

import os
import re


class ScatterFlasher:
    """
    Parses MediaTek XML / TXT scatter configuration files and maps
    partition flash targets for Tecno Camon 50 Pro.
    """
    def __init__(self, scatter_file_path: str | None = None):
        self.scatter_path = scatter_file_path

    def parse_scatter(self, path: str) -> tuple[bool, list[dict[str, any]], str]:
        if not os.path.isfile(path):
            return False, [], f"Scatter file not found: {path}"

        partitions = []
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Parse standard MTK scatter blocks
            raw_blocks = content.split("- partition_index:")
            for b in raw_blocks[1:]:
                p_name_match = re.search(r"partition_name:\s*([^\r\n]+)", b)
                f_name_match = re.search(r"file_name:\s*([^\r\n]+)", b)
                start_match = re.search(r"linear_start_addr:\s*(0x[0-9a-fA-F]+)", b)
                boundary_match = re.search(r"boundary_check:\s*([^\r\n]+)", b)

                if p_name_match:
                    name = p_name_match.group(1).strip()
                    file_name = f_name_match.group(1).strip() if f_name_match else "NONE"
                    start = start_match.group(1).strip() if start_match else "0x0"
                    partitions.append({
                        "name": name,
                        "file": file_name,
                        "offset": start,
                        "enabled": (file_name != "NONE")
                    })

            return True, partitions, f"Successfully parsed {len(partitions)} partition targets from scatter."
        except Exception as e:
            return False, [], f"Scatter parse error: {e}"

    def build_tecno_camon50_partition_map(self) -> list[dict[str, str]]:
        """Default hardware partition map for Tecno Camon 50 Pro (TECNO CN5c - UFS Storage)."""
        return [
            {"partition": "preloader", "file": "preloader_tecno_cn5c.bin", "target": "UFS Boot1"},
            {"partition": "init_boot", "file": "init_boot.img", "target": "Android 15/16 Kernel Ramdisk"},
            {"partition": "boot", "file": "boot.img", "target": "Kernel & Drivers"},
            {"partition": "vbmeta", "file": "vbmeta.img", "target": "AVB 2.0 Security Header"},
            {"partition": "super", "file": "super.img", "target": "Dynamic System/Vendor/Product"},
            {"partition": "md1img", "file": "md1img.img", "target": "Cellular Modem Baseband Firmware"},
            {"partition": "spmfw", "file": "spmfw.img", "target": "Dimensity Power Management Firmware"},
            {"partition": "recovery", "file": "recovery.img", "target": "Recovery OS"},
            {"partition": "persist", "file": "persist.img", "target": "Factory Calibration & Sensors"}
        ]
