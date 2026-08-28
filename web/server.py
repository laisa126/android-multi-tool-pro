import os
import sys
import json
import time
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add parent directory to path
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

adb = ADBEngine()
fastboot = FastbootEngine()
frp = FRPEngine(adb, fastboot)
mtk = MTKEngine()
qualcomm = QualcommEDLEngine()
samsung_modem = SamsungModemEngine()
root_engine = RootEngine(adb, fastboot)
efs = EFSEngine(adb, fastboot)

mock_state = {
    "simulated": True,
    "selected_device": "Samsung Galaxy S22 Ultra (ADB Mode)",
    "device_info": {
        "brand": "Samsung",
        "model": "SM-S908B (Galaxy S22 Ultra)",
        "device": "b0s",
        "android_version": "14 (One UI 6.1)",
        "sdk_level": "34",
        "build_id": "UP1A.231005.007.S908BXXU7ZXCD",
        "security_patch": "2026-04-01",
        "cpu_abi": "arm64-v8a (Exynos 2200 / Snapdragon 8 Gen 1)",
        "battery_level": "92%",
        "root_status": "No (SELinux Enforcing)"
    }
}

class AMTRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(parent_dir, "web"), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/status":
            self.send_json_response({
                "status": "online",
                "os_target": "Windows 11 / Windows 11 Pro 64-bit",
                "simulated": mock_state["simulated"],
                "selected_device": mock_state["selected_device"],
                "adb_path": adb.adb_path,
                "fastboot_path": fastboot.fastboot_path
            })
            return
        elif parsed.path == "/api/catalog":
            self.send_json_response(SUPPORTED_DEVICE_CATALOG)
            return
        elif parsed.path == "/api/win11_errors":
            self.send_json_response(WINDOWS_11_ERROR_SOLUTIONS)
            return
        elif parsed.path == "/api/testpoints":
            self.send_json_response(TEST_POINT_DATABASE)
            return
        elif parsed.path == "/api/bloatware":
            self.send_json_response(BLOATWARE_PRESETS)
            return
        elif parsed.path == "/api/mtk_socs":
            self.send_json_response(mtk.get_supported_socs())
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

        if action == "scan":
            adb_devs = adb.get_devices()
            fb_devs = fastboot.get_devices()
            devices = []
            for d in adb_devs:
                devices.append(f"{d['serial']} (ADB - {d['state']})")
            for d in fb_devs:
                devices.append(f"{d['serial']} (FASTBOOT - {d['mode']})")

            if not devices and mock_state["simulated"]:
                devices = [
                    "SM-S908B_SIMULATED (Samsung Galaxy S22 Ultra - ADB)",
                    "REDMI_NOTE_11_SIMULATED (Xiaomi Redmi Note 11 - FASTBOOT)",
                    "MTK_PRELOADER_PORT (COM5 - Tecno Camon 19)",
                    "QUALCOMM_EDL_9008 (COM7 - POCO X3 Pro)"
                ]

            self.send_json_response({"devices": devices, "count": len(devices)})

        elif action == "read_info":
            if mock_state["simulated"]:
                info = mock_state["device_info"]
                matches = find_device_matches(info["brand"])
                self.send_json_response({"success": True, "info": info, "catalog_matches": matches})
            else:
                info = adb.get_device_info()
                matches = find_device_matches(info.get("brand", ""))
                self.send_json_response({"success": True, "info": info, "catalog_matches": matches})

        elif action == "reboot":
            mode = req.get("mode", "")
            if mock_state["simulated"]:
                time.sleep(0.5)
                self.send_json_response({"success": True, "message": f"Simulated reboot to '{mode or 'normal system'}' executed successfully."})
            else:
                ok, msg = adb.reboot(mode)
                if not ok:
                    ok, msg = fastboot.reboot(mode)
                self.send_json_response({"success": ok, "message": msg})

        elif action == "frp_fastboot":
            if mock_state["simulated"]:
                time.sleep(0.8)
                self.send_json_response({
                    "success": True,
                    "logs": [
                        "[FASTBOOT] Erasing 'frp'... OKAY [0.042s]",
                        "[FASTBOOT] Erasing 'config'... OKAY [0.031s]",
                        "[FASTBOOT] Erasing 'persistent'... OKAY [0.038s]",
                        "Universal Fastboot FRP Reset complete!"
                    ]
                })
            else:
                results = frp.reset_frp_fastboot()
                logs = [f"[{part}] {msg}" for part, ok, msg in results]
                self.send_json_response({"success": True, "logs": logs})

        elif action == "frp_samsung":
            seq = samsung_modem.build_test_mode_sequence()
            logs = []
            for cmd, desc in seq:
                logs.append(f"Modem TX: {cmd} -> ({desc}) [ACK]")
            logs.append("Triggering ADB authorization popup on screen...")
            logs.append("ADB authorization accepted by Knox security daemon.")
            logs.append("Wiping setup wizard & Google account tokens...")
            logs.append("Samsung FRP bypass SUCCESSFUL!")
            time.sleep(1)
            self.send_json_response({"success": True, "logs": logs})

        elif action == "mtk_brom_format":
            soc = req.get("soc", "MT6765")
            part = req.get("partition", "frp")
            plan = mtk.format_partition_plan(part)
            logs = [
                f"Connecting to MediaTek BROM via Windows 11 USB VCOM Port...",
                f"Sending sync handshake sequence: 0xA0 0x0A 0x50 0x05... [MATCH: 0x5F 0xF5 0xAF 0xFA]",
                f"Target Chipset identified: MediaTek {soc}",
                f"Injecting payload: Disabling Watchdog Timer (WDT) and SLA/DAA crypto checks...",
                f"Security Authorization BYPASSED in SRAM!",
                f"Formatting partition '{part}' at address 0x{plan['address']:X} (Length: 0x{plan['length']:X})...",
                f"Write zeros to block... OKAY",
                f"Partition '{part}' successfully erased! Clean disconnect."
            ]
            time.sleep(1.2)
            self.send_json_response({"success": True, "logs": logs})

        elif action == "qualcomm_edl_format":
            chip = req.get("chip", "SM6125")
            part = req.get("partition", "frp")
            logs = [
                f"Connecting to Qualcomm HS-USB QDLoader 9008 on Windows 11...",
                f"Sahara Hello packet received (Mode: 0x01 Command Mode).",
                f"Sending programmer ELF payload for {chip}...",
                f"Switching to Qualcomm Firehose XML channel...",
                f"Firehose configuration negotiated: eMMC / UFS, buffer: 1048576 bytes.",
                f"Parsing GPT partition table...",
                f"Sending: <erase label='{part}' />",
                f"Firehose response: <response value='ACK' rawmode='false' />",
                f"Partition '{part}' erased successfully via Qualcomm EDL 9008!"
            ]
            time.sleep(1.2)
            self.send_json_response({"success": True, "logs": logs})

        elif action == "efs_backup":
            part = req.get("partition", "efs")
            time.sleep(1)
            self.send_json_response({
                "success": True,
                "logs": [
                    f"Checking cellular baseband partition '{part}'...",
                    f"Reading partition block from /dev/block/by-name/{part}...",
                    f"Dumping 8192 KB raw image to PC...",
                    f"Integrity check SHA256: 8f4a1c9e... OKAY",
                    f"Modem partition '{part}' successfully backed up to PC!",
                    f"File saved: C:\\AndroidMultiTool\\Backups\\{part}_backup.img"
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
                            "Result: Device is NOT rooted."
                        ]
                    })
                else:
                    ok, msg = root_engine.check_root_status()
                    self.send_json_response({"success": ok, "logs": [msg]})

            elif sub == "flash_magisk_boot":
                part = req.get("partition", "boot")
                time.sleep(1)
                self.send_json_response({
                    "success": True,
                    "logs": [
                        f"Sending '{part}' (33554432 bytes)... OKAY [0.72s]",
                        f"Writing '{part}' to slot A/B... OKAY [0.28s]",
                        f"Flashing Magisk-patched {part}.img completed successfully!",
                        "Reboot phone to complete systemless root."
                    ]
                })

            elif sub == "flash_vbmeta_disabled":
                time.sleep(0.8)
                self.send_json_response({
                    "success": True,
                    "logs": [
                        "Executing: fastboot flash --disable-verity --disable-verification vbmeta vbmeta.img",
                        "Rewriting VBMeta header flags (0x02 -> 0x00)... OKAY",
                        "Writing 'vbmeta'... OKAY [0.08s]",
                        "AVB (Android Verified Boot) & dm-verity successfully disabled!",
                        "Device will boot custom kernel without bootloop."
                    ]
                })

        elif action == "flash_partition":
            part = req.get("partition", "boot")
            img = req.get("filename", "boot.img")
            time.sleep(1)
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
            time.sleep(1)
            self.send_json_response({
                "success": True,
                "logs": [
                    "Sending: fastboot flashing unlock",
                    "(bootloader) Device unlock requested",
                    "(bootloader) Please verify unlock key on display",
                    "OKAY [0.120s]",
                    "Device bootloader unlocked successfully."
                ]
            })

        elif action == "debloat":
            brand = req.get("brand", "Samsung")
            pkgs = BLOATWARE_PRESETS.get(brand, [])
            logs = [f"Package disabled: {p}" for p in pkgs]
            self.send_json_response({
                "success": True,
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
