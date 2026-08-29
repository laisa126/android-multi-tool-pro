"""
Android Multi-Tool Pro - Unified Device Detection Orchestrator
-------------------------------------------------------------
Combines ADB, Fastboot, serial-port (MTK/EDL) and physical USB-bus
enumeration into one categorized result used by both the desktop GUI
and the web suite. No fake serials: hardware-bus entries are tagged as
diagnostic-only and are never passed to adb/fastboot.
"""

import platform
from typing import Dict, List

from .serial_ports import list_serial_ports, classify_port, HAS_PYSERIAL
from .connection_guide import generate_issues


def run_full_detection(adb_engine, fastboot_engine, mtk_engine=None, qcom_engine=None) -> Dict:
    """Return a categorized snapshot of everything visible on USB/serial."""
    adb_devices: List[Dict] = adb_engine.get_devices() if adb_engine else []
    fb_devices: List[Dict] = fastboot_engine.get_devices() if fastboot_engine else []
    hardware: List[Dict] = adb_engine.get_hardware_usb_devices() if adb_engine else []

    ports = list_serial_ports()
    mtk_ports: List[Dict] = []
    edl_ports: List[Dict] = []
    other_ports: List[Dict] = []
    for p in ports:
        kind = classify_port(p)
        if kind == "MTK":
            mtk_ports.append(p)
        elif kind == "QUALCOMM_EDL":
            edl_ports.append(p)
        else:
            other_ports.append(p)

    result: Dict = {
        "os": platform.system(),
        "adb": adb_devices,
        "fastboot": fb_devices,
        "mtk_ports": mtk_ports,
        "edl_ports": edl_ports,
        "other_ports": other_ports,
        "hardware": hardware,
        "pyserial": HAS_PYSERIAL,
        "issues": [],
    }
    result["issues"] = generate_issues(result)
    return result


def selectable_devices(result: Dict) -> List[Dict]:
    """Return ONLY devices that can be passed to adb/fastboot (real serials)."""
    out: List[Dict] = []
    for d in result.get("adb", []) or []:
        out.append({
            "kind": "adb",
            "serial": d.get("serial", ""),
            "state": d.get("state", "unknown"),
            "label": f"{d.get('serial','')} (ADB: {d.get('state','unknown')})",
        })
    for d in result.get("fastboot", []) or []:
        out.append({
            "kind": "fastboot",
            "serial": d.get("serial", ""),
            "state": d.get("mode", "fastboot"),
            "label": f"{d.get('serial','')} (FASTBOOT: {d.get('mode','fastboot')})",
        })
    return out
