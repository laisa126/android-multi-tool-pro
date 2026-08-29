""" 
Android Multi-Tool Pro - MediaTek Scatter File Flasher Engine
Specifically designed for Transsion Tecno Camon 50 Pro.
Variants: Camon 50 Pro 4G (CN5c) = MT6789 Helio G200 Ultimate (default target);
          Camon 50 Pro 5G (CN7c) = MT6878 Dimensity 7400 Ultimate.
Parses scatter.txt, maps UFS partition offsets, and orchestrates multi-partition flashing.
"""

import os
import re
from typing import Dict, List, Tuple, Optional

class ScatterFlasher:
    """
    Parses MediaTek XML / TXT scatter configuration files and maps
    partition flash targets for Tecno Camon 50 Pro.
    """
    def __init__(self, scatter_file_path: Optional[str] = None):
        self.scatter_path = scatter_file_path

    def parse_scatter(self, path: str) -> Tuple[bool, List[Dict[str, any]], str]:
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

    def build_tecno_camon50_partition_map(self) -> List[Dict[str, str]]:
        """Default hardware partition map for Tecno Camon 50 Pro 4G (TECNO CN5c - UFS 2.2)."""
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

    # ------------------------------------------------------------------
    # Tecno Camon 50 Pro scatter file generation (variant-aware)
    # ------------------------------------------------------------------
    CAMON50_VARIANTS: Dict[str, Dict[str, str]] = {
        "cn5c": {
            "label": "Tecno Camon 50 Pro 4G (TECNO-CN5c)",
            "platform": "MT6789",
            "platform_desc": "MT6789 (Helio G200 Ultimate)",
            "project": "tecno_cn5c",
            "preloader": "preloader_tecno_cn5c.bin",
            "storage": "UFS 2.2",
        },
        "cn7c": {
            "label": "Tecno Camon 50 Pro 5G (TECNO-CN7c)",
            "platform": "MT6878",
            "platform_desc": "MT6878 (Dimensity 7400 Ultimate)",
            "project": "tecno_cn7c",
            "preloader": "preloader_tecno_cn7c.bin",
            "storage": "UFS 3.1",
        },
    }

    TECNO_CAMON50_SCATTER_LAYOUT: List[Tuple[str, str, int, int]] = [
        # (partition_name, file_name, linear_start_addr, partition_size)
        # "__PRELOADER__" is substituted with the variant's preloader file name.
        ("preloader",      "__PRELOADER__",            0x0,         0x400000),
        ("init_boot",      "init_boot.img",            0x400000,    0x800000),
        ("boot",           "boot.img",                 0x1000000,   0x2000000),
        ("recovery",       "recovery.img",             0x3000000,   0x2000000),
        ("dtbo",           "dtbo.img",                 0x5000000,   0x200000),
        ("vbmeta",         "vbmeta.img",               0x5200000,   0x80000),
        ("vbmeta_system",  "vbmeta_system.img",        0x5280000,   0x80000),
        ("vbmeta_vendor",  "vbmeta_vendor.img",        0x5300000,   0x80000),
        ("nvram",          "nvram.img",                0x5800000,   0x500000),
        ("nvdata",         "nvdata.img",               0x5D00000,   0x2000000),
        ("protect1",       "protect1.img",             0x7D00000,   0xA00000),
        ("protect2",       "protect2.img",             0x8700000,   0xA00000),
        ("frp",            "frp.img",                  0x9100000,   0x100000),
        ("md1img",         "md1img.img",               0x9200000,   0xC800000),
        ("spmfw",          "spmfw.img",                0x15A00000,  0x100000),
        ("metadata",       "metadata.img",             0x15B00000,  0x1000000),
        ("super",          "super.img",                0x16B00000,  0xE0000000),
        ("userdata",       "userdata.img",             0xF6B00000,  0x80000000),
    ]

    @staticmethod
    def default_scatter_output_path() -> str:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "bin", "scatter", "tecno_camon50_pro_4g_cn5c_scatter.txt")

    def generate_tecno_camon50_scatter(self, output_path: Optional[str] = None,
                                       variant: str = "cn5c") -> Tuple[bool, str]:
        """Write a real MTK-format scatter file for Tecno Camon 50 Pro.

        Default variant is CN5c (4G, MT6789 — the primary target). Pass variant="cn7c"
        for the 5G (MT6878) template. Addresses are a template — replace with the
        firmware package's official scatter for production flashing.
        """
        info = self.CAMON50_VARIANTS.get(variant, self.CAMON50_VARIANTS["cn5c"])
        if output_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_path = os.path.join(base, "bin", "scatter",
                                       f"tecno_camon50_pro_{'5g_cn7c' if variant == 'cn7c' else '4g_cn5c'}_scatter.txt")
        path = output_path
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except Exception:
            pass

        lines = []
        lines.append("###############################################################################")
        lines.append("##  Android Multi-Tool Pro — MediaTek Scatter File")
        lines.append(f"##  Project : {info['label']}")
        lines.append(f"##  Platform: {info['platform_desc']} | Storage: {info['storage']}")
        lines.append("##  NOTE: template addresses — replace with firmware-provided scatter to flash.")
        lines.append("###############################################################################")
        lines.append("")
        lines.append("- general: MTK_PLATFORM_CFG")
        lines.append("  info:")
        lines.append("    - config_version: V1.1.2")
        lines.append(f"      platform: {info['platform']}")
        lines.append(f"      project: {info['project']}")
        lines.append("      storage: UFS")
        lines.append("      boot_channel: MSDC_0")
        lines.append("      block_size: 0x200000")
        lines.append("")
        lines.append("###############################################################################")
        lines.append("##  Layout Setting")
        lines.append("###############################################################################")
        lines.append("")

        for idx, (name, fname, addr, size) in enumerate(self.TECNO_CAMON50_SCATTER_LAYOUT):
            if fname == "__PRELOADER__":
                fname = info["preloader"]
            lines.append(f"- partition_index: SYS{idx}")
            lines.append(f"  partition_name: {name}")
            lines.append(f"  file_name: {fname}")
            lines.append("  is_download: true")
            lines.append("  type: NORMAL_ROM")
            lines.append(f"  linear_start_addr: 0x{addr:X}")
            lines.append(f"  physical_start_addr: 0x{addr:X}")
            lines.append(f"  partition_size: 0x{size:X}")
            lines.append("  region: EMMC_USER")
            lines.append("  storage: HW_STORAGE_UFS")
            lines.append("  boundary_check: true")
            lines.append("  is_reserved: false")
            lines.append("  operation_type: UPDATE")
            lines.append("  reserve: 0x00")
            lines.append("")

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True, path
        except Exception as e:
            return False, f"Failed writing scatter file: {e}"

    def verify_tecno_camon50_scatter(self) -> Dict[str, any]:
        """Verify the CN5c scatter file exists and parses cleanly."""
        path = self.default_scatter_output_path()
        result = {
            "path": path,
            "exists": os.path.isfile(path),
            "partitions": 0,
            "parse_ok": False,
            "message": "",
        }
        if not result["exists"]:
            result["message"] = "Scatter file missing — run generate_tecno_camon50_scatter()."
            return result
        ok, parts, msg = self.parse_scatter(path)
        result["parse_ok"] = ok
        result["partitions"] = len(parts)
        result["message"] = msg
        return result
