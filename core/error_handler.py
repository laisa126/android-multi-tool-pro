"""
Android Multi-Tool Pro - Windows 11 Diagnostic & Error Handling Engine
Specialized resolution matrix for Windows 11 & Windows 11 Pro environments.
Handles Core Isolation (HVCI), Driver Signature Enforcement, USB 3.0 AMD dropouts,
and device connection errors across ADB, Fastboot, MTK, and Qualcomm.
"""


WINDOWS_11_ERROR_SOLUTIONS = {
    "DEVICE_UNAUTHORIZED": {
        "title": "Device Unauthorized (ADB)",
        "symptoms": ["adb devices shows 'xxxxxx unauthorized'", "RSA fingerprint dialog does not appear"],
        "cause": "The device's ADB security key does not match the PC's adbkey.pub, or the prompt was missed.",
        "win11_fix": (
            "1. On phone: Go to Developer Options -> Revoke USB debugging authorizations.\n"
            "2. Toggle USB Debugging OFF and then ON.\n"
            "3. On Windows 11 PC: Open CMD and run:\n"
            "   adb kill-server\n"
            "   del %USERPROFILE%\\.android\\adbkey*\n"
            "   adb start-server\n"
            "4. Re-plug the USB cable into a USB 2.0 port. Check phone display and tap 'Always allow from this computer'."
        )
    },
    "DEVICE_NOT_FOUND": {
        "title": "Waiting for Any Device / Device Not Detected",
        "symptoms": ["Tool says 'No device detected'", "Device Manager shows yellow exclamation mark under Other Devices"],
        "cause": "Windows 11 missing WinUSB/ADB driver or driver was blocked by Windows 11 Memory Integrity.",
        "win11_fix": (
            "1. Press Win + X and select 'Device Manager'.\n"
            "2. Look for 'Android' or 'Unknown Device' with a yellow warning triangle.\n"
            "3. Right-click -> Update driver -> 'Browse my computer for drivers' -> 'Let me pick from a list of available drivers'.\n"
            "4. Select 'Android Device' -> choose 'Android Composite ADB Interface'.\n"
            "5. If Windows 11 blocks it: use the app's 'Install Tools & Drivers' (auto-installs the drivers) or 'Force-Install VCOM (Test Mode)'."
        )
    },
    "TECNO_TRANSSION_NOT_DETECTED": {
        "title": "Tecno / Infinix / Transsion (Camon 50 Pro) Not Detected",
        "symptoms": [
            "Samsung / Xiaomi devices are detected fine, but Tecno Camon 50 Pro (CN5c) shows 'No device found'",
            "Phone is charging via USB but no 'Allow USB Debugging' popup appears on screen",
            "Windows Device Manager shows 'TECNO-CN5c' or 'Android' under Other Devices with a yellow exclamation mark (!)",
            "Device connects for 2 seconds and disconnects (MTK Preloader)"
        ],
        "cause": (
            "1. Phone is Locked: If screen is locked by PIN or Admin Plugin, Android cuts off USB data lines (Charge only).\n"
            "2. HiOS Default USB Mode: Transsion HiOS defaults to 'Charge only', powering off the ADB interface.\n"
            "3. Missing Transsion VID (0x2E04): Windows lacks the Transsion Holdings WinUSB driver mapping.\n"
            "4. Missing adb_usb.ini entry: ADB server does not probe Transsion VID 0x2E04 by default.\n"
            "5. AMD Ryzen / USB 3.0 Handshake Drop: Dimensity 7400 SoCs drop packets on blue USB 3.1/3.2 ports."
        ),
        "win11_fix": (
            "IF PHONE IS LOCKED (CANNOT ENABLE ADB):\n"
            "- Do not use ADB. Use MediaTek BROM mode instead!\n"
            "- Power off CN5c completely (hold Power + Vol Down 10s if screen is frozen).\n"
            "- Start the tool FIRST, then plug USB with NO buttons (Preloader mode) - the tool crashes it into BROM.\n"
            "- Do NOT hold Vol Up + Vol Down: that boots RECOVERY, not BROM.\n"
            "- Tool will detect MediaTek Preloader COM Port and format userdata/frp directly.\n\n"
            "IF PHONE CAN BE UNLOCKED (ADB MODE):\n"
            "- Swipe down notification shade -> tap 'Charging this device via USB' -> change to 'File Transfer (MTP)'.\n"
            "- Go to Settings -> Developer options -> tap 'Revoke USB debugging authorizations' -> toggle 'USB Debugging' OFF and ON.\n\n"
            "ON PC (TRANSSION DRIVER FIX):\n"
            "- Click 'Install Tools & Drivers' in the app (auto-adds 0x2e04, installs VCOM/ADB drivers, restarts ADB).\n"
            "- In Device Manager -> check 'TECNO-CN5c' -> update driver to 'Android Composite ADB Interface'."
        )
    },
    "FASTBOOT_AMD_USB3_BUG": {
        "title": "Fastboot Freeze / Command Hangs on Windows 11 (AMD Ryzen / USB 3.0)",
        "symptoms": ["Fastboot hangs on <waiting for any device>", "Flashing stops midway through large partition"],
        "cause": "Well-documented Windows 11 xHCI USB 3.1/3.2 bug on AMD AM4/AM5 chipsets communicating with Fastboot.",
        "win11_fix": (
            "1. Connect the phone to an older USB 2.0 port (black ports on motherboard I/O backplate, NOT blue/red ports).\n"
            "2. Alternatively, plug a cheap unpowered USB 2.0 hub between your PC and phone.\n"
            "3. In Windows 11 Device Manager -> Universal Serial Bus controllers -> USB Root Hub -> Properties -> "
            "Power Management -> Uncheck 'Allow the computer to turn off this device to save power'."
        )
    },
    "WIN11_CORE_ISOLATION_BLOCK": {
        "title": "MediaTek / Qualcomm Driver Blocked by Windows 11 Core Isolation (HVCI)",
        "symptoms": ["Windows 11 displays: 'A driver cannot load on this device (libusb0.sys / qcser.sys)'", "Error Code 39 in Device Manager"],
        "cause": "Windows 11 Memory Integrity / Hypervisor-Enforced Code Integrity (HVCI) blocks legacy unsigned GSM drivers.",
        "win11_fix": (
            "1. Click Start -> Search 'Core Isolation'.\n"
            "2. Temporarily toggle 'Memory Integrity' to OFF.\n"
            "3. Restart Windows 11.\n"
            "4. Click 'Install Tools & Drivers' in the app (auto-installs VCOM/ADB).\n"
            "5. After servicing is complete, you can toggle Memory Integrity back ON."
        )
    },
    "FASTBOOT_DYNAMIC_PARTITION_ERROR": {
        "title": "Fastboot Flashing Error: 'Partition not found' or 'No such partition'",
        "symptoms": ["fastboot flash system system.img fails on Android 10/11/12/13/14"],
        "cause": "Modern Android devices use dynamic 'super' partitions. System, vendor, and product partitions cannot be flashed in bootloader.",
        "win11_fix": (
            "1. Reboot device into Fastbootd mode:\n"
            "   adb reboot fastboot  (OR in fastboot: fastboot reboot fastboot)\n"
            "2. Screen should display: 'Fastbootd' on device display.\n"
            "3. Now flash the partition normally: fastboot flash system system.img."
        )
    },
    "MTK_HANDSHAKE_TIMEOUT": {
        "title": "MediaTek BROM Handshake Disconnecting Immediately",
        "symptoms": ["Phone connects as 'MediaTek USB Port' for 2 seconds and reboots", "COM port vanishes"],
        "cause": "Missing LibUSB-Win32 filter driver or Watchdog Timer reset triggered.",
        "win11_fix": (
            "1. Open Device Manager on Windows 11.\n"
            "2. Power the phone OFF, start the tool, then plug USB with NO buttons (Preloader).\n"
            "3. As soon as 'MediaTek USB Port' appears under Ports (COM & LPT), ensure driver says 'MediaTek Inc.'.\n"
            "4. Use a high-quality USB-C data cable (not a charge-only cable)."
        )
    }
}

class Windows11Diagnostics:
    @staticmethod
    def analyze_error(command_output: str, exit_code: int) -> dict[str, str] | None:
        """Scans terminal output for common Windows 11 technician errors and returns structured troubleshooting."""
        text = command_output.lower()

        if "unauthorized" in text:
            return WINDOWS_11_ERROR_SOLUTIONS["DEVICE_UNAUTHORIZED"]
        if "waiting for any device" in text or "device not found" in text or exit_code == -1:
            return WINDOWS_11_ERROR_SOLUTIONS["DEVICE_NOT_FOUND"]
        if "cannot load" in text or "unknown partition" in text:
            return WINDOWS_11_ERROR_SOLUTIONS["FASTBOOT_DYNAMIC_PARTITION_ERROR"]
        if "data transfer failed" in text or "protocol error" in text:
            return WINDOWS_11_ERROR_SOLUTIONS["FASTBOOT_AMD_USB3_BUG"]
        if "handshake timeout" in text or "port disconnected" in text:
            return WINDOWS_11_ERROR_SOLUTIONS["MTK_HANDSHAKE_TIMEOUT"]

        return None
