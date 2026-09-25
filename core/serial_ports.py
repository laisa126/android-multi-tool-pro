"""
Android Multi-Tool Pro - Serial Port Enumeration & Classification
-----------------------------------------------------------------
Cross-platform discovery of serial (COM / tty) ports used by
MediaTek BROM/Preloader, Qualcomm EDL 9008 and Samsung download modes.

Uses pyserial when available and falls back to native Windows registry
or Linux sysfs enumeration so detection still works without pyserial.
"""

import os
import re
import platform
from typing import Dict, List, Optional

try:  # pyserial is an optional dependency (see requirements.txt)
    import serial.tools.list_ports as _list_ports
    HAS_PYSERIAL = True
except Exception:  # pragma: no cover
    _list_ports = None
    HAS_PYSERIAL = False


def _norm_vid_pid(value: str) -> str:
    value = (value or "").strip().upper().replace("0X", "")
    return value.zfill(4) if value else ""


def _extract_vid_pid(hwid: str):
    vid = pid = ""
    m = re.search(r"VID[_:]?\s*([0-9A-Fa-f]{4})", hwid or "")
    if m:
        vid = _norm_vid_pid(m.group(1))
    m = re.search(r"PID[_:]?\s*([0-9A-Fa-f]{4})", hwid or "")
    if m:
        pid = _norm_vid_pid(m.group(1))
    return vid, pid


def _enum_windows() -> List[Dict[str, str]]:
    """Native Windows enumeration without pyserial (registry only)."""
    ports: List[Dict[str, str]] = []
    try:
        import winreg
    except Exception:
        return ports

    # 1. COM port name -> registry value name map
    com_map: Dict[str, str] = {}
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
        i = 0
        while True:
            try:
                name, val, _ = winreg.EnumValue(key, i)
                i += 1
                com_map[str(val)] = name
            except OSError:
                break
    except Exception:
        pass

    # 2. USB enum for VID/PID + friendly name + which COM port each device owns
    try:
        usb_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\USB")
        idx = 0
        while True:
            try:
                key_name = winreg.EnumKey(usb_key, idx)
                idx += 1
            except OSError:
                break
            m = re.search(r"VID_([0-9A-Fa-f]{4})&PID_([0-9A-Fa-f]{4})", key_name)
            vid = _norm_vid_pid(m.group(1)) if m else ""
            pid = _norm_vid_pid(m.group(2)) if m else ""
            try:
                dev_key = winreg.OpenKey(usb_key, key_name)
            except OSError:
                continue
            s_idx = 0
            while True:
                try:
                    inst = winreg.EnumKey(dev_key, s_idx)
                    s_idx += 1
                except OSError:
                    break
                if inst.startswith("&"):
                    continue
                try:
                    inst_key = winreg.OpenKey(dev_key, inst)
                except OSError:
                    continue
                desc = ""
                try:
                    d, _ = winreg.QueryValueEx(inst_key, "DeviceDesc")
                    desc = d.split(";")[-1] if ";" in d else d
                except Exception:
                    pass
                port = ""
                try:
                    dp = winreg.OpenKey(inst_key, "Device Parameters")
                    pv, _ = winreg.QueryValueEx(dp, "PortName")
                    port = str(pv)
                except Exception:
                    pass
                if port and port in com_map:
                    ports.append({
                        "port": port,
                        "description": desc or com_map.get(port, ""),
                        "hwid": key_name,
                        "vid": vid,
                        "pid": pid,
                        "manufacturer": "",
                    })
    except Exception:
        pass

    # 3. Any COM ports we could not map to a USB device (still list them)
    seen = {p["port"] for p in ports}
    for port, name in com_map.items():
        if port not in seen:
            ports.append({"port": port, "description": name, "hwid": "", "vid": "", "pid": "", "manufacturer": ""})
    return ports


