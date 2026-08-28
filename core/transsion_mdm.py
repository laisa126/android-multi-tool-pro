"""
Android Multi-Tool Pro - Transsion / Tecno MDM & PayJoy Disabler Engine
Specifically targets persistent financing, Carlcare MDM, and PalmPay
enterprise provisioning packages on Tecno Camon 50 Pro (HiOS 14/15/16).
"""

from typing import List, Tuple, Dict

class TranssionMDMEngine:
    def __init__(self, adb_engine):
        self.adb = adb_engine

    # Enterprise, financing, and telemetry targets on Transsion HiOS
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
        ("com.google.android.apps.work.clouddpc", "Google Enterprise Cloud DPC")
    ]

    def disable_mdm_services(self) -> List[Tuple[str, bool, str]]:
        results = []
        for pkg, desc in self.TRANSSION_MDM_TARGETS:
            code, out, err = self.adb.run_cmd(["shell", "pm", "disable-user", "--user", "0", pkg])
            if code == 0:
                results.append((pkg, True, f"Disabled ({desc})"))
            else:
                # Try uninstall user 0
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
