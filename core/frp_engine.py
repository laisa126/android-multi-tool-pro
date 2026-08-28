"""
Android Multi-Tool Pro - FRP & Screen Lock Bypass Engine
Provides technical methods for FRP (Factory Reset Protection) removal,
Setup Wizard bypass, and Screen Lock handling across ADB, Fastboot, and MTP.
"""

from typing import Tuple, List, Dict
import time

class FRPEngine:
    def __init__(self, adb_engine, fastboot_engine):
        self.adb = adb_engine
        self.fastboot = fastboot_engine

    def reset_frp_fastboot(self) -> List[Tuple[str, bool, str]]:
        """
        Attempts Universal Fastboot FRP partition erases across common vendor partitions:
        config, frp, persistent, devinfo.
        """
        partitions = ["config", "frp", "persistent", "devinfo"]
        results = []
        for part in partitions:
            success, msg = self.fastboot.erase_partition(part)
            results.append((part, success, msg))
        return results

    def bypass_frp_adb_setupwizard(self) -> Tuple[bool, List[str]]:
        """
        Bypasses Setup Wizard via ADB if USB Debugging is active (e.g. after Samsung *#0*# exploit).
        Sets user_setup_complete and device_provisioned flags, then disables Google Setup Wizard.
        """
        logs = []
        commands = [
            ("content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:s:1", "Set user_setup_complete = 1"),
            ("content insert --uri content://settings/global --bind name:s:device_provisioned --bind value:s:1", "Set device_provisioned = 1"),
            ("pm disable-user --user 0 com.google.android.setupwizard", "Disable Google Setup Wizard"),
            ("pm disable-user --user 0 com.sec.android.app.SecSetupWizard", "Disable Samsung Setup Wizard"),
            ("am start -c android.intent.category.HOME -a android.intent.action.MAIN", "Launch Home Screen")
        ]

        success_count = 0
        for cmd, desc in commands:
            code, out, err = self.adb.run_cmd(["shell"] + cmd.split())
            if code == 0:
                logs.append(f"[OK] {desc}")
                success_count += 1
            else:
                logs.append(f"[FAIL] {desc}: {err or out}")

        return (success_count > 0), logs

    def remove_screen_lock_rooted(self) -> Tuple[bool, List[str]]:
        """
        Removes gesture.key, password.key, and locksettings database.
        Requires root or TWRP recovery shell.
        """
        logs = []
        files_to_remove = [
            "/data/system/gesture.key",
            "/data/system/password.key",
            "/data/system/locksettings.db",
            "/data/system/locksettings.db-shm",
            "/data/system/locksettings.db-wal",
            "/data/system/gatekeeper.password.key",
            "/data/system/gatekeeper.pattern.key"
        ]

        cleared = 0
        for target in files_to_remove:
            code, out, err = self.adb.run_cmd(["shell", "rm", "-f", target])
            if code == 0:
                logs.append(f"[DELETED] {target}")
                cleared += 1
            else:
                logs.append(f"[FAILED] {target}: {err or out}")

        return (cleared > 0), logs

    def get_frp_methods_info(self) -> Dict[str, str]:
        return {
            "Samsung Test Mode (*#0*#)": (
                "1. Power on device to Welcome screen.\n"
                "2. Tap 'Emergency Call' and dial *#0*# (or *#9900# / *#0808#).\n"
                "3. When technician test menu appears, connect USB to PC.\n"
                "4. Tool sends modem AT command to trigger 'Allow USB Debugging' dialog on phone.\n"
                "5. Tap 'Always allow from this computer' on phone.\n"
                "6. Click 'Bypass FRP via ADB' to clear Google Account."
            ),
            "Fastboot Universal Wipe": (
                "1. Boot phone into Fastboot Mode (Hold Vol Down + Power).\n"
                "2. Connect to PC via original USB cable.\n"
                "3. Tool executes erasure on 'config', 'frp', and 'persistent' partitions.\n"
                "4. Works on Motorola, Lenovo, Xiaomi, OnePlus, Unisoc, and MTK Fastboot devices."
            ),
            "Xiaomi Mi Account / FRP (EDL / Fastboot)": (
                "1. Put Xiaomi device in Fastboot or EDL 9008 mode.\n"
                "2. In Fastboot: 'fastboot erase persist' removes corrupt or locked account locks.\n"
                "3. In EDL: Tool flashes clean persist.img to restore factory state."
            ),
            "MTP Browser Trigger": (
                "1. Device connected on Setup Wizard in normal MTP mode.\n"
                "2. Tool sends MTP Push notification launching YouTube or Chrome browser intent.\n"
                "3. From browser, technician navigates to FRP bypass settings page (e.g. vnrom.net/bypass)."
            )
        }
