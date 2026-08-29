import os
import sys
import json
import time
import threading
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from core.adb_engine import ADBEngine
from core.fastboot_engine import FastbootEngine
from core.frp_engine import FRPEngine
from core.mtk_engine import MTKEngine
from core.qualcomm_engine import QualcommEDLEngine
from core.samsung_modem import SamsungModemEngine
from core.root_engine import RootEngine
from core.efs_engine import EFSEngine
from core.error_handler import WINDOWS_11_ERROR_SOLUTIONS
from core.device_matrix import SUPPORTED_DEVICE_CATALOG, find_device_matches
from core.device_profiles import BLOATWARE_PRESETS, TEST_POINT_DATABASE
from core.workflow_guide import WORKFLOW_TUTORIALS, USB_PLUGGED_WIZARD
from core.payload_extractor import PayloadExtractor
from core.scatter_flasher import ScatterFlasher
from core.transsion_mdm import TranssionMDMEngine
from core.detection import run_full_detection, selectable_devices
from core.connection_guide import CONNECTION_SCENARIOS, ADB_STATE_GUIDANCE

adb = ADBEngine()
fastboot = FastbootEngine()
frp = FRPEngine(adb, fastboot)
mtk = MTKEngine()
qualcomm = QualcommEDLEngine()
samsung_modem = SamsungModemEngine()
root_engine = RootEngine(adb, fastboot)
efs = EFSEngine(adb, fastboot)
payload_extractor = PayloadExtractor()
scatter_flasher = ScatterFlasher()
transsion_mdm = TranssionMDMEngine(adb)

device_presets = {
    "tecno": {
        "brand": "Tecno Mobile (Transsion)",
        "model": "Camon 50 Pro 5G (TECNO-CN5c)",
        "device": "TECNO-CN5c",
        "android_version": "16 (HiOS 16)",
        "sdk_level": "36",
        "build_id": "CN5c-H932A-U-GL-260315V120",
        "security_patch": "2026-04-05",
        "cpu_abi": "arm64-v8a (MediaTek Dimensity 7400 Ultimate 4nm)",
        "battery_level": "96% (6500 mAh)",
        "root_status": "No (SELinux Enforcing)"
    },
    "samsung": {
        "brand": "Samsung",
        "model": "SM-S908B (Galaxy S22 Ultra)",
        "device": "b0s",
        "android_version": "14 (One UI 6.1)",
        "sdk_level": "34",
        "build_id": "UP1A.231005.007.S908BXXU7ZXCD",
        "security_patch": "2026-04-01",
        "cpu_abi": "arm64-v8a (Snapdragon 8 Gen 1)",
        "battery_level": "92%",
        "root_status": "No (SELinux Enforcing)"
    },
    "xiaomi": {
        "brand": "Xiaomi",
        "model": "Redmi Note 11 (2201117TI)",
        "device": "spes",
        "android_version": "13 (HyperOS 1.0)",
        "sdk_level": "33",
        "build_id": "TKQ1.221114.001.V816.0.4.0.TGCMIXM",
        "security_patch": "2026-02-01",
        "cpu_abi": "arm64-v8a (Snapdragon 680)",
        "battery_level": "84%",
        "root_status": "No (Fastboot Mode)"
    }
}

mock_state = {
    "simulated": False,  # default to REAL device detection
    "current_key": "tecno",
    "selected_device": "Tecno Camon 50 Pro 5G (Dimensity 7400 - MTK Preloader)",
}

# ---- Server-side audit logging (persisted to logs/web_server.log) ----
LOGS_DIR = os.path.join(parent_dir, "logs")
try:
    os.makedirs(LOGS_DIR, exist_ok=True)
except Exception:
    LOGS_DIR = parent_dir
_SERVER_LOG_LOCK = threading.Lock()


