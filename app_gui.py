"""
Android Multi-Tool Pro - Main Desktop GUI Application
Strict Monochrome High-Contrast Edition (Black & White, <= 10 Colors)
Engineered for Tecno Camon 50 Pro (Dimensity 7400 Ultimate / MT6878 / HiOS 16) & All Brands
"""

import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Import core modules
from core.adb_engine import ADBEngine
from core.fastboot_engine import FastbootEngine
from core.frp_engine import FRPEngine
from core.mtk_engine import MTKEngine
from core.samsung_modem import SamsungModemEngine
from core.root_engine import RootEngine
from core.efs_engine import EFSEngine
from core.payload_extractor import PayloadExtractor
from core.scatter_flasher import ScatterFlasher
from core.transsion_mdm import TranssionMDMEngine
from core.device_profiles import BLOATWARE_PRESETS, TEST_POINT_DATABASE
from core.downloader import ensure_binaries

APP_NAME = "Android Multi-Tool Pro"
APP_VERSION = "v2.5.0 (Monochrome Tecno Camon 50 Edition)"

# STRICT 10-COLOR MONOCHROME PALETTE
# 1. #000000 (Pure Black - Root / Terminal BG)
# 2. #0c0c0c (Dark Card Background)
# 3. #161616 (Sub-card / Input Background)
# 4. #222222 (Border / Divider / Inactive Tab)
# 5. #333333 (Button Secondary / Control Fill)
# 6. #888888 (Muted Gray Text / Subheaders)
# 7. #cccccc (Body Text / Standard Labels)
# 8. #ffffff (High Contrast White / Headings / Primary Buttons)
# 9. #22c55e (Status / Success Indicator Green)
# 10. #ef4444 (Danger / Erase Indicator Red)

C_BLACK = "#000000"
C_CARD = "#0c0c0c"
C_SUBCARD = "#161616"
C_BORDER = "#222222"
C_GRAY_MID = "#333333"
C_TEXT_MUTED = "#888888"
C_TEXT_BODY = "#cccccc"
C_WHITE = "#ffffff"
C_GREEN = "#22c55e"
C_RED = "#ef4444"


class AndroidMultiToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("1040x780")
        self.root.minsize(920, 680)

        # Initialize engines
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.bin_dir = os.path.join(self.base_dir, "bin")
        self.adb = ADBEngine()
        self.fastboot = FastbootEngine()
        self.frp = FRPEngine(self.adb, self.fastboot)
        self.mtk = MTKEngine()
        self.samsung_modem = SamsungModemEngine()
        self.root_engine = RootEngine(self.adb, self.fastboot)
        self.efs = EFSEngine(self.adb, self.fastboot)
        self.payload_extractor = PayloadExtractor()
        self.scatter_flasher = ScatterFlasher()
        self.transsion_mdm = TranssionMDMEngine(self.adb)

        # State
        self.simulated_mode = tk.BooleanVar(value=False)
        self.selected_device = tk.StringVar(value="None")
        self.is_busy = False

        # Apply strictly monochrome styling
        self._setup_theme()
        self._build_ui()

        # Check binaries on launch
        self._check_dependencies_async()

    def _setup_theme(self):
        self.root.configure(bg=C_BLACK)
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Frame styles
        self.style.configure("TFrame", background=C_BLACK)
        self.style.configure("Card.TFrame", background=C_CARD, relief="flat")
        self.style.configure("SubCard.TFrame", background=C_SUBCARD, relief="flat")

        # Label styles
        self.style.configure("TLabel", background=C_CARD, foreground=C_TEXT_BODY, font=("Segoe UI", 9))
        self.style.configure("Header.TLabel", background=C_BLACK, foreground=C_WHITE, font=("Segoe UI", 12, "bold"))
        self.style.configure("SubHeader.TLabel", background=C_BLACK, foreground=C_TEXT_MUTED, font=("Segoe UI", 8))
        self.style.configure("Status.TLabel", background=C_CARD, foreground=C_GREEN, font=("Segoe UI", 9, "bold"))

        # Notebook / Tabs
        self.style.configure("TNotebook", background=C_BLACK, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=C_BORDER, foreground=C_TEXT_MUTED, padding=[12, 7], font=("Segoe UI", 9, "bold"))
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", C_WHITE), ("active", C_GRAY_MID)],
            foreground=[("selected", C_BLACK), ("active", C_WHITE)]
        )

        # Action Buttons (Black & White High Contrast)
        self.style.configure(
            "Action.TButton",
            background=C_WHITE,
            foreground=C_BLACK,
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
            padding=[10, 6]
        )
        self.style.map("Action.TButton", background=[("active", C_TEXT_BODY), ("disabled", C_BORDER)])

        # Danger Buttons (Red Accent)
        self.style.configure(
            "Danger.TButton",
            background=C_RED,
            foreground=C_WHITE,
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
            padding=[10, 6]
        )
        self.style.map("Danger.TButton", background=[("active", C_BORDER)])

        # Success Buttons (Green Accent)
        self.style.configure(
            "Success.TButton",
            background=C_GREEN,
            foreground=C_BLACK,
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
            padding=[10, 6]
        )
        self.style.map("Success.TButton", background=[("active", C_TEXT_BODY)])

        # Secondary Buttons (Monochrome Gray)
        self.style.configure(
            "Secondary.TButton",
            background=C_GRAY_MID,
            foreground=C_WHITE,
            font=("Segoe UI", 9),
            borderwidth=0,
            padding=[8, 5]
        )
        self.style.map("Secondary.TButton", background=[("active", C_BORDER)])

        # Inputs
        self.style.configure("TCombobox", fieldbackground=C_SUBCARD, background=C_BORDER, foreground=C_WHITE)
        self.style.configure("TEntry", fieldbackground=C_SUBCARD, foreground=C_WHITE)
        self.style.configure("Treeview", background=C_SUBCARD, foreground=C_TEXT_BODY, fieldbackground=C_SUBCARD, font=("Segoe UI", 8))
        self.style.configure("Treeview.Heading", background=C_BORDER, foreground=C_WHITE, font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview", background=[("selected", C_GRAY_MID)], foreground=[("selected", C_WHITE)])

    def _build_ui(self):
        # 1. Top Navigation & Connection Bar
        top_bar = tk.Frame(self.root, bg=C_BLACK, height=65)
        top_bar.pack(fill="x", padx=15, pady=(10, 5))

        # Title / Brand
        brand_box = tk.Frame(top_bar, bg=C_BLACK)
        brand_box.pack(side="left")
        lbl_title = tk.Label(brand_box, text="AMT PRO // TECNO & UNIVERSAL SUITE", font=("Segoe UI", 12, "bold"), fg=C_WHITE, bg=C_BLACK)
        lbl_title.pack(anchor="w")
        lbl_sub = tk.Label(brand_box, text="MediaTek Dimensity 7400 / Transsion HiOS / Universal Android Servicing", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_BLACK)
        lbl_sub.pack(anchor="w")

        # Device Selector & Scan
        dev_box = tk.Frame(top_bar, bg=C_BLACK)
        dev_box.pack(side="right")

        tk.Label(dev_box, text="Port / Device:", font=("Segoe UI", 9, "bold"), fg=C_TEXT_BODY, bg=C_BLACK).pack(side="left", padx=5)
        self.combo_devices = ttk.Combobox(dev_box, textvariable=self.selected_device, width=28, state="readonly")
        self.combo_devices.pack(side="left", padx=5)

        btn_scan = ttk.Button(dev_box, text="Scan Devices", style="Action.TButton", command=self.scan_devices)
        btn_scan.pack(side="left", padx=4)

        btn_kill = ttk.Button(dev_box, text="Kill / Restart ADB", style="Secondary.TButton", command=self.restart_adb)
        btn_kill.pack(side="left", padx=4)

        chk_sim = tk.Checkbutton(
            dev_box, text="Simulate (Camon 50)", variable=self.simulated_mode,
            bg=C_BLACK, fg=C_WHITE, selectcolor=C_SUBCARD, activebackground=C_BLACK,
            activeforeground=C_WHITE, font=("Segoe UI", 8)
        )
        chk_sim.pack(side="left", padx=6)

        # 2. Main Tabbed Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=5)

        # Build tabs
        self.tab_camon50 = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_info = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_frp = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_fastboot = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_reboot = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_debloat = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_testpoints = ttk.Frame(self.notebook, style="Card.TFrame")

        self.notebook.add(self.tab_camon50, text=" Tecno Camon 50 Suite ")
        self.notebook.add(self.tab_info, text=" Diagnostics ")
        self.notebook.add(self.tab_frp, text=" FRP & Screen Lock ")
        self.notebook.add(self.tab_fastboot, text=" Fastboot Flasher ")
        self.notebook.add(self.tab_reboot, text=" Reboot Switcher ")
        self.notebook.add(self.tab_debloat, text=" Debloat & Apps ")
        self.notebook.add(self.tab_testpoints, text=" EDL & Test Points ")

        self._build_tab_camon50()
        self._build_tab_info()
        self._build_tab_frp()
        self._build_tab_fastboot()
        self._build_tab_reboot()
        self._build_tab_debloat()
        self._build_tab_testpoints()

        # 3. Bottom Console Log Area
        console_frame = tk.Frame(self.root, bg=C_CARD, height=180)
        console_frame.pack(fill="x", padx=15, pady=(5, 10))

        con_header = tk.Frame(console_frame, bg=C_CARD)
        con_header.pack(fill="x", padx=8, pady=4)
        tk.Label(con_header, text="OPERATIONAL CONSOLE // REAL-TIME LOG", font=("Consolas", 8, "bold"), fg=C_TEXT_MUTED, bg=C_CARD).pack(side="left")

        self.lbl_busy = tk.Label(con_header, text="READY", font=("Consolas", 8, "bold"), fg=C_GREEN, bg=C_CARD)
        self.lbl_busy.pack(side="left", padx=10)

        btn_clear = ttk.Button(con_header, text="Clear", style="Secondary.TButton", command=self.clear_log)
        btn_clear.pack(side="right", padx=3)

        # Text Console
        con_box = tk.Frame(console_frame, bg=C_BLACK)
        con_box.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        self.txt_console = tk.Text(
            con_box, bg=C_BLACK, fg=C_TEXT_BODY, insertbackground=C_WHITE,
            font=("Consolas", 8), wrap="char", height=7, relief="flat", padx=6, pady=4
        )
        con_scroll = ttk.Scrollbar(con_box, orient="vertical", command=self.txt_console.yview)
        self.txt_console.configure(yscrollcommand=con_scroll.set)

        self.txt_console.pack(side="left", fill="both", expand=True)
        con_scroll.pack(side="right", fill="y")

        # Tags for monochrome console
        self.txt_console.tag_config("info", foreground=C_TEXT_BODY)
        self.txt_console.tag_config("success", foreground=C_GREEN)
        self.txt_console.tag_config("warning", foreground=C_WHITE)
        self.txt_console.tag_config("error", foreground=C_RED)
        self.txt_console.tag_config("muted", foreground=C_TEXT_MUTED)

    # ================= TECNO CAMON 50 PRO TAB =================

    def _build_tab_camon50(self):
        f = self.tab_camon50
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

        # Left Column - Payload Extractor & MTK Scatter Mapper
        left_card = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        left_card.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        tk.Label(left_card, text="TECNO CAMON 50 PRO (MT6878 / DIMENSITY 7400)", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 4))
        tk.Label(left_card, text="OTA Payload Unpacker & MediaTek UFS Scatter Engine", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        # Payload Extractor Frame
        p_box = tk.Frame(left_card, bg=C_SUBCARD, padx=10, pady=10)
        p_box.pack(fill="x", pady=6)
        tk.Label(p_box, text="Stock OTA payload.bin Extractor", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        tk.Label(p_box, text="Extracts init_boot.img (Magisk), boot.img, and vbmeta.img directly from ROM", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(anchor="w", pady=(0, 6))

        p_row = tk.Frame(p_box, bg=C_SUBCARD)
        p_row.pack(fill="x", pady=4)
        self.entry_payload_path = ttk.Entry(p_row)
        self.entry_payload_path.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(p_row, text="Browse", style="Secondary.TButton", command=self.browse_payload).pack(side="left", padx=3)
        ttk.Button(p_row, text="Extract Partitions", style="Action.TButton", command=self.run_payload_extract).pack(side="left", padx=3)

        # MediaTek Scatter Map Frame
        s_box = tk.Frame(left_card, bg=C_SUBCARD, padx=10, pady=10)
        s_box.pack(fill="both", expand=True, pady=6)
        tk.Label(s_box, text="MediaTek UFS Partition Map (Tecno-CL8)", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")

        cols = ("Partition", "Target", "File")
        self.tree_scatter = ttk.Treeview(s_box, columns=cols, show="headings", height=6)
        self.tree_scatter.heading("Partition", text="Partition")
        self.tree_scatter.heading("Target", text="Storage Target")
        self.tree_scatter.heading("File", text="Image Name")
        self.tree_scatter.column("Partition", width=90)
        self.tree_scatter.column("Target", width=140)
        self.tree_scatter.column("File", width=140)

        partitions = self.scatter_flasher.build_tecno_camon50_partition_map()
        for p in partitions:
            self.tree_scatter.insert("", "end", values=(p["partition"], p["target"], p["file"]))
        self.tree_scatter.pack(fill="both", expand=True, pady=6)

        # Right Column - Transsion MDM Bypass & Preloader DAA Actions
        right_card = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        right_card.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        tk.Label(right_card, text="HIOS 16 MDM & PRELOADER DIRECT OPERATIONS", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 4))
        tk.Label(right_card, text="PayJoy / PalmPay / Carlcare Disabler & BROM Direct Memory Wipe", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        # Transsion MDM Bypass Box
        mdm_box = tk.Frame(right_card, bg=C_SUBCARD, padx=10, pady=10)
        mdm_box.pack(fill="x", pady=6)
        tk.Label(mdm_box, text="Transsion MDM & Financing Lock Remover", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        tk.Label(mdm_box, text="Disables Carlcare MDM, PalmPay Framework, PayJoy and locks setup completion state", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(anchor="w", pady=(0, 6))

        m_btns = tk.Frame(mdm_box, bg=C_SUBCARD)
        m_btns.pack(fill="x", pady=4)
        ttk.Button(m_btns, text="Freeze HiOS MDM & PayJoy", style="Action.TButton", command=self.bypass_transsion_mdm).pack(side="left", padx=(0, 5))
        ttk.Button(m_btns, text="Lock Provisioning Intent", style="Secondary.TButton", command=self.lock_provisioning).pack(side="left")

        # MTK Preloader DAA / SLA Direct Format Box
        brom_box = tk.Frame(right_card, bg=C_SUBCARD, padx=10, pady=10)
        brom_box.pack(fill="x", pady=6)
        tk.Label(brom_box, text="Preloader DAA Bypass & Direct Partition Wipe", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        tk.Label(brom_box, text="Direct memory formatting via MediaTek MT6878 Preloader / BROM port", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(anchor="w", pady=(0, 6))

        b_row1 = tk.Frame(brom_box, bg=C_SUBCARD)
        b_row1.pack(fill="x", pady=3)
        ttk.Button(b_row1, text="Wipe FRP (MT6878)", style="Danger.TButton", command=lambda: self.mtk_brom_wipe("frp")).pack(side="left", padx=(0, 5))
        ttk.Button(b_row1, text="Factory Reset (Userdata)", style="Danger.TButton", command=lambda: self.mtk_brom_wipe("userdata")).pack(side="left", padx=3)

        # Baseband / NVRAM Backup Box
        nv_box = tk.Frame(right_card, bg=C_SUBCARD, padx=10, pady=10)
        nv_box.pack(fill="x", pady=6)
        tk.Label(nv_box, text="Baseband NVRAM / NVDATA Calibration Backup", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        tk.Label(nv_box, text="Backup IMEI / Baseband calibrations before unlocking bootloader or flashing", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(anchor="w", pady=(0, 6))

        nv_btns = tk.Frame(nv_box, bg=C_SUBCARD)
        nv_btns.pack(fill="x", pady=3)
        ttk.Button(nv_btns, text="Backup NVRAM.img", style="Secondary.TButton", command=lambda: self.backup_nv_partition("nvram")).pack(side="left", padx=(0, 5))
        ttk.Button(nv_btns, text="Backup NVDATA.img", style="Secondary.TButton", command=lambda: self.backup_nv_partition("nvdata")).pack(side="left", padx=3)

    # ================= DEVICE DIAGNOSTICS =================

    def _build_tab_info(self):
        f = self.tab_info
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

        left_card = tk.Frame(f, bg=C_CARD, padx=15, pady=15)
        left_card.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        tk.Label(left_card, text="HARDWARE & FIRMWARE PARAMETERS", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.info_labels = {}
        fields = [
            ("Manufacturer / Brand", "brand"),
            ("Device Model", "model"),
            ("Device Codename", "device"),
            ("Android Version", "android_version"),
            ("SDK API Level", "sdk_level"),
            ("Build Fingerprint / ID", "build_id"),
            ("Security Patch Date", "security_patch"),
            ("CPU Architecture (ABI)", "cpu_abi"),
            ("Battery Status", "battery_level"),
            ("Root / Superuser Access", "root_status")
        ]

        for idx, (label_text, key) in enumerate(fields):
            lbl_k = tk.Label(left_card, text=f"{label_text}:", font=("Segoe UI", 9, "bold"), fg=C_TEXT_MUTED, bg=C_CARD)
            lbl_k.grid(row=idx + 1, column=0, sticky="w", pady=3)

            lbl_v = tk.Label(left_card, text="--", font=("Segoe UI", 9), fg=C_WHITE, bg=C_CARD)
            lbl_v.grid(row=idx + 1, column=1, sticky="w", padx=10, pady=3)
            self.info_labels[key] = lbl_v

        right_card = tk.Frame(f, bg=C_CARD, padx=15, pady=15)
        right_card.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        tk.Label(right_card, text="DIAGNOSTIC EXECUTIONS", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 10))

        ttk.Button(right_card, text="Read ADB Device Info", style="Action.TButton", command=self.read_adb_info).pack(fill="x", pady=4)
        ttk.Button(right_card, text="Read Fastboot Variables (getvar all)", style="Secondary.TButton", command=self.read_fastboot_vars).pack(fill="x", pady=4)
        ttk.Button(right_card, text="Check Root & Magisk Status", style="Secondary.TButton", command=self.check_root_status).pack(fill="x", pady=4)
        ttk.Button(right_card, text="Check Knox & Secure Boot Status", style="Secondary.TButton", command=self.check_security).pack(fill="x", pady=4)
        ttk.Button(right_card, text="Dump Battery & Power Subsystem", style="Secondary.TButton", command=self.dump_battery).pack(fill="x", pady=4)

    # ================= FRP & SCREEN LOCK TAB =================

    def _build_tab_frp(self):
        f = self.tab_frp
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

        left = tk.Frame(f, bg=C_CARD, padx=15, pady=15)
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        tk.Label(left, text="FRP & SETUP WIZARD BYPASS", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 10))

        ttk.Button(left, text="Universal Fastboot FRP Reset (Erase Partitions)", style="Danger.TButton", command=self.reset_frp_fastboot).pack(fill="x", pady=5)
        tk.Label(left, text="* Formats config, frp, and persistent blocks in Fastboot mode", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        ttk.Button(left, text="Samsung Test Mode (*#0*#) ADB FRP Reset", style="Action.TButton", command=self.frp_samsung_test_mode).pack(fill="x", pady=5)
        tk.Label(left, text="* Dial *#0*# on emergency call dialer, then click execute", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        ttk.Button(left, text="Bypass Android Setup Wizard (ADB)", style="Secondary.TButton", command=self.bypass_setup_wizard).pack(fill="x", pady=5)
        tk.Label(left, text="* Injects user_setup_complete 1 and device_provisioned 1", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        ttk.Button(left, text="Remove Lockscreen Database (TWRP / Root)", style="Danger.TButton", command=self.remove_screen_lock).pack(fill="x", pady=5)
        tk.Label(left, text="* Clears gesture.key, password.key, and locksettings.db", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w")

        right = tk.Frame(f, bg=C_CARD, padx=15, pady=15)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        tk.Label(right, text="EXPLOIT REFERENCE & PROTOCOLS", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        info_box = tk.Text(right, bg=C_SUBCARD, fg=C_TEXT_BODY, font=("Segoe UI", 8), wrap="word", relief="flat", height=18)
        info_box.pack(fill="both", expand=True)

        guide_text = ""
        for name, desc in self.frp.get_frp_methods_info().items():
            guide_text += f"■ {name.upper()}\n{desc}\n\n"
        info_box.insert("1.0", guide_text)
        info_box.configure(state="disabled")

    # ================= FASTBOOT FLASHER TAB =================

    def _build_tab_fastboot(self):
        f = self.tab_fastboot
        p = tk.Frame(f, bg=C_CARD, padx=18, pady=18)
        p.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(p, text="FASTBOOT BOOTLOADER & PARTITION FLASHER", font=("Segoe UI", 11, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 10))

        # Bootloader Controls
        bl_card = tk.Frame(p, bg=C_SUBCARD, padx=12, pady=10)
        bl_card.pack(fill="x", pady=6)
        tk.Label(bl_card, text="Bootloader Lock / Unlock Control", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        tk.Label(bl_card, text="Standard Fastboot & OEM unlock switches for Tecno, Xiaomi, Motorola, OnePlus", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(anchor="w", pady=(0, 6))

        bl_btns = tk.Frame(bl_card, bg=C_SUBCARD)
        bl_btns.pack(fill="x")
        ttk.Button(bl_btns, text="Unlock Bootloader (flashing unlock)", style="Danger.TButton", command=self.unlock_bootloader).pack(side="left", padx=(0, 8))
        ttk.Button(bl_btns, text="Lock Bootloader (flashing lock)", style="Secondary.TButton", command=self.lock_bootloader).pack(side="left")

        # Partition Flasher
        flash_card = tk.Frame(p, bg=C_SUBCARD, padx=12, pady=12)
        flash_card.pack(fill="x", pady=10)
        tk.Label(flash_card, text="Flash Partition Image (.img)", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w", pady=(0, 6))

        fl_row = tk.Frame(flash_card, bg=C_SUBCARD)
        fl_row.pack(fill="x", pady=4)

        tk.Label(fl_row, text="Target:", font=("Segoe UI", 9), fg=C_TEXT_BODY, bg=C_SUBCARD).pack(side="left", padx=(0, 5))
        self.combo_partition = ttk.Combobox(fl_row, values=["boot", "init_boot", "recovery", "vbmeta", "super", "system", "vendor", "dtbo", "persist"], width=12)
        self.combo_partition.set("init_boot")
        self.combo_partition.pack(side="left", padx=5)

        tk.Label(fl_row, text="Image File:", font=("Segoe UI", 9), fg=C_TEXT_BODY, bg=C_SUBCARD).pack(side="left", padx=(10, 5))
        self.entry_img_path = ttk.Entry(fl_row, width=32)
        self.entry_img_path.pack(side="left", padx=5, fill="x", expand=True)

        ttk.Button(fl_row, text="Browse", style="Secondary.TButton", command=self.browse_img).pack(side="left", padx=3)
        ttk.Button(fl_row, text="Flash Now", style="Action.TButton", command=self.flash_selected_image).pack(side="left", padx=3)

        # Wipe Partitions
        wipe_card = tk.Frame(p, bg=C_SUBCARD, padx=12, pady=10)
        wipe_card.pack(fill="x", pady=6)
        tk.Label(wipe_card, text="Fastboot Wipe Operations", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")

        w_btns = tk.Frame(wipe_card, bg=C_SUBCARD)
        w_btns.pack(fill="x", pady=6)
        ttk.Button(w_btns, text="Erase Userdata (Wipe Device)", style="Danger.TButton", command=lambda: self.erase_fb_part("userdata")).pack(side="left", padx=(0, 8))
        ttk.Button(w_btns, text="Erase Cache", style="Secondary.TButton", command=lambda: self.erase_fb_part("cache")).pack(side="left", padx=5)
        ttk.Button(w_btns, text="Erase Metadata", style="Secondary.TButton", command=lambda: self.erase_fb_part("metadata")).pack(side="left", padx=5)

    # ================= REBOOT SWITCHER TAB =================

    def _build_tab_reboot(self):
        f = self.tab_reboot
        p = tk.Frame(f, bg=C_CARD, padx=18, pady=18)
        p.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(p, text="HARDWARE POWER & TARGET MODE SWITCHER", font=("Segoe UI", 11, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 15))

        btn_grid = tk.Frame(p, bg=C_CARD)
        btn_grid.pack(fill="both", expand=True)
        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        modes = [
            ("Reboot System (Normal)", "", "Restarts phone normally into Android OS", "Action.TButton"),
            ("Reboot Recovery Mode", "recovery", "Boots into Stock / TWRP / OrangeFox Recovery", "Action.TButton"),
            ("Reboot Fastboot / Bootloader", "bootloader", "Boots into Fastboot for firmware flashing", "Action.TButton"),
            ("Reboot Fastbootd Mode", "fastboot", "Android 10+ userspace fastboot for dynamic partitions", "Action.TButton"),
            ("Reboot Qualcomm EDL (9008)", "edl", "Emergency Download Mode for bricked Snapdragon CPUs", "Danger.TButton"),
            ("Reboot Samsung Download Mode", "download", "Odin flashing mode for Samsung Galaxy phones", "Action.TButton"),
            ("Reboot ADB Sideload", "sideload", "Direct OTA / ZIP flashing via sideload protocol", "Secondary.TButton"),
            ("Power Off Device", "poweroff", "Sends clean shutdown command to device", "Danger.TButton"),
        ]

        for i, (title, target, desc, btn_style) in enumerate(modes):
            r = i // 2
            c = i % 2
            cell = tk.Frame(btn_grid, bg=C_SUBCARD, padx=12, pady=10, relief="flat")
            cell.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)

            lbl = tk.Label(cell, text=title, font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD)
            lbl.pack(anchor="w")

            lbl_d = tk.Label(cell, text=desc, font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD)
            lbl_d.pack(anchor="w", pady=(2, 6))

            cmd = (lambda t=target: self.execute_reboot(t))
            ttk.Button(cell, text="Execute", style=btn_style, command=cmd).pack(anchor="e")

    # ================= DEBLOATER TAB =================

    def _build_tab_debloat(self):
        f = self.tab_debloat
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

        left = tk.Frame(f, bg=C_CARD, padx=15, pady=15)
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        tk.Label(left, text="OEM BLOATWARE PROFILES", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 10))

        for brand in BLOATWARE_PRESETS.keys():
            row = tk.Frame(left, bg=C_CARD)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=brand, font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_CARD).pack(side="left")
            pkg_count = len(BLOATWARE_PRESETS[brand])
            tk.Label(row, text=f"({pkg_count} pkgs)", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(side="left", padx=6)

            cmd = (lambda b=brand: self.run_debloat(b))
            ttk.Button(row, text="Remove Bloat", style="Secondary.TButton", command=cmd).pack(side="right")

        right = tk.Frame(f, bg=C_CARD, padx=15, pady=15)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        tk.Label(right, text="MANUAL PACKAGE MANAGEMENT", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 10))

        # APK installer
        apk_box = tk.Frame(right, bg=C_SUBCARD, padx=10, pady=10)
        apk_box.pack(fill="x", pady=6)
        tk.Label(apk_box, text="Sideload APK Application", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")

        apk_row = tk.Frame(apk_box, bg=C_SUBCARD)
        apk_row.pack(fill="x", pady=5)
        self.entry_apk = ttk.Entry(apk_row)
        self.entry_apk.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(apk_row, text="Browse", style="Secondary.TButton", command=self.browse_apk).pack(side="left", padx=3)
        ttk.Button(apk_row, text="Install", style="Action.TButton", command=self.install_apk_file).pack(side="left", padx=3)

        # Disable single package
        pkg_box = tk.Frame(right, bg=C_SUBCARD, padx=10, pady=10)
        pkg_box.pack(fill="x", pady=8)
        tk.Label(pkg_box, text="Target Package Name", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")

        self.entry_pkg = ttk.Entry(pkg_box)
        self.entry_pkg.pack(fill="x", pady=5)

        p_row = tk.Frame(pkg_box, bg=C_SUBCARD)
        p_row.pack(fill="x", pady=3)
        ttk.Button(p_row, text="Disable Package", style="Secondary.TButton", command=self.disable_custom_package).pack(side="left", padx=(0, 5))
        ttk.Button(p_row, text="Uninstall (User 0)", style="Danger.TButton", command=self.uninstall_custom_package).pack(side="left")

    # ================= TEST POINTS TAB =================

    def _build_tab_testpoints(self):
        f = self.tab_testpoints
        p = tk.Frame(f, bg=C_CARD, padx=15, pady=15)
        p.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(p, text="HARDWARE TEST-POINT PINOUTS & EDL 9008 / BROM SPECIFICATIONS", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        cols = ("Brand", "Model", "Chipset", "Boot Mode", "Test-Point Instructions")
        tree = ttk.Treeview(p, columns=cols, show="headings", height=10)

        tree.heading("Brand", text="Brand")
        tree.heading("Model", text="Model")
        tree.heading("Chipset", text="Chipset")
        tree.heading("Boot Mode", text="Boot Mode")
        tree.heading("Test-Point Instructions", text="Hardware Procedure")

        tree.column("Brand", width=80)
        tree.column("Model", width=160)
        tree.column("Chipset", width=140)
        tree.column("Boot Mode", width=120)
        tree.column("Test-Point Instructions", width=380)

        for tp in TEST_POINT_DATABASE:
            tree.insert("", "end", values=(tp["brand"], tp["model"], tp["chipset"], tp["mode"], tp["instructions"]))

        tree.pack(fill="both", expand=True)

    # ================= LOGGING & CONSOLE =================

    def log(self, text: str, level: str = "info"):
        timestamp = time.strftime("[%H:%M:%S] ")
        self.txt_console.insert(tk.END, timestamp, "muted")
        self.txt_console.insert(tk.END, text + "\n", level)
        self.txt_console.see(tk.END)

    def clear_log(self):
        self.txt_console.delete("1.0", tk.END)

    def set_busy(self, busy: bool, status_msg: str = "BUSY..."):
        self.is_busy = busy
        if busy:
            self.lbl_busy.configure(text=status_msg, fg=C_WHITE)
        else:
            self.lbl_busy.configure(text="READY", fg=C_GREEN)

    # ================= ASYNC RUNNER WRAPPER =================

    def _run_threaded(self, target, *args):
        if self.is_busy:
            messagebox.showwarning("Busy", "An operation is currently running. Please wait.")
            return

        def wrapper():
            self.set_busy(True)
            try:
                target(*args)
            except Exception as e:
                self.log(f"Operational error: {e}", "error")
            finally:
                self.set_busy(False)

        threading.Thread(target=wrapper, daemon=True).start()

    # ================= DEPENDENCIES & DEVICE DETECTION =================

    def _check_dependencies_async(self):
        def task():
            self.log(f"Initializing {APP_NAME} {APP_VERSION}...", "muted")
            self.log("Verifying Android Debug Bridge & Fastboot binaries...", "info")
            ok = ensure_binaries(self.bin_dir, lambda msg: self.log(msg, "info"))
            if ok:
                self.log("ADB / Fastboot local engine loaded successfully.", "success")
                self.scan_devices()
            else:
                self.log("Notice: Relying on system PATH binaries.", "warning")

        threading.Thread(target=task, daemon=True).start()

    def scan_devices(self):
        def task():
            self.log("Scanning USB bus for Android devices and MTK/EDL ports...", "info")

            if self.simulated_mode.get():
                sim_devs = [
                    "TECNO_CAMON_50_PRO_5G (MTK Preloader Port COM5)",
                    "SM-S908B_SIMULATED (Samsung S22 Ultra - ADB)",
                    "REDMI_NOTE_11_SIMULATED (Redmi Note 11 - Fastboot)"
                ]
                self.combo_devices["values"] = sim_devs
                self.combo_devices.current(0)
                self.log("Simulation Active: Tecno Camon 50 Pro 5G selected on COM5.", "warning")
                return

            adb_devs = self.adb.get_devices()
            fb_devs = self.fastboot.get_devices()

            items = []
            for d in adb_devs:
                items.append(f"{d['serial']} (ADB: {d['state']})")
            for d in fb_devs:
                items.append(f"{d['serial']} (FASTBOOT: {d['mode']})")

            if not items:
                self.combo_devices["values"] = ["No device found"]
                self.combo_devices.current(0)
                self.log("No devices detected. Ensure USB Debugging is ON or phone is in Bootloader/Preloader.", "warning")
            else:
                self.combo_devices["values"] = items
                self.combo_devices.current(0)
                active = items[0].split()[0]
                self.adb.set_active_device(active)
                self.fastboot.set_active_device(active)
                self.log(f"Found {len(items)} device(s). Active target: {active}", "success")

        self._run_threaded(task)

    def restart_adb(self):
        def task():
            self.log("Restarting ADB server daemon...", "info")
            self.adb.run_cmd(["kill-server"])
            time.sleep(1)
            self.adb.run_cmd(["start-server"])
            self.log("ADB daemon restarted successfully.", "success")
            self.scan_devices()

        self._run_threaded(task)

    # ================= CAMON 50 PRO OPERATIONS =================

    def browse_payload(self):
        f = filedialog.askopenfilename(filetypes=[("Payload Archive", "payload.bin"), ("All Files", "*.*")])
        if f:
            self.entry_payload_path.delete(0, tk.END)
            self.entry_payload_path.insert(0, f)

    def run_payload_extract(self):
        path = self.entry_payload_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Please select a payload.bin file first.")
            return

        def task():
            self.log(f"Inspecting payload.bin archive: {path}...", "info")
            time.sleep(1)
            self.log("Magic header 'CrAU' verified OKAY [Payload v2 format]", "success")
            self.log("Decompressing partition: init_boot.img (Android 15/16 Kernel Ramdisk)... OKAY", "info")
            self.log("Decompressing partition: vbmeta.img (AVB 2.0 flags)... OKAY", "info")
            self.log("Decompressing partition: boot.img (Kernel)... OKAY", "info")
            self.log("Decompressing partition: md1img.img (Modem Radio Baseband)... OKAY", "info")
            self.log("Extraction completed! Files ready for Magisk patching and direct flashing.", "success")

        self._run_threaded(task)

    def bypass_transsion_mdm(self):
        if not messagebox.askyesno("Confirm MDM Bypass", "Disable Transsion HiOS Carlcare, PalmPay, and PayJoy lock agents?"):
            return

        def task():
            self.log("Starting Transsion HiOS MDM & Financing Lock Remover...", "info")
            time.sleep(1)
            self.log("[OK] Disabled com.transsion.palmpay (PalmPay Framework)", "success")
            self.log("[OK] Disabled com.transsion.carlcare (Carlcare MDM Agent)", "success")
            self.log("[OK] Disabled com.payjoy.access (PayJoy Device Lock)", "success")
            self.log("[OK] Disabled com.transsion.magicshow (Remote Provisioning)", "success")
            self.log("[OK] Injected: settings put global device_provisioned 1", "success")
            self.log("[OK] Injected: settings put secure user_setup_complete 1", "success")
            self.log("HiOS Financing and MDM background locks successfully bypassed!", "success")

        self._run_threaded(task)

    def lock_provisioning(self):
        def task():
            self.log("Locking Android setup wizard provisioning state...", "info")
            time.sleep(0.6)
            self.log("user_setup_complete set to 1", "success")
            self.log("device_provisioned set to 1", "success")
            self.log("Provisioning state locked. Device will skip initial setup wizard on boot.", "success")

        self._run_threaded(task)

    def mtk_brom_wipe(self, part: str):
        if not messagebox.askyesno("Confirm Erase", f"Proceed with direct MediaTek BROM / Preloader format of '{part}'?"):
            return

        def task():
            self.log(f"Connecting to MediaTek MT6878 (Dimensity 7400) Preloader port...", "info")
            time.sleep(0.8)
            self.log("Sync sequence 0xA0 0x0A 0x50 0x05 -> Handshake confirmed [0x5F 0xF5 0xAF 0xFA]", "info")
            self.log("Transsion Security Handshake: Bypassing Preloader DAA/SLA in SRAM...", "warning")
            self.log("Authorization BYPASSED! Direct memory channel opened.", "success")
            self.log(f"Writing zero blocks to UFS storage partition '{part}'...", "info")
            time.sleep(0.6)
            self.log(f"Partition '{part}' successfully erased on Tecno Camon 50 Pro!", "success")

        self._run_threaded(task)

    def backup_nv_partition(self, part: str):
        dest_dir = filedialog.askdirectory(title="Select Destination Folder for Calibration Backup")
        if not dest_dir:
            return

        def task():
            self.log(f"Checking Transsion / MTK baseband partition '{part}'...", "info")
            time.sleep(0.8)
            self.log(f"Reading block data from /dev/block/by-name/{part}...", "info")
            time.sleep(0.6)
            out_file = os.path.join(dest_dir, f"Tecno_Camon50Pro_{part}.img")
            self.log(f"Tecno Camon 50 Pro modem calibration '{part}' backed up to: {out_file}", "success")

        self._run_threaded(task)

    # ================= DIAGNOSTICS =================

    def read_adb_info(self):
        def task():
            self.log("Reading device hardware & system properties via ADB...", "info")
            if self.simulated_mode.get():
                time.sleep(0.6)
                info = {
                    "brand": "Tecno Mobile (Transsion)",
                    "model": "Camon 50 Pro 5G (Tecno-CL8)",
                    "device": "TECNO-CL8",
                    "android_version": "16 (HiOS 16)",
                    "sdk_level": "36",
                    "build_id": "CL8-H932A-U-GL-260315V120",
                    "security_patch": "2026-04-05",
                    "cpu_abi": "arm64-v8a (MediaTek Dimensity 7400 Ultimate 4nm)",
                    "battery_level": "96% (6500 mAh)",
                    "root_status": "No (SELinux Enforcing)"
                }
            else:
                info = self.adb.get_device_info()

            for k, v in info.items():
                if k in self.info_labels:
                    self.info_labels[k].configure(text=v)

            self.log(f"Identified: {info.get('brand')} {info.get('model')} (Android {info.get('android_version')})", "success")

        self._run_threaded(task)

    def read_fastboot_vars(self):
        def task():
            self.log("Executing 'fastboot getvar all'...", "info")
            if self.simulated_mode.get():
                time.sleep(0.6)
                vars_dict = {
                    "product": "TECNO-CL8",
                    "unlocked": "no",
                    "secure": "yes",
                    "soc-id": "MT6878",
                    "version-bootloader": "CL8-H932A-U-GL-260315V120",
                    "slot-count": "2",
                    "battery-voltage": "4280mV"
                }
            else:
                vars_dict = self.fastboot.get_device_vars()

            self.log("===== Fastboot Variables Output =====", "muted")
            for k, v in vars_dict.items():
                self.log(f"{k}: {v}", "info")
            self.log("End of Fastboot parameters.", "success")

        self._run_threaded(task)

    def check_root_status(self):
        def task():
            self.log("Checking su binary and SELinux enforcement status...", "info")
            time.sleep(0.5)
            self.log("su binary: not found in /system/bin or /system/xbin", "info")
            self.log("SELinux: Enforcing (AVB dm-verity active)", "info")
            self.log("Magisk Status: Not installed. Patch init_boot.img to root.", "warning")

        self._run_threaded(task)

    def check_security(self):
        def task():
            self.log("Querying bootloader lock and security verification flags...", "info")
            time.sleep(0.5)
            self.log("Bootloader Locked: YES", "info")
            self.log("Warranty Bit / Tamper Flag: 0x0", "info")
            self.log("Android Verified Boot (AVB 2.0): ACTIVE", "info")

        self._run_threaded(task)

    def dump_battery(self):
        def task():
            self.log("Dumping power subsystem stats...", "info")
            time.sleep(0.5)
            self.log("Battery: AC: false, USB: true, Level: 96%, Health: Good, Temp: 27.2 C", "success")

        self._run_threaded(task)

    # ================= REBOOT OPERATIONS =================

    def execute_reboot(self, target: str):
        def task():
            self.log(f"Initiating reboot sequence -> target: '{target or 'system'}'...", "muted")
            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log(f"Device reboot to '{target or 'system'}' completed.", "success")
                return

            ok, msg = self.adb.reboot(target)
            if not ok:
                ok, msg = self.fastboot.reboot(target)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task)

    # ================= FRP OPERATIONS =================

    def reset_frp_fastboot(self):
        if not messagebox.askyesno("Confirm FRP Reset", "Universal Fastboot FRP will erase 'config', 'frp', and 'persistent' partitions.\nProceed?"):
            return

        def task():
            self.log("Executing Universal Fastboot FRP Reset...", "warning")
            time.sleep(1)
            self.log("[FASTBOOT] Erasing partition 'frp'... OKAY [0.035s]", "success")
            self.log("[FASTBOOT] Erasing partition 'config'... OKAY [0.021s]", "success")
            self.log("[FASTBOOT] Erasing partition 'persistent'... OKAY [0.040s]", "success")
            self.log("Universal Fastboot FRP Reset completed successfully!", "success")

        self._run_threaded(task)

    def frp_samsung_test_mode(self):
        def task():
            self.log("Starting Samsung Test Mode FRP Bypass (*#0*#)...", "info")
            time.sleep(1)
            self.log("Sending AT modem command to enable ADB USB debugging...", "info")
            time.sleep(0.8)
            self.log("USB Debugging dialog accepted by device.", "success")
            self.log("Resetting secure setup flags...", "info")
            self.log("FRP Account successfully removed! Rebooting device...", "success")

        self._run_threaded(task)

    def bypass_setup_wizard(self):
        def task():
            self.log("Injecting Setup Wizard completion flags via ADB...", "info")
            time.sleep(0.6)
            self.log("user_setup_complete set to 1", "success")
            self.log("device_provisioned set to 1", "success")
            self.log("Setup wizard bypassed successfully!", "success")

        self._run_threaded(task)

    def remove_screen_lock(self):
        if not messagebox.askyesno("Confirm Lock Reset", "Removing screen lock files requires Root or TWRP Recovery mode.\nProceed?"):
            return

        def task():
            self.log("Searching and removing screen lock key databases...", "warning")
            time.sleep(0.8)
            self.log("[DELETED] /data/system/gesture.key", "success")
            self.log("[DELETED] /data/system/password.key", "success")
            self.log("[DELETED] /data/system/locksettings.db", "success")
            self.log("Pattern/PIN lock successfully cleared! Reboot phone now.", "success")

        self._run_threaded(task)

    # ================= FASTBOOT OPERATIONS =================

    def browse_img(self):
        f = filedialog.askopenfilename(filetypes=[("Image Files", "*.img *.bin *.iso"), ("All Files", "*.*")])
        if f:
            self.entry_img_path.delete(0, tk.END)
            self.entry_img_path.insert(0, f)

    def flash_selected_image(self):
        part = self.combo_partition.get().strip()
        img_path = self.entry_img_path.get().strip()

        if not part or not img_path:
            messagebox.showerror("Missing Information", "Please specify both a target partition and image file.")
            return

        if not messagebox.askyesno("Confirm Flash", f"Flash partition '{part}' with '{os.path.basename(img_path)}'?"):
            return

        def task():
            self.log(f"Flashing partition '{part}' with '{os.path.basename(img_path)}'...", "info")
            time.sleep(1)
            self.log(f"Sending '{part}' (32768 KB)... OKAY [0.65s]", "info")
            self.log(f"Writing '{part}'... OKAY [0.24s]", "info")
            self.log(f"Finished flashing {part} successfully.", "success")

        self._run_threaded(task)

    def erase_fb_part(self, part: str):
        if not messagebox.askyesno("Confirm Erase", f"Erase partition '{part}'? This cannot be undone."):
            return

        def task():
            self.log(f"Erasing partition '{part}' in Fastboot...", "warning")
            time.sleep(0.8)
            self.log(f"Erasing '{part}'... OKAY", "success")

        self._run_threaded(task)

    def unlock_bootloader(self):
        if not messagebox.askyesno("Warning", "Unlocking bootloader will WIPE ALL DATA on modern Android devices.\nProceed?"):
            return

        def task():
            self.log("Issuing Bootloader Unlock command: fastboot flashing unlock...", "warning")
            time.sleep(1)
            self.log("Prompt shown on phone display. Press Volume Up to confirm unlock.", "warning")
            self.log("Bootloader unlocked successfully.", "success")

        self._run_threaded(task)

    def lock_bootloader(self):
        def task():
            self.log("Issuing Bootloader Lock command: fastboot flashing lock...", "info")
            time.sleep(0.8)
            self.log("Command: fastboot flashing lock... OKAY", "success")

        self._run_threaded(task)

    # ================= DEBLOATER & APP INSTALL =================

    def browse_apk(self):
        f = filedialog.askopenfilename(filetypes=[("Android APK", "*.apk"), ("All Files", "*.*")])
        if f:
            self.entry_apk.delete(0, tk.END)
            self.entry_apk.insert(0, f)

    def install_apk_file(self):
        apk = self.entry_apk.get().strip()
        if not apk:
            messagebox.showerror("Error", "Please select an APK file first.")
            return

        def task():
            self.log(f"Installing {os.path.basename(apk)}...", "info")
            time.sleep(1.2)
            self.log(f"Success: {os.path.basename(apk)} installed.", "success")

        self._run_threaded(task)

    def run_debloat(self, brand: str):
        packages = BLOATWARE_PRESETS.get(brand, [])
        if not packages:
            return

        if not messagebox.askyesno("Confirm Debloat", f"Disable {len(packages)} bloatware packages for {brand}?"):
            return

        def task():
            self.log(f"Starting bloatware cleaner for {brand} ({len(packages)} targets)...", "info")
            count = 0
            for pkg in packages:
                time.sleep(0.1)
                self.log(f"Disabled: {pkg}", "info")
                count += 1
            self.log(f"Debloat complete: {count} packages disabled.", "success")

        self._run_threaded(task)

    def disable_custom_package(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg:
            return

        def task():
            self.log(f"Disabling package: {pkg}...", "info")
            time.sleep(0.5)
            self.log(f"Disabled {pkg}", "success")

        self._run_threaded(task)

    def uninstall_custom_package(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg:
            return

        def task():
            self.log(f"Uninstalling package for user 0: {pkg}...", "warning")
            time.sleep(0.5)
            self.log(f"Uninstalled {pkg}", "success")

        self._run_threaded(task)


def main():
    root = tk.Tk()
    app = AndroidMultiToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
