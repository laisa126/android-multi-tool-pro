"""
Android Multi-Tool Pro - Connection Guide & Troubleshooting
-----------------------------------------------------------
Single source of truth for "how do I get the device to show up" across
every connection scenario (ADB, Fastboot, MTK BROM, Qualcomm EDL,
Samsung Download, Recovery/Sideload) plus per-state diagnostics that the
GUI and web suite render as an in-app tutorial.

Every dict here is plain data so both UIs can render it identically.
"""

from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# ADB / FASTBOOT DEVICE-STATE GUIDANCE
# ---------------------------------------------------------------------------
ADB_STATE_GUIDANCE: Dict[str, Dict] = {
    "device": {
        "title": "Connected & Authorized",
        "severity": "ok",
        "detail": "ADB handshake complete. Full shell access is available for this serial.",
        "fix": ["Device is ready — you can run any operation in the tool."],
    },
    "unauthorized": {
        "title": "USB Debugging Not Authorized",
        "severity": "warning",
        "detail": "The RSA key on this PC has not been approved by the phone, or the prompt was missed.",
        "fix": [
            "On the phone: tap 'Always allow from this computer' and then 'Allow'.",
            "No popup? Go to Developer Options -> 'Revoke USB debugging authorizations', then toggle USB Debugging OFF and ON.",
            "Re-plug the cable. If the prompt reappears, accept it.",
        ],
    },
    "offline": {
        "title": "Device Offline (ADB)",
        "severity": "warning",
        "detail": "The device is enumerated but the ADB daemon cannot talk to it (driver, cable, or USB mode).",
        "fix": [
            "Re-plug the cable into a USB 2.0 port (black port, not blue/red).",
            "On the phone, switch USB mode to 'File Transfer / MTP'.",
            "Run 'Kill / Restart ADB' in the tool, then scan again.",
        ],
    },
    "recovery": {
        "title": "Device Is In Recovery Mode",
        "severity": "info",
        "detail": "ADB sees the device in recovery. Only recovery commands / sideload apply.",
        "fix": ["Use the Reboot tab -> 'System' to return to Android, or use ADB Sideload."],
    },
    "sideload": {
        "title": "Device Is In Sideload Mode",
        "severity": "info",
        "detail": "The device is ready to receive an OTA via 'adb sideload'.",
        "fix": ["Load an OTA zip and use the Fastboot/Sideload operation in the tool."],
    },
    "bootloader": {
        "title": "Device Is In Bootloader (Fastboot)",
        "severity": "info",
        "detail": "ADB lists the device but it must be managed with Fastboot, not ADB shell.",
        "fix": ["Use the Fastboot Flasher tab or 'fastboot devices' operations."],
    },
    "no permissions": {
        "title": "ADB Permission Denied (Linux udev)",
        "severity": "error",
        "detail": "On Linux the current user lacks udev rules for the device's USB VID.",
        "fix": [
            "Add a udev rule: /etc/udev/rules.d/51-android.rules with your VID.",
            "Reload: sudo udevadm control --reload-rules && sudo udevadm trigger.",
            "Or run the tool with sudo if you trust the environment.",
        ],
    },
    "unknown": {
        "title": "ADB State Unknown",
        "severity": "warning",
        "detail": "The device reported an unrecognized state string.",
        "fix": ["Restart the ADB daemon and scan again.", "Check the cable and USB port."],
    },
    "not_detected": {
        "title": "No ADB Device Detected",
        "severity": "error",
        "detail": "adb devices returned no entries. See the scenario guide for the mode you need.",
        "fix": [
            "Confirm USB Debugging is ON (Developer Options).",
            "Confirm the phone is unlocked and USB mode is 'File Transfer'.",
            "Check Device Manager for a missing driver (yellow !).",
            "If the phone is locked, use MTK BROM / EDL instead of ADB.",
        ],
    },
}


def classify_adb_state(state: str) -> Optional[Dict]:
    """Map a raw adb state string to guidance, or None if no guidance."""
    if not state:
        return ADB_STATE_GUIDANCE["not_detected"]
    key = state.strip().lower()
    return ADB_STATE_GUIDANCE.get(key)


