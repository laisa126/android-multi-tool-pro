"""
Android Multi-Tool Pro - Qualcomm Snapdragon EDL (9008) Engine
Implements Qualcomm Sahara Protocol (Mode 0x01/0x02) and Firehose XML Command Protocol
used for emergency flashing and partition manipulation without bootloader unlocking.
"""

from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET

from .serial_ports import list_serial_ports, classify_port

class QualcommEDLEngine:
    """
    Qualcomm Snapdragon Emergency Download Protocol (HS-USB QDLoader 9008)
    1. Sahara Handshake: Loads programmer ELF file (prog_firehose_lite.elf)
    2. Firehose XML Channel: Exchanges XML commands for GPT reading, flashing, and wiping
    """
    SAHARA_HELLO_REQ = 0x01
    SAHARA_HELLO_RESP = 0x02
    SAHARA_READ_DATA = 0x03
    SAHARA_END_TRANSFER = 0x04
    SAHARA_DONE_REQ = 0x05
    SAHARA_DONE_RESP = 0x06
    SAHARA_RESET_REQ = 0x07

    def generate_firehose_configure_xml(self, max_payload_size: int = 1048576) -> str:
        """Initial XML handshake configuring storage type and buffer size."""
        root = ET.Element("data")
        ET.SubElement(root, "configure", {
            "MemoryName": "eMMC",
            "Verbose": "0",
            "AlwaysValidate": "0",
            "MaxPayloadSizeToTargetInBytes": str(max_payload_size)
        })
        return ET.tostring(root, encoding="utf-8").decode("utf-8")

    def generate_erase_partition_xml(self, partition_name: str, start_sector: int, num_sectors: int, sector_size: int = 512) -> str:
        """Generates Firehose XML instruction to erase a specific partition (e.g. FRP or userdata)."""
        root = ET.Element("data")
        ET.SubElement(root, "erase", {
            "start_sector": str(start_sector),
            "num_partition_sectors": str(num_sectors),
            "SECTOR_SIZE_IN_BYTES": str(sector_size),
            "label": partition_name
        })
        return ET.tostring(root, encoding="utf-8").decode("utf-8")

    def generate_reboot_xml(self, mode: str = "reset") -> str:
        """Sends clean power reboot command over Firehose."""
        root = ET.Element("data")
        ET.SubElement(root, "power", {"value": mode})
        return ET.tostring(root, encoding="utf-8").decode("utf-8")

    def get_supported_snapdragons(self) -> List[Dict[str, str]]:
        return [
            {"chip": "SDM660", "name": "Snapdragon 660", "loader": "prog_emmc_firehose_sdm660.mbn"},
            {"chip": "SM6125", "name": "Snapdragon 665", "loader": "prog_firehose_lite_sm6125.elf"},
            {"chip": "SM7150", "name": "Snapdragon 730G / 732G", "loader": "prog_firehose_ddr_sm7150.elf"},
            {"chip": "SM7225", "name": "Snapdragon 750G", "loader": "prog_firehose_ddr_sm7225.elf"},
            {"chip": "SM8250", "name": "Snapdragon 865", "loader": "prog_firehose_ufs_sm8250.elf"},
            {"chip": "SM8450", "name": "Snapdragon 8 Gen 1", "loader": "prog_firehose_ufs_sm8450.elf"}
        ]

    def detect_edl_ports(self) -> List[Dict[str, str]]:
        """Enumerate serial ports classified as Qualcomm HS-USB QDLoader (EDL)."""
        return [p for p in list_serial_ports() if classify_port(p) == "QUALCOMM_EDL"]
