"""
Android Multi-Tool Pro - Transsion / Tecno MDM & PayJoy Disabler Engine
Specifically targets persistent financing, Carlcare MDM, PalmPay,
Device Admin Security Plugins, and enterprise provisioning on
Tecno Camon 50 Pro (HiOS 14/15/16 / MT6878).
"""

import re
from typing import List, Tuple, Dict

class TranssionMDMEngine:
    def __init__(self, adb_engine):
        self.adb = adb_engine

    # Enterprise, financing, security plugins, and telemetry targets on Transsion HiOS
    TRANSSION_MDM_TARGETS = [
        ("com.transsion.palmpay", "PalmPay Microfinance Framework"),
        ("com.transsion.carlcare", "Carlcare Customer Service & Cloud Auth"),
        ("com.transsion.phonemaster", "PhoneMaster Enterprise Telemetry"),
        ("com.transsion.magicshow", "HiOS Remote Provisioning Agent"),
        ("com.transsion.aha", "AHA Application Store Push Daemon"),
        ("com.transsion.molink", "Transsion Cloud Sync Service"),
        ("com.payjoy.access", "PayJoy Device Lock Agent"),
        ("com.payjoy.status", "PayJoy Background Enforcer"),
        ("com.trustonic.telecoms.direct", "Trustonic Enterprise Cloud Lock"),
        ("com.trustonic.telecoms.direct.service", "Trustonic Knox Guard Service"),
        ("com.cloud.mplus", "M-KOPA M+ Financed Security Plugin"),
        ("com.dlight.atlas", "D.light Financed Device Controller"),
        ("com.watu.credit", "Watu Credit Financing Lock"),
        ("com.watu.android", "Watu Device Enforcer"),
        ("com.angaza.nexus", "Angaza Pay-as-you-go Enforcer"),
        ("com.mobile.security.plugin", "Generic OEM Security Plugin"),
        ("com.android.security.plugin", "HiOS Admin Security Plugin"),
        ("com.google.android.apps.work.clouddpc", "Google Enterprise Cloud DPC")
    ]

    # Known device admin receiver components
    KNOWN_ADMIN_COMPONENTS = [
        "com.transsion.carlcare/.receiver.DeviceAdminReceiver",
        "com.transsion.palmpay/.admin.DeviceAdminReceiver",
        "com.payjoy.access/.receiver.AdminReceiver",
        "com.payjoy.access/com.payjoy.access.receiver.AdminReceiver",
        "com.trustonic.telecoms.direct.service/.receiver.DeviceAdminReceiver",
        "com.cloud.mplus/.receiver.AdminReceiver",
        "com.transsion.magicshow/.AdminReceiver",
        "com.mobile.security.plugin/.receiver.AdminReceiver",
        "com.android.security.plugin/.AdminReceiver",
        "com.transsion.phonemaster/.admin.DeviceAdminReceiver"
    ]

    def list_active_device_admins(self) -> List[str]:
        """Queries the device policy manager for active admin receivers."""
        admins = []
        code, out, _ = self.adb.run_cmd(["shell", "dpm", "list-active-admins"])
        if code == 0 and out:
            for line in out.splitlines():
                line = line.strip()
                if "/" in line and not line.startswith("Active"):
                    admins.append(line)

        if not admins:
            # Fallback to dumpsys device_policy
            code, out, _ = self.adb.run_cmd(["shell", "dumpsys", "device_policy"])
            if code == 0 and out:
                matches = re.findall(r"Admin:?\s*ComponentInfo\{([^}]+)\}", out)
                for m in matches:
                    if m not in admins:
                        admins.append(m)
        return admins

    def remove_device_admin(self, component: str) -> Tuple[bool, str]:
        """Attempts to unregister an active device administrator."""
        code, out, err = self.adb.run_cmd(["shell", "dpm", "remove-active-admin", component])
        if code == 0:
            return True, f"Device admin component '{component}' successfully deactivated."
        return False, f"Failed to deactivate '{component}': {err or out}"

    def neutralize_admin_security_plugin(self, package: str) -> List[str]:
        """
        Strips permissions, overlay rights, background execution, and uninstalls/disables
        the admin app security plugin even when standard uninstall fails.
        """
        logs = []
        logs.append(f"Targeting Admin App Security Plugin: {package}")

        # 1. Strip AppOps permissions (prevents overlay lockscreens and background execution)
        appops_caps = [
            ("SYSTEM_ALERT_WINDOW", "Overlay display rights (screen lock banner)"),
            ("RUN_IN_BACKGROUND", "Background execution"),
            ("GET_USAGE_STATS", "Usage monitoring & app detection"),
            ("START_FOREGROUND", "Foreground service persistence"),
            ("BIND_ACCESSIBILITY_SERVICE", "Accessibility keylogging & UI hijacking"),
            ("WAKE_LOCK", "Power wake lock")
        ]
        for cap, desc in appops_caps:
            code, _, _ = self.adb.run_cmd(["shell", "cmd", "appops", "set", package, cap, "ignore"])
            if code == 0:
                logs.append(f"[OK] Revoked {cap} ({desc})")

        # 2. Revoke sensitive runtime permissions
        permissions = [
            "android.permission.RECEIVE_BOOT_COMPLETED",
            "android.permission.POST_NOTIFICATIONS",
            "android.permission.INTERNET",
            "android.permission.ACCESS_NETWORK_STATE",
            "android.permission.READ_PHONE_STATE"
        ]
        for perm in permissions:
            self.adb.run_cmd(["shell", "pm", "revoke", package, perm])

        # 3. Force stop process
        self.adb.run_cmd(["shell", "am", "force-stop", package])
        logs.append(f"[OK] Terminated running process for {package}")

        # 4. Attempt to remove active admin if known
        for comp in self.KNOWN_ADMIN_COMPONENTS:
            if comp.startswith(package + "/"):
                self.adb.run_cmd(["shell", "dpm", "remove-active-admin", comp])

        # 5. Clear application storage data & cache
        code, _, _ = self.adb.run_cmd(["shell", "pm", "clear", package])
        if code == 0:
            logs.append(f"[OK] Cleared package cache and local credentials database")

        # 6. Disable application for user 0
        code, _, err = self.adb.run_cmd(["shell", "pm", "disable-user", "--user", "0", package])
        if code == 0:
            logs.append(f"[OK] Disabled package for user 0: {package}")
        else:
            # 7. Try uninstall user 0
            u_code, _, u_err = self.adb.run_cmd(["shell", "pm", "uninstall", "-k", "--user", "0", package])
            if u_code == 0:
                logs.append(f"[OK] Uninstalled package for user 0: {package}")
            else:
                logs.append(f"[WARN] Cannot directly uninstall {package}: {u_err or err}. AppOps neutralized.")

        return logs

    def remove_device_owner_rooted(self) -> List[str]:
        """
        Removes device_owner_2.xml and device_policies.xml via root access.
        Completely strips all Device Owner & Admin restrictions permanently.
        """
        logs = []
        files = [
            "/data/system/device_owner_2.xml",
            "/data/system/device_policies.xml",
            "/data/system/users/0/device_policies.xml",
            "/data/system/device_owner.xml"
        ]
        for f in files:
            code, _, err = self.adb.run_cmd(["shell", "su", "-c", f"rm -f {f}"])
            if code == 0:
                logs.append(f"[OK] Deleted {f} (Admin privilege configuration purged)")
            else:
                logs.append(f"[FAIL] Could not delete {f}: {err} (Requires root access)")
        return logs

    def disable_mdm_services(self) -> List[Tuple[str, bool, str]]:
        results = []
        for pkg, desc in self.TRANSSION_MDM_TARGETS:
            code, out, err = self.adb.run_cmd(["shell", "pm", "disable-user", "--user", "0", pkg])
            if code == 0:
                results.append((pkg, True, f"Disabled ({desc})"))
            else:
                u_code, _, u_err = self.adb.run_cmd(["shell", "pm", "uninstall", "-k", "--user", "0", pkg])
                if u_code == 0:
                    results.append((pkg, True, f"Uninstalled for user 0 ({desc})"))
                else:
                    results.append((pkg, False, f"Not present or protected ({desc})"))
        return results

    def freeze_provisioning_intents(self) -> List[str]:
        logs = []
        commands = [
            ("settings put global device_provisioned 1", "Force global device_provisioned = 1"),
            ("settings put secure user_setup_complete 1", "Force user_setup_complete = 1"),
            ("pm disable-user --user 0 com.google.android.setupwizard", "Disable Google Setup Wizard"),
            ("pm disable-user --user 0 com.transsion.setupwizard", "Disable Tecno Setup Wizard")
        ]
        for cmd, desc in commands:
            code, out, err = self.adb.run_cmd(["shell"] + cmd.split())
            if code == 0:
                logs.append(f"[OK] {desc}")
            else:
                logs.append(f"[SKIP] {desc}: {err or out}")
        return logs