# ---------------------------------------------------------------------------
# DETECTION-LEVEL ISSUE FIXES
# ---------------------------------------------------------------------------
ISSUE_FIXES: Dict[str, Dict] = {
    "nothing_detected": {
        "key": "nothing_detected",
        "title": "Nothing detected on any bus",
        "cause": "No ADB device, no Fastboot device, no MTK/EDL serial port, and no USB device from a known vendor.",
        "fix": [
            "Use a data cable (not charge-only).",
            "Try a different USB port — prefer USB 2.0 (black).",
            "Enable USB Debugging / enter the correct mode on the phone (see guide).",
            "Run 'Kill / Restart ADB' and scan again.",
        ],
    },
    "device_on_bus_no_adb": {
        "key": "device_on_bus_no_adb",
        "title": "Device seen on USB bus but not in ADB",
        "cause": "The phone is physically connected (USB hardware bus) but ADB cannot enumerate it — almost always a driver, USB mode, or lock-screen issue.",
        "fix": [
            "On phone: unlock the screen and set USB mode to 'File Transfer (MTP)'.",
            "Windows: install the driver (install_drivers.bat) — check Device Manager for a yellow '!' device.",
            "Enable USB Debugging, then 'Revoke USB debugging authorizations'.",
            "If the phone is locked: use MTK BROM (hold Vol Up + Vol Down, plug USB) or EDL.",
        ],
    },
    "mtk_port_present": {
        "key": "mtk_port_present",
        "title": "MediaTek BROM/Preloader port found",
        "cause": "A MediaTek (VID 0E8D) serial port is present. The port usually stays alive only 1-2 seconds unless the watchdog is disabled.",
        "fix": [
            "Keep the button combo held (Vol Up + Vol Down) until the tool confirms the handshake.",
            "If the port vanishes, power the phone fully off and retry.",
            "Use a USB 2.0 port and a known-good data cable.",
        ],
    },
    "edl_port_present": {
        "key": "edl_port_present",
        "title": "Qualcomm EDL 9008 port found",
        "cause": "A Qualcomm HS-USB QDLoader 9008 port is present (VID 05C6).",
        "fix": [
            "Load a Firehose programmer for the exact chipset before flashing.",
            "Do not disconnect during a Sahara handshake.",
        ],
    },
    "adb_server_stale": {
        "key": "adb_server_stale",
        "title": "ADB server may be stale or conflicting",
        "cause": "The bundled adb could not enumerate devices, possibly because another adb server (Android Studio, another tool) is running under a different context.",
        "fix": [
            "Close Android Studio / other tools using adb.",
            "Run 'Kill / Restart ADB' in the tool.",
            "On Windows: Task Manager -> kill any stray adb.exe, then rescan.",
        ],
    },
    "usb3_amd": {
        "key": "usb3_amd",
        "title": "Possible USB 3.x handshake drop (AMD)",
        "cause": "Windows 11 xHCI USB 3.1/3.2 ports on AMD chipsets are known to drop Fastboot/MTK packets.",
        "fix": [
            "Use a black USB 2.0 port on the motherboard rear I/O.",
            "Or insert an unpowered USB 2.0 hub between PC and phone.",
        ],
    },
    "tecno_driver_missing": {
        "key": "tecno_driver_missing",
        "title": "Tecno / Transsion (Camon 50 Pro) on USB bus but NOT visible to ADB",
        "cause": "Windows sees the Tecno hardware (VID 0x2E04) but the interface is not bound to the WinUSB ADB driver — the Transsion driver INF is unsigned/missing, or the phone is in Charge-only / MTP mode.",
        "fix": [
            "On the phone: unlock the screen, pull down the USB notification, and switch to 'File Transfer (MTP)'.",
            "Enable Developer Options -> USB Debugging, then tap 'Always allow from this computer' when the prompt appears.",
            "Device Manager: find the Tecno/Android device -> Update driver -> Browse my computer -> Let me pick from a list -> Android Device -> 'Android Composite ADB Interface'.",
            "If it shows a yellow '!': run install_drivers.bat AS ADMIN; on Windows 11 also turn OFF Memory Integrity (Core Isolation) and reboot with driver signature enforcement disabled.",
            "Then click 'Kill / Restart ADB' in the tool and scan again.",
        ],
    },
    "tecno_driver_wrong_binding": {
        "key": "tecno_driver_wrong_binding",
        "title": "Tecno device is bound to the WRONG driver (not WinUSB)",
        "cause": "The Tecno interface is currently using another driver (e.g. MTP/wudfrd or usbccgp composite), which means it shows in Explorer but ADB can never enumerate it.",
        "fix": [
            "Device Manager -> right-click the Tecno interface -> Update driver -> Browse -> Let me pick -> Android Composite ADB Interface.",
            "Or install a device-specific WinUSB INF generated by the tool (see log).",
            "Re-plug the USB cable after the driver change, then scan again.",
        ],
    },
}