def _enum_linux() -> List[Dict[str, str]]:
    """Native Linux enumeration without pyserial (sysfs only)."""
    ports: List[Dict[str, str]] = []
    base = "/sys/class/tty"
    if not os.path.isdir(base):
        return ports
    for dev in sorted(os.listdir(base)):
        if not (dev.startswith("ttyACM") or dev.startswith("ttyUSB")):
            continue
        vid = pid = prod = manu = ""
        node = os.path.realpath(os.path.join(base, dev))
        for _ in range(6):
            node = os.path.dirname(node)
            if os.path.isfile(os.path.join(node, "idVendor")):
                try:
                    with open(os.path.join(node, "idVendor")) as f:
                        vid = _norm_vid_pid(f.read())
                    with open(os.path.join(node, "idProduct")) as f:
                        pid = _norm_vid_pid(f.read())
                    with open(os.path.join(node, "product"), encoding="utf-8", errors="ignore") as f:
                        prod = f.read().strip()
                    with open(os.path.join(node, "manufacturer"), encoding="utf-8", errors="ignore") as f:
                        manu = f.read().strip()
                except Exception:
                    pass
                break
        ports.append({
            "port": f"/dev/{dev}",
            "description": prod or dev,
            "hwid": f"VID_{vid}&PID_{pid}" if vid else "",
            "vid": vid,
            "pid": pid,
            "manufacturer": manu,
        })
    return ports


def list_serial_ports() -> List[Dict[str, str]]:
    """Return a de-duplicated list of serial ports with VID/PID metadata."""
    ports: List[Dict[str, str]] = []
    if HAS_PYSERIAL and _list_ports is not None:
        try:
            for p in _list_ports.comports():
                vid, pid = _extract_vid_pid(p.hwid or "")
                ports.append({
                    "port": p.device or "",
                    "description": (p.description or "").strip(),
                    "hwid": (p.hwid or "").strip(),
                    "vid": vid,
                    "pid": pid,
                    "manufacturer": (getattr(p, "manufacturer", "") or "").strip(),
                })
        except Exception:
            ports = []
    if not ports:
        system = platform.system()
        if system == "Windows":
            ports = _enum_windows()
        elif system == "Linux":
            ports = _enum_linux()

    seen = set()
    out = []
    for p in ports:
        if not p.get("port") or p["port"] in seen:
            continue
        seen.add(p["port"])
        out.append(p)
    return out


MEDIATEK_VIDS = {"0E8D"}
QUALCOMM_VIDS = {"05C6", "1E0E"}
SAMSUNG_VIDS = {"04E8", "04E9"}


def classify_port(port: Dict[str, str]) -> str:
    """Classify a serial port as MTK / QUALCOMM_EDL / SAMSUNG / UNKNOWN."""
    text = " ".join([
        port.get("description", ""),
        port.get("hwid", ""),
        port.get("manufacturer", ""),
    ]).lower()
    vid = (port.get("vid") or "").upper()

    if vid in MEDIATEK_VIDS or any(k in text for k in ("mediatek", "mtk", "preloader", "vcom", "da usb")):
        return "MTK"
    if vid in QUALCOMM_VIDS or any(k in text for k in ("qdloader", "9008", "900e", "sahara", "qualcomm hs-usb")):
        return "QUALCOMM_EDL"
    if vid in SAMSUNG_VIDS or "samsung" in text:
        return "SAMSUNG"
    return "UNKNOWN"


def is_mtk_port(port: Dict[str, str]) -> bool:
    return classify_port(port) == "MTK"


def is_edl_port(port: Dict[str, str]) -> bool:
    return classify_port(port) == "QUALCOMM_EDL"


# ---------------------------------------------------------------------------
# Windows USB driver binding diagnostics (why ADB can't see a device)
# ---------------------------------------------------------------------------
TRANSSION_VID = "2E04"

