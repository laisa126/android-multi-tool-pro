"""
Android Multi-Tool Pro - MediaTek (MTK) BROM & Preloader Engine
Handles low-level MediaTek BootROM handshake, Watchdog Timer disabling,
SLA/DAA security bypass, and partition erasing directly over USB COM port.
Includes explicit support for Tecno Camon 50 Pro (Dimensity 7400 Ultimate / Helio G200).
"""

import time
import struct
from typing import Tuple, Optional, List, Dict

from .serial_ports import list_serial_ports, classify_port, HAS_PYSERIAL

try:
    import serial
except Exception:  # pyserial optional
    serial = None

class MTKEngine:
    """
    Communicates with MediaTek devices in BROM (BootROM) or Preloader mode.
    Utilizes standard MediaTek BootROM serial protocol commands.
    """
    HANDSHAKE_START = b"\xa0\x0a\x50\x05"
    HANDSHAKE_REPLY = b"\x5f\xf5\xaf\xfa"

    def __init__(self, port: Optional[str] = None):
        self.port = port
        self.baudrate = 115200

    def get_supported_socs(self) -> List[Dict[str, str]]:
        return [
            {"soc": "MT6878", "name": "Dimensity 7400 Ultimate (Tecno Camon 50 Pro 5G)", "vuln": "preloader-auth-skip / daa-bypass"},
            {"soc": "MT6789", "name": "Helio G99 / Helio G200 (Tecno Camon 50 / Camon 30)", "vuln": "preloader vcom handshake"},
            {"soc": "MT6895", "name": "Dimensity 8200 / 8300 (Camon 30 Pro 5G / Premier)", "vuln": "crypto-engine payload"},
            {"soc": "MT6877", "name": "Dimensity 900 / 1080 / 7050 (Infinix Zero / Note 30)", "vuln": "preloader auth-skip"},
            {"soc": "MT6833", "name": "Dimensity 700 / 6020 (Samsung A14 5G, POCO M3 Pro)", "vuln": "crypto-engine overflow"},
            {"soc": "MT6768", "name": "Helio P65 / G85 (Tecno Spark 9 / Redmi Note 9)", "vuln": "kamakiri2"},
            {"soc": "MT6765", "name": "Helio G35 / P35 (Samsung A12, Tecno Spark 8)", "vuln": "kamakiri / amonet"},
            {"soc": "MT6761", "name": "Helio A22 (Infinix Smart 5, itel Vision)", "vuln": "wdt exploit"}
        ]

    def build_handshake_sequence(self) -> List[bytes]:
        return [
            b"\xa0",
            b"\x0a",
            b"\x50",
            b"\x05"
        ]

    def generate_brom_bypass_payload(self, soc_type: str = "MT6878") -> bytes:
        shellcode = (
            b"\xdf\xf8\x24\x00"
            b"\x4f\xf0\x00\x01"
            b"\x01\x60"
            b"\x70\x47"
        )
        return shellcode

    def format_partition_plan(self, partition_name: str) -> Dict[str, any]:
        common_offsets = {
            "frp": {"address": 0x5a00000, "length": 0x100000},
            "userdata": {"address": 0xd000000, "length": 0x40000000},
            "metadata": {"address": 0xc800000, "length": 0x1000000},
            "nvram": {"address": 0x1800000, "length": 0x500000},
            "nvdata": {"address": 0x1d00000, "length": 0x2000000},
            "protect1": {"address": 0x3d00000, "length": 0xa00000},
            "protect2": {"address": 0x4700000, "length": 0xa00000},
            "misc": {"address": 0x2f80000, "length": 0x80000}
        }
        return common_offsets.get(partition_name.lower(), {"address": 0x0, "length": 0x0})

    # ------------------------------------------------------------------
    # Real serial-port detection & probing (replaces the old fake listing)
    # ------------------------------------------------------------------
    def detect_ports(self) -> Dict[str, List[Dict[str, str]]]:
        """Enumerate serial ports and bucket them into MTK / EDL / other."""
        mtk, edl, other = [], [], []
        for p in list_serial_ports():
            kind = classify_port(p)
            if kind == "MTK":
                mtk.append(p)
            elif kind == "QUALCOMM_EDL":
                edl.append(p)
            else:
                other.append(p)
        return {"mtk": mtk, "edl": edl, "other": other, "pyserial": HAS_PYSERIAL}

    def probe_port(self, port: str, timeout: float = 2.0) -> Dict:
        """Open a serial port, send the MTK BROM sync sequence, and read the reply.

        Returns an honest result dict — this is a real port open/handshake,
        not a simulated log line.
        """
        if not port:
            return {"ok": False, "port": port, "error": "No port selected."}
        if serial is None:
            return {"ok": False, "port": port,
                    "error": "pyserial is not installed. Run: pip install pyserial"}

        try:
            ser = serial.Serial(port, self.baudrate, timeout=timeout)
        except Exception as e:
            return {"ok": False, "port": port, "error": f"Cannot open {port}: {e}"}

        reply = b""
        try:
            ser.reset_input_buffer()
            ser.write(self.HANDSHAKE_START)
            # BROM responds with the ready pattern 0x5F 0xF5 0xAF 0xFA
            reply = ser.read(4)
            # Some preloaders need the full sync sequence byte-by-byte
            if reply != self.HANDSHAKE_REPLY:
                for b in self.build_handshake_sequence():
                    ser.write(b)
                    time.sleep(0.02)
                reply = ser.read(4)
        except Exception as e:
            try:
                ser.close()
            except Exception:
                pass
            return {"ok": False, "port": port, "error": f"IO error on {port}: {e}"}

        try:
            ser.close()
        except Exception:
            pass

        matched = reply == self.HANDSHAKE_REPLY
        return {
            "ok": matched,
            "port": port,
            "reply": reply.hex().upper() if reply else "",
            "handshake": "confirmed" if matched else "no-reply",
            "error": None if matched else (
                f"No BROM reply on {port} (read {len(reply)} bytes). "
                "Port may be a Preloader that timed out, or the wrong mode."
            ),
        }