ALL_ISSUE_KEYS = list(ISSUE_FIXES.keys())


def generate_issues(result: Dict) -> List[Dict]:
    """Derive a list of issue dicts from a detection result (see core.detection)."""
    issues: List[Dict] = []
    adb = result.get("adb", []) or []
    fb = result.get("fastboot", []) or []
    mtk = result.get("mtk_ports", []) or []
    edl = result.get("edl_ports", []) or []
    hw = result.get("hardware", []) or []
    usb_driver = result.get("usb_driver", []) or []

    tecno_on_bus = any((h.get("vid") or "").upper() == "2E04" for h in hw)
    tecno_in_driver = any((d.get("vid") or "").upper() == "2E04" for d in usb_driver)

    if not adb and not fb and not mtk and not edl:
        if tecno_on_bus or tecno_in_driver:
            # Tecno is the special case: seen on the bus but not in ADB
            wrong_binding = any(
                (d.get("vid") or "").upper() == "2E04" and not d.get("adb_visible")
                for d in usb_driver
            )
            issues.append(ISSUE_FIXES["tecno_driver_wrong_binding"] if wrong_binding else ISSUE_FIXES["tecno_driver_missing"])
        elif hw:
            issues.append(ISSUE_FIXES["device_on_bus_no_adb"])
            issues.append(ISSUE_FIXES["adb_server_stale"])
        else:
            issues.append(ISSUE_FIXES["nothing_detected"])

    # per-device adb state guidance
    for d in adb:
        state = (d.get("state") or "").strip().lower()
        if state == "device":
            continue
        g = classify_adb_state(state)
        if g and g.get("severity") in ("warning", "error"):
            issues.append({
                "key": f"adb_{state}",
                "title": f"ADB device {d.get('serial', '?')} is '{state}' — {g['title']}",
                "cause": g["detail"],
                "fix": g["fix"],
            })

    if mtk:
        issues.append(ISSUE_FIXES["mtk_port_present"])
    if edl:
        issues.append(ISSUE_FIXES["edl_port_present"])

    # de-duplicate by key
    seen = set()
    out = []
    for iss in issues:
        k = iss.get("key", iss.get("title"))
        if k in seen:
            continue
        seen.add(k)
        out.append(iss)
    return out