def get_windows_usb_driver_status(vids: Optional[object] = None) -> List[Dict[str, str]]:
    """Windows-only: report the current driver binding for USB devices of interest.

    Returns a list of dicts with keys: vid, pid, hardware_id, description,
    service, adb_visible. ``adb_visible`` is True only when the interface is
    bound to WinUSB — the driver ADB actually talks to. MTP-only interfaces
    bind to wudfrd (adb_visible=False), which is the #1 reason a phone charges
    and shows in Explorer but is invisible to `adb devices`.
    """
    if platform.system() != "Windows":
        return []
    target = {v.upper() for v in (vids or [TRANSSION_VID, "0E8D", "18D1", "2717", "04E8", "22D9", "2A70"])}
    results: List[Dict[str, str]] = []
    try:
        import winreg
    except Exception:
        return results
    try:
        usb_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\USB")
    except OSError:
        return results

    idx = 0
    while True:
        try:
            key_name = winreg.EnumKey(usb_key, idx)
            idx += 1
        except OSError:
            break
        m = re.search(r"VID_([0-9A-Fa-f]{4})&PID_([0-9A-Fa-f]{4})(.*)$", key_name)
        if not m:
            continue
        vid, pid = m.group(1).upper(), m.group(2).upper()
        if vid not in target:
            continue
        try:
            dev_key = winreg.OpenKey(usb_key, key_name)
        except OSError:
            continue
        i = 0
        while True:
            try:
                inst = winreg.EnumKey(dev_key, i)
                i += 1
            except OSError:
                break
            if inst.startswith("&"):
                continue
            try:
                ik = winreg.OpenKey(dev_key, inst)
            except OSError:
                continue
            service, desc, hwids = "", "", []
            try:
                service, _ = winreg.QueryValueEx(ik, "Service")
            except Exception:
                pass
            try:
                d, _ = winreg.QueryValueEx(ik, "DeviceDesc")
                desc = d.split(";")[-1] if ";" in d else d
            except Exception:
                pass
            try:
                hwids, _ = winreg.QueryValueEx(ik, "HardwareID")
                if isinstance(hwids, str):
                    hwids = [hwids]
            except Exception:
                pass
            results.append({
                "vid": vid,
                "pid": pid,
                "hardware_id": hwids[0] if hwids else f"USB\\VID_{vid}&PID_{pid}",
                "description": desc,
                "service": str(service),
                "adb_visible": str(service).strip().lower() == "winusb",
            })
    return results


def build_custom_adb_inf(hardware_ids: List[str], output_path: Optional[str] = None,
                         provider: str = "Android Multi-Tool Pro") -> str:
    """Generate a device-specific WinUSB (ADB) driver INF for the exact hardware IDs.

    Returns the written path. The generated INF is unsigned — install it with
    driver signature enforcement temporarily disabled (see install notes).
    """
    ids = sorted({h.strip() for h in hardware_ids if h and h.strip()})
    if not ids:
        raise ValueError("No hardware IDs supplied")

    lines = [
        "; Device-specific WinUSB (ADB) driver for:",
    ]
    for h in ids:
        lines.append(f";   {h}")
    lines += [
        "; Generated by Android Multi-Tool Pro — install with driver signature",
        "; enforcement disabled:",
        ";   pnputil /add-driver <this file> /install",
        "",
        "[Version]",
        'Signature   = "$Windows NT$"',
        "Class       = AndroidUsbDeviceClass",
        "ClassGuid   = {3F966BD9-FA04-4ec5-991C-D326973B5128}",
        f"Provider    = %ProviderName%",
        "DriverVer   = 08/28/2026,14.0.0.0",
        "",
        "[Manufacturer]",
        "%ProviderName% = DeviceList, NTx86, NTamd64",
        "",
        "[DeviceList.NTx86]",
    ]
    for h in ids:
        lines.append(f"%CompositeAdbInterface% = USB_Install, {h}")
    lines += ["", "[DeviceList.NTamd64]"]
    for h in ids:
        lines.append(f"%CompositeAdbInterface% = USB_Install, {h}")
    lines += [
        "",
        "[USB_Install]",
        "Include = winusb.inf",
        "Needs   = WINUSB.NT",
        "",
        "[USB_Install.Services]",
        "Include    = winusb.inf",
        "AddService = WinUSB,0x00000002,WinUSB_ServiceInstall",
        "",
        "[WinUSB_ServiceInstall]",
        "DisplayName     = %WinUSB_SvcDesc%",
        "ServiceType     = 1",
        "StartType       = 3",
        "ErrorControl    = 1",
        "ServiceBinary   = %12%\\WinUSB.sys",
        "",
        "[USB_Install.Wdf]",
        "KmdfService = WINUSB, WinUSB_Install",
        "",
        "[WinUSB_Install]",
        "KmdfLibraryVersion = 1.9",
        "",
        "[USB_Install.HW]",
        "AddReg = Dev_AddReg",
        "",
        "[Dev_AddReg]",
        'HKR,,DeviceInterfaceGUIDs,0x00010000,"{F72FE0D4-CBCB-407d-8814-9ED673D0DD6B}"',
        "",
        "[Strings]",
        f'ProviderName           = "{provider}"',
        'ClassName              = "Android Device"',
        'WinUSB_SvcDesc         = "Android ADB WinUSB Driver"',
        'CompositeAdbInterface  = "Android Composite ADB Interface"',
    ]

    path = output_path or os.path.join(os.getcwd(), "tecno_adb_driver_custom.inf")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path