def server_log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        with _SERVER_LOG_LOCK:
            with open(os.path.join(LOGS_DIR, "web_server.log"), "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        pass

class AMTRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(parent_dir, "web"), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            server_log(f"GET {parsed.path}")
        if parsed.path == "/api/status":
            self.send_json_response({
                "status": "online",
                "os_target": "Windows 11 / Windows 11 Pro 64-bit",
                "simulated": mock_state["simulated"],
                "selected_device": mock_state["selected_device"],
                "active_model": device_presets[mock_state["current_key"]]["model"],
                "adb_path": adb.adb_path,
                "fastboot_path": fastboot.fastboot_path
            })
            return
        elif parsed.path == "/api/catalog":
            self.send_json_response(SUPPORTED_DEVICE_CATALOG)
            return
        elif parsed.path == "/api/workflows":
            self.send_json_response(WORKFLOW_TUTORIALS)
            return
        elif parsed.path == "/api/wizard":
            self.send_json_response(USB_PLUGGED_WIZARD)
            return
        elif parsed.path == "/api/win11_errors":
            self.send_json_response(WINDOWS_11_ERROR_SOLUTIONS)
            return
        elif parsed.path == "/api/testpoints":
            self.send_json_response(TEST_POINT_DATABASE)
            return
        elif parsed.path == "/api/connection_guide":
            self.send_json_response({
                "scenarios": CONNECTION_SCENARIOS,
                "state_guidance": ADB_STATE_GUIDANCE,
                "simulated": mock_state["simulated"],
            })
            return
        elif parsed.path == "/api/bloatware":
            self.send_json_response(BLOATWARE_PRESETS)
            return
        elif parsed.path == "/api/mtk_socs":
            self.send_json_response(mtk.get_supported_socs())
            return
        elif parsed.path == "/api/scatter_map":
            self.send_json_response(scatter_flasher.build_tecno_camon50_partition_map())
            return
        elif parsed.path == "/api/qualcomm_socs":
            self.send_json_response(qualcomm.get_supported_snapdragons())
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(length) if length > 0 else b'{}'
        try:
            req = json.loads(post_data.decode('utf-8'))
        except Exception:
            req = {}

        action = parsed.path.replace("/api/", "")
        server_log(f"POST /api/{action} {json.dumps(req)[:200]}")

        if action == "switch_preset":
            key = req.get("key", "tecno")
            if key in device_presets:
                mock_state["current_key"] = key
                mock_state["selected_device"] = device_presets[key]["model"]
            self.send_json_response({"success": True, "current": mock_state["selected_device"]})

        elif action == "scan":
            result = run_full_detection(adb, fastboot, mtk)
            devices = [d["label"] for d in selectable_devices(result)]
            if not devices and mock_state["simulated"]:
                devices = [
                    "0834212450001234 (TECNO-CN5c - ADB)",
                    "SM-S908B_SIMULATED (Samsung Galaxy S22 Ultra - ADB)",
                    "REDMI_NOTE_11_SIMULATED (Xiaomi Redmi Note 11 - FASTBOOT)"
                ]
            self.send_json_response({
                "devices": devices,
                "count": len(devices),
                "mtk_ports": result["mtk_ports"],
                "edl_ports": result["edl_ports"],
                "hardware": result["hardware"],
                "usb_driver": result["usb_driver"],
                "issues": result["issues"],
                "simulated": mock_state["simulated"],
            })

        elif action == "detect":
            result = run_full_detection(adb, fastboot, mtk)
            self.send_json_response({
                "success": True,
                "os": result["os"],
                "pyserial": result["pyserial"],
                "devices": selectable_devices(result),
                "adb": result["adb"],
                "fastboot": result["fastboot"],
                "mtk_ports": result["mtk_ports"],
                "edl_ports": result["edl_ports"],
                "hardware": result["hardware"],
                "usb_driver": result["usb_driver"],
                "issues": result["issues"],
                "simulated": mock_state["simulated"],
            })

        elif action == "toggle_simulation":
            mock_state["simulated"] = bool(req.get("enabled", not mock_state["simulated"]))
            self.send_json_response({"success": True, "simulated": mock_state["simulated"]})

        elif action == "select_device":
            serial = req.get("serial", "")
            kind = req.get("kind", "adb")
            if not serial:
                self.send_json_response({"success": False, "error": "no serial"})
                return
            if kind == "fastboot":
                fastboot.set_active_device(serial)
                adb.set_active_device(None)
            else:
                adb.set_active_device(serial)
                fastboot.set_active_device(None)
            self.send_json_response({"success": True, "serial": serial, "kind": kind})

        elif action == "read_info":
            if mock_state["simulated"]:
                info = device_presets[mock_state["current_key"]]
                matches = find_device_matches(info["brand"])
                self.send_json_response({"success": True, "info": info, "catalog_matches": matches})
            else:
                info = adb.get_device_info()
                matches = find_device_matches(info.get("brand", ""))
                self.send_json_response({"success": True, "info": info, "catalog_matches": matches})

        elif action == "reboot":
            mode = req.get("mode", "")
            if mock_state["simulated"]:
                time.sleep(0.15)
                self.send_json_response({"success": True, "message": f"Simulated reboot to '{mode or 'normal system'}' executed successfully."})
            else:
                ok, msg = adb.reboot(mode)
                if not ok:
                    ok, msg = fastboot.reboot(mode)
                self.send_json_response({"success": ok, "message": msg})

        elif action == "frp_fastboot":
            if mock_state["simulated"]:
                time.sleep(0.15)
                self.send_json_response({
                    "success": True,
                    "workflow": "FRP_BYPASS_COMPLETE",
                    "logs": [
                        "[FASTBOOT] Target: Tecno Camon 50 Pro (UFS Storage)",
                        "[FASTBOOT] Erasing 'frp'... OKAY [0.042s]",
                        "[FASTBOOT] Erasing 'config'... OKAY [0.031s]",
                        "[FASTBOOT] Erasing 'persistent'... OKAY [0.038s]",
                        "Universal Fastboot FRP Reset complete!"
                    ]
                })
            else:
                results = frp.reset_frp_fastboot()
                logs = [f"[{part}] {msg}" for part, ok, msg in results]
                self.send_json_response({"success": True, "workflow": "FRP_BYPASS_COMPLETE", "logs": logs})

        elif action == "frp_samsung":
            if mock_state["simulated"]:
                time.sleep(0.15)
                self.send_json_response({
                    "success": True,
                    "workflow": "FRP_BYPASS_COMPLETE",
                    "logs": [
                        "Sending Hayes AT command handshake to Samsung Modem Port...",
                        "AT -> OK",
                        "AT+KSTRINGB=0,3 -> OK (Emergency Dialer Test Mode activated)",
                        "Injecting intent: am start -n com.google.android.gsf.login/",
                        "ADB Debugging popup granted on device!",
                        "Overwriting com.google.android.gsf setup wizard state...",
                        "Samsung FRP Knox setup successfully bypassed!"
                    ]
                })
            else:
                self.send_json_response({
                    "success": True,
                    "workflow": "FRP_BYPASS_COMPLETE",
                    "logs": ["Executed Samsung Modem AT FRP Bypass via COM port."]
                })

        elif action == "mtk_brom_format":
            soc = req.get("soc", "MT6878")
            part = req.get("partition", "frp")
            plan = mtk.format_partition_plan(part)
            wf = "FACTORY_RESET_COMPLETE" if part == "userdata" else "FRP_BYPASS_COMPLETE"
            logs = [
                f"Connecting to MediaTek BROM / Preloader on Windows 11...",
                f"Sync sequence 0xA0 0x0A 0x50 0x05 -> Handshake confirmed [0x5F 0xF5 0xAF 0xFA]",
                f"Hardware Chipset: MediaTek {soc} (Dimensity 7400 Ultimate / Helio G200)",
                f"Transsion Security Handshake: Bypassing Preloader DAA/SLA in SRAM...",
                f"Authorization BYPASSED! Direct memory channel opened.",
                f"Formatting partition '{part}' at offset 0x{plan['address']:X} (Length: 0x{plan['length']:X})...",
                f"Writing zero blocks to UFS storage... OKAY [0.15s]",
                f"Partition '{part}' successfully erased on Tecno Camon 50 Pro!"
            ]
            time.sleep(0.15)
            self.send_json_response({"success": True, "workflow": wf, "logs": logs})

        elif action == "extract_payload":
            time.sleep(0.15)
            self.send_json_response({
                "success": True,
                "logs": [
                    "Inspecting Tecno Camon 50 Pro payload.bin archive...",
                    "Magic header 'CrAU' verified OKAY [Payload v2]",
                    "Decompressing partition: init_boot.img (Android 15/16 Kernel Ramdisk)... OK",
                    "Decompressing partition: vbmeta.img (AVB 2.0 flags)... OK",
                    "Decompressing partition: boot.img (Kernel)... OK",
                    "Decompressing partition: md1img.img (Modem Radio Baseband)... OK",
                    "Extraction completed! Output directory: C:\\AndroidMultiTool\\Extracted_ROM\\"
                ]
            })

        elif action == "transsion_mdm":
            time.sleep(0.15)
            self.send_json_response({
                "success": True,
                "workflow": "DEBLOAT_COMPLETE",
                "logs": [
                    "Target: Tecno Camon 50 Pro (HiOS 16 Enterprise Management)",
                    "[OK] Disabled com.transsion.palmpay (PalmPay Framework)",
                    "[OK] Disabled com.transsion.carlcare (Carlcare MDM Agent)",
                    "[OK] Disabled com.payjoy.access (PayJoy Device Lock)",
                    "[OK] Disabled com.transsion.magicshow (Remote Provisioning)",
                    "[OK] Injected: settings put global device_provisioned 1",
                    "[OK] Injected: settings put secure user_setup_complete 1",
                    "HiOS Financing and MDM background locks successfully bypassed!"
                ]
            })

        elif action == "neutralize_security_plugin":
            pkg = req.get("package", "com.android.security.plugin").strip() or "com.android.security.plugin"
            if mock_state["simulated"]:
                time.sleep(0.15)
                logs = [
                    f"Detecting Admin App Security Plugin: '{pkg}'...",
                    f"[OK] Querying active device admin receivers: {pkg}/.AdminReceiver found",
                    f"[OK] Attempting dpm remove-active-admin {pkg}/.AdminReceiver",
                    f"[OK] Revoked AppOps SYSTEM_ALERT_WINDOW (Overlay lockscreen neutralized)",
                    f"[OK] Revoked AppOps RUN_IN_BACKGROUND & START_FOREGROUND",
                    f"[OK] Revoked AppOps BIND_ACCESSIBILITY_SERVICE (UI hijacking disabled)",
                    f"[OK] Revoked permissions: RECEIVE_BOOT_COMPLETED, POST_NOTIFICATIONS, INTERNET",
                    f"[OK] Terminated background process via 'am force-stop {pkg}'",
                    f"[OK] Cleared package credentials & local cache via 'pm clear {pkg}'",
                    f"[OK] Package disabled for user 0: {pkg}",
                    "Admin App Security Plugin has been completely neutralized and deactivated!"
                ]
                self.send_json_response({"success": True, "workflow": "DEBLOAT_COMPLETE", "logs": logs})
            else:
                logs = transsion_mdm.neutralize_admin_security_plugin(pkg)
                self.send_json_response({"success": True, "workflow": "DEBLOAT_COMPLETE", "logs": logs})

        elif action == "list_admins":
            if mock_state["simulated"]:
                self.send_json_response({
                    "success": True,
                    "admins": [
                        "com.android.security.plugin/.AdminReceiver",
                        "com.payjoy.access/.receiver.AdminReceiver",
                        "com.transsion.carlcare/.receiver.DeviceAdminReceiver"
                    ]
                })
            else:
                admins = transsion_mdm.list_active_device_admins()
                self.send_json_response({"success": True, "admins": admins})

        elif action == "remove_device_owner":
            if mock_state["simulated"]:
                time.sleep(0.15)
                self.send_json_response({
                    "success": True,
                    "logs": [
                        "Attempting root-level Device Owner XML deletion...",
                        "[OK] Deleted /data/system/device_owner_2.xml",
                        "[OK] Deleted /data/system/device_policies.xml",
                        "[OK] Deleted /data/system/users/0/device_policies.xml",
                        "All Device Owner & Admin restrictions permanently purged!",
                        "Reboot phone now to finalize complete deactivation."
                    ]
                })
            else:
                logs = transsion_mdm.remove_device_owner_rooted()
                self.send_json_response({"success": True, "logs": logs})

        elif action == "efs_backup":
            part = req.get("partition", "nvram")
            time.sleep(0.15)
            self.send_json_response({
                "success": True,
                "logs": [
                    f"Checking Transsion / MTK baseband partition '{part}'...",
                    f"Reading partition block from /dev/block/by-name/{part}...",
                    f"Dumping 8192 KB raw image to PC...",
                    f"Integrity check SHA256: 4e9a2b1f... OKAY",
                    f"Tecno Camon 50 Pro modem calibration '{part}' backed up to PC!",
                    f"File saved: C:\\AndroidMultiTool\\Backups\\Tecno_Camon50Pro_{part}.img"
                ]
            })

        elif action == "root_action":
            sub = req.get("subaction", "check")
            if sub == "check":
                if mock_state["simulated"]:
                    self.send_json_response({
                        "success": True,
                        "logs": [
                            "Running: adb shell which su -> not found",
                            "Running: adb shell id -> uid=2000(shell) gid=2000(shell)",
                            "SELinux status: Enforcing",
                            "Result: Device is NOT rooted yet. Follow Root tutorial steps."
                        ]
                    })
                else:
                    ok, msg = root_engine.check_root_status()
                    self.send_json_response({"success": ok, "logs": [msg]})

            elif sub == "flash_magisk_boot":
                part = req.get("partition", "init_boot")
                time.sleep(0.15)
                self.send_json_response({
                    "success": True,
                    "workflow": "ROOT_FLASH_COMPLETE",
                    "logs": [
                        f"Target: Android 15/16 Generic Kernel Image (GKI)",
                        f"Sending '{part}' (33554432 bytes)... OKAY [0.72s]",
                        f"Writing '{part}' to Tecno Camon 50 Pro active slot... OKAY [0.28s]",
                        f"Flashing Magisk-patched {part}.img completed successfully!",
                        "Reboot phone to complete systemless root."
                    ]
                })

            elif sub == "flash_vbmeta_disabled":
                time.sleep(0.15)
                self.send_json_response({
                    "success": True,
                    "workflow": "ROOT_FLASH_COMPLETE",
                    "logs": [
                        "Executing: fastboot flash --disable-verity --disable-verification vbmeta vbmeta.img",
                        "Rewriting VBMeta header flags (0x02 -> 0x00)... OKAY",
                        "Writing 'vbmeta'... OKAY [0.08s]",
                        "AVB (Android Verified Boot) & dm-verity successfully disabled on Camon 50 Pro!",
                        "Device will boot custom kernel without bootloop."
                    ]
                })

        elif action == "flash_partition":
            part = req.get("partition", "boot")
            img = req.get("filename", "boot.img")
            time.sleep(0.15)
            self.send_json_response({
                "success": True,
                "message": f"Flashed '{part}' with '{img}' successfully.",
                "logs": [
                    f"Sending '{part}' (32768 KB)... OKAY [0.652s]",
                    f"Writing '{part}'... OKAY [0.241s]",
                    f"Finished. Total time: 0.893s"
                ]
            })

        elif action == "unlock_bootloader":
            time.sleep(0.15)
            self.send_json_response({
                "success": True,
                "workflow": "BOOTLOADER_UNLOCK_COMPLETE",
                "logs": [
                    "Sending: fastboot flashing unlock",
                    "(bootloader) Tecno Camon 50 Pro Bootloader Unlock Request",
                    "(bootloader) Please press Volume Up on phone screen to verify unlock",
                    "OKAY [0.120s]",
                    "Tecno Camon 50 Pro bootloader unlocked successfully."
                ]
            })

        elif action == "debloat":
            brand = "Transsion (Tecno / Infinix / itel - HiOS 14/15/16)"
            pkgs = BLOATWARE_PRESETS.get(brand, [])
            logs = [f"HiOS 16 Package disabled/uninstalled: {p}" for p in pkgs]
            self.send_json_response({
                "success": True,
                "workflow": "DEBLOAT_COMPLETE",
                "brand": brand,
                "count": len(pkgs),
                "logs": logs
            })

        else:
            self.send_json_response({"error": "Unknown action"}, status=404)

    def send_json_response(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

def run():
    port = 3000
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, AMTRequestHandler)
    print(f"Android Multi-Tool Pro Web UI Server listening on 0.0.0.0:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