# ---------------------------------------------------------------------------
# CONNECTION SCENARIOS (THE IN-APP TUTORIAL)
# ---------------------------------------------------------------------------
CONNECTION_SCENARIOS: List[Dict] = [
    {
        "key": "adb_usb",
        "title": "ADB over USB (normal Android OS)",
        "icon": "\U0001F50C",  # electric plug
        "mode": "ADB",
        "use_when": "The phone boots normally and you can unlock the screen.",
        "prerequisites": [
            "Developer Options enabled (Settings -> About Phone -> tap Build Number 7 times).",
            "USB Debugging turned ON.",
        ],
        "steps": [
            "Unlock the phone screen.",
            "Plug a data cable into a USB 2.0 (black) port on the PC.",
            "Swipe down the notification shade -> tap the USB notification -> select 'File Transfer (MTP)' (NOT charge only).",
            "A 'Allow USB debugging?' popup appears -> tick 'Always allow from this computer' -> tap Allow.",
            "In the tool: click 'Scan Devices' (or 'Kill / Restart ADB' first if nothing shows).",
        ],
        "verify": "adb devices must list the serial with state 'device' (green).",
        "failures": [
            {"symptom": "Nothing listed", "cause": "USB debugging off / charge-only mode / bad cable", "fix": "Enable debugging, set MTP, try another cable/port."},
            {"symptom": "'unauthorized'", "cause": "RSA prompt missed or not accepted", "fix": "Revoke USB debugging authorizations and re-accept."},
            {"symptom": "'offline'", "cause": "Driver or USB 3.x port issue", "fix": "Use USB 2.0 port; reinstall driver; restart ADB."},
        ],
    },
    {
        "key": "adb_wifi",
        "title": "ADB over Wi-Fi (wireless debugging)",
        "icon": "\U0001F4F6",  # antenna bars
        "mode": "ADB",
        "use_when": "No cable available, or the USB port is damaged.",
        "prerequisites": [
            "Android 11+ with Wireless Debugging (or classic 'adb tcpip' on rooted/older devices).",
            "Phone and PC on the same network.",
        ],
        "steps": [
            "Enable Developer Options -> Wireless Debugging -> ON.",
            "Tap 'Pair device with pairing code' and note the IP:PORT + 6-digit code.",
            "On PC run: adb pair IP:PORT then enter the code.",
            "Then run: adb connect IP:PORT (from the Wireless Debugging main screen).",
            "Scan in the tool — the device appears like a USB device.",
        ],
        "verify": "adb devices lists the IP:PORT with state 'device'.",
        "failures": [
            {"symptom": "Connection refused", "cause": "Wrong port / not on same network", "fix": "Use the exact IP:PORT shown; disable AP isolation on the router."},
        ],
    },
    {
        "key": "fastboot",
        "title": "Fastboot / Fastbootd (bootloader)",
        "icon": "\U0001F4A0",  # zap
        "mode": "FASTBOOT",
        "use_when": "Flashing partitions, unlocking the bootloader, or the phone only boots to bootloader.",
        "prerequisites": [
            "Phone in bootloader (power off -> hold Power + Vol Down), or 'adb reboot bootloader'.",
            "Fastboot driver installed (Android Bootloader Interface).",
        ],
        "steps": [
            "Put the phone in Fastboot (or Fastbootd: 'adb reboot fastboot').",
            "Plug into a USB 2.0 port.",
            "Windows: confirm Device Manager shows 'Android Bootloader Interface' (no yellow !).",
            "In the tool: click 'Scan Devices' — it appears with a FASTBOOT tag.",
            "Run fastboot operations (flash, unlock, getvar).",
        ],
        "verify": "fastboot devices lists the serial in 'fastboot' or 'fastbootd' mode.",
        "failures": [
            {"symptom": "Hangs on '< waiting for any device >'", "cause": "AMD USB 3.x bug or missing driver", "fix": "Use USB 2.0 port; reinstall bootloader driver."},
            {"symptom": "Partition not found", "cause": "Dynamic super partition", "fix": "Boot into Fastbootd for system/vendor/product."},
        ],
    },
    {
        "key": "recovery_sideload",
        "title": "Recovery / ADB Sideload",
        "icon": "\U0001F504",  # arrows ccw
        "mode": "RECOVERY",
        "use_when": "Installing an OTA/zip on a non-booting or locked device that still has recovery.",
        "prerequisites": ["Phone in stock recovery with 'Apply update from ADB' selected."],
        "steps": [
            "Boot to recovery (power off -> hold Power + Vol Up).",
            "Choose 'Apply update from ADB' (sideload).",
            "Connect USB; the device appears with state 'sideload'.",
            "Load the OTA zip in the tool and start sideload.",
        ],
        "verify": "adb devices shows the serial with state 'sideload'.",
        "failures": [
            {"symptom": "Device listed as 'recovery' only", "cause": "Sideload not selected", "fix": "Select 'Apply update from ADB' in recovery first."},
        ],
    },
    {
        "key": "mtk_brom",
        "title": "MediaTek BROM / Preloader (locked / bricked)",
        "icon": "\U000026A1",  # high voltage
        "mode": "MTK BROM",
        "use_when": "Screen is locked by PIN/admin plugin, or the phone is bricked and won't boot.",
        "prerequisites": [
            "Phone fully powered OFF.",
            "MediaTek Preloader USB VCOM driver installed (VID 0E8D).",
        ],
        "steps": [
            "Power off completely (hold Power + Vol Down 10s if frozen).",
            "Hold Volume Up + Volume Down together.",
            "While holding, plug the USB cable into a USB 2.0 port.",
            "Watch the tool: the MTK Preloader port appears under the MTK BROM tab.",
            "Keep holding until the tool reports the handshake (the port closes in 1-2s otherwise).",
        ],
        "verify": "A COM/tty port with VID 0E8D appears and the handshake returns 0x5F 0xF5 0xAF 0xFA.",
        "failures": [
            {"symptom": "Port appears for 2s then vanishes", "cause": "Watchdog reset (normal)", "fix": "Hold the button combo until the tool catches it."},
            {"symptom": "No port at all", "cause": "Missing VCOM driver / charge-only cable", "fix": "Install driver (install_drivers.bat); use a data cable."},
        ],
    },
    {
        "key": "locked_brom",
        "title": "Phone LOCKED — FRP / screen-lock removal (NO USB debugging)",
        "icon": "\U0001F512",  # lock
        "mode": "MTK BROM",
        "use_when": "The Tecno Camon 50 Pro (or any MTK phone) is PIN/pattern/FRP locked and you CANNOT enable USB debugging because the screen is locked.",
        "prerequisites": [
            "Understand: ADB is IMPOSSIBLE on a locked phone — USB debugging can only be turned on from inside Android. Use the hardware BROM channel instead.",
            "MediaTek Preloader USB VCOM driver installed (VID 0E8D) — Connection Guide -> Install Tools & Drivers.",
        ],
        "steps": [
            "Power the phone OFF completely (hold Power + Vol Down ~10s if the screen is frozen).",
            "Hold Volume Up + Volume Down TOGETHER.",
            "While holding, plug the USB cable into a USB 2.0 (black) port on the PC.",
            "In the tool: open the ⚡ MTK BROM tab -> click 'Detect BROM Port & Handshake'.",
            "When the handshake confirms, run 'Wipe FRP' or 'Factory Reset (Userdata)' from the BROM tab — this clears the lock without any USB debugging.",
        ],
        "verify": "A COM/tty port with VID 0E8D appears and the handshake returns 0x5F 0xF5 0xAF 0xFA.",
        "failures": [
            {"symptom": "No MTK port appears", "cause": "Missing VCOM driver / charge-only cable / wrong button combo", "fix": "Install the MTK VCOM driver, use a data cable, and hold the buttons before plugging in."},
            {"symptom": "Port appears for 2s then vanishes", "cause": "Watchdog reset (normal)", "fix": "Keep holding the button combo until the tool reports the handshake."},
            {"symptom": "ADB 'not found'", "cause": "Locked phone has no USB debugging", "fix": "That's expected — use BROM, not ADB."},
        ],
    },
    {
        "key": "qcom_edl",
        "title": "Qualcomm EDL 9008 (Snapdragon)",
        "icon": "\U0001F3AF",  # dart
        "mode": "EDL",
        "use_when": "Qualcomm device is bricked or needs FRP/partition erase without bootloader unlock.",
        "prerequisites": ["Qualcomm HS-USB QDLoader 9008 driver (VID 05C6).", "Firehose programmer for the exact chipset."],
        "steps": [
            "Enter EDL (test points, or 'adb reboot edl', or hold keys per model).",
            "Confirm Device Manager shows 'Qualcomm HS-USB QDLoader 9008'.",
            "Load the correct Firehose programmer in the tool.",
            "Run the desired partition/FRP operation.",
        ],
        "verify": "A COM port with VID 05C6 (QDLoader 9008) is listed under EDL ports.",
        "failures": [
            {"symptom": "Port shows 900E instead of 9008", "cause": "Device in wrong EDL state", "fix": "Re-enter EDL via test points."},
        ],
    },
    {
        "key": "samsung_download",
        "title": "Samsung Download (Odin) Mode",
        "icon": "\U0001F50B",  # battery
        "mode": "DOWNLOAD",
        "use_when": "Flashing Samsung firmware with Odin-style tools.",
        "prerequisites": ["Samsung USB driver installed."],
        "steps": [
            "Power off the phone.",
            "Hold Volume Down + Volume Up (or Vol Down + Home on older models) and plug USB.",
            "Press Volume Up when the warning screen appears.",
            "The device is now in Download mode for firmware flashing.",
        ],
        "verify": "Odin/tool shows 'Added!!' and a COM port is assigned.",
        "failures": [
            {"symptom": "Not recognized", "cause": "Missing Samsung driver / USB 3.x port", "fix": "Install Samsung driver; use USB 2.0 port."},
        ],
    },
]


def all_scenarios() -> List[Dict]:
    return CONNECTION_SCENARIOS


def scenario_by_key(key: str) -> Optional[Dict]:
    for s in CONNECTION_SCENARIOS:
        if s["key"] == key:
            return s
    return None


def all_guidance() -> Dict[str, Dict]:
    return ADB_STATE_GUIDANCE
