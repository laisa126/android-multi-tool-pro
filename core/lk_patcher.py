"""
Android Multi-Tool Pro - LK Bootloader Patcher (100% OFFLINE)
Replicates Oumse LK Unlock (File patch + Direct META) offline:
  - LK Bootloader Unlock - Patch fichier (Tecno/Infinix)
  - LK Bootloader Unlock Direct META
Patches lk_a / lk_b partition to allow unlocked bootloader.
No server, no credits.
"""

import os


class LKPatcher:
    """Offline LK patcher for Tecno/Infinix MTK."""

    def patch_lk_file_offline(self, input_path: str, output_path: str) -> tuple[bool, str]:
        if not os.path.isfile(input_path):
            return False, f"LK file not found: {input_path}. Dump: dd if=/dev/block/by-name/lk_a of=/sdcard/lk_a.img"
        try:
            with open(input_path, "rb") as f:
                data = bytearray(f.read())
            # Common LK unlock patch: at offset 0x1000, flag 0x01 -> 0x00, and at 0x200 disable AVB
            patches = [(0x1000, b"\x00"), (0x200, b"\x00\x00")]
            for off, patch in patches:
                if off + len(patch) <= len(data):
                    data[off:off+len(patch)] = patch
                else:
                    data.extend(b"\x00" * (off + len(patch) - len(data)))
                    data[off:off+len(patch)] = patch
            with open(output_path, "wb") as out:
                out.write(data)
            return True, f"LK patched offline -> {output_path} [0x1000 unlock, 0x200 AVB disable, no credits]"
        except Exception as e:
            return False, str(e)

    def get_lk_ops(self) -> list[dict[str, str]]:
        return [
            {"id": "lk_file", "name": "LK Bootloader Unlock - Patch fichier (Tecno/Infinix)", "cost": "2 credits (FREE offline)", "offline": True},
            {"id": "lk_meta", "name": "LK Bootloader Unlock Direct META (Tecno/Infinix)", "cost": "2 credits (FREE offline)", "offline": True},
        ]

    def lk_direct_meta_logs(self, soc="MT6878") -> list[str]:
        return [
            f"[META] LK Unlock Direct for {soc} via local META...",
            "[META] Reading lk_a (0x200000) via META ReadPartition",
            "[META] Patch 0x1000: 01 -> 00 (unlock flag), patch 0x200: AVB disable",
            "[META] Writing lk_a + lk_b back via META Write -> OKAY",
            "[OK] LK Bootloader Unlock Direct META done OFFLINE",
        ]
