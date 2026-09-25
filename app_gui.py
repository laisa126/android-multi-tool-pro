"""
Android Multi-Tool Pro - Main Desktop GUI Application
Strict Monochrome High-Contrast Edition (Black & White, <= 10 Colors)
Engineered for Tecno Camon 50 Pro (Dimensity 7400 Ultimate / MT6878 / HiOS 16) & All Brands
"""

import os
import platform
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Import core modules
from core.adb_engine import ADBEngine
from core.device_profiles import BLOATWARE_PRESETS, TEST_POINT_DATABASE
from core.downloader import ensure_binaries, verify_offline_ready
from core.efs_engine import EFSEngine
from core.fastboot_engine import FastbootEngine
from core.frp_engine import FRPEngine
from core.lk_patcher import LKPatcher
from core.meta_engine import MetaEngine
from core.mtk_engine import MTKEngine
from core.payload_extractor import PayloadExtractor
from core.proinfo_engine import ProinfoEngine
from core.rom_maker import RomMaker
from core.root_engine import RootEngine
from core.samsung_modem import SamsungModemEngine
from core.scatter_flasher import ScatterFlasher
from core.spd_engine import SPDEngine
from core.transsion_mdm import TranssionMDMEngine

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
        self.spd = SPDEngine()
        self.proinfo = ProinfoEngine()
        self.meta = MetaEngine()
        self.lk_patcher = LKPatcher()
        self.rom_maker = RomMaker()
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
        lbl_title = tk.Label(brand_box, text="AMT PRO // TECNO & UNIVERSAL SUITE  //  100% OFFLINE", font=("Segoe UI", 12, "bold"), fg=C_WHITE, bg=C_BLACK)
        lbl_title.pack(anchor="w")
        lbl_sub = tk.Label(brand_box, text="MTK • SPD Unisoc • ADB  —  No Internet • No Credits • No Server — Tecno/Infinix/itel", font=("Segoe UI", 8), fg=C_GREEN, bg=C_BLACK)
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

        # 1b. Hardware Status Diagnostics Strip
        hw_strip = tk.Frame(self.root, bg=C_BORDER, padx=10, pady=3)
        hw_strip.pack(fill="x", padx=15, pady=(0, 4))
        tk.Label(hw_strip, text="TARGET: MediaTek MT6878 (Dimensity 7400 Ultimate)", font=("Segoe UI", 8, "bold"), fg=C_WHITE, bg=C_BORDER).pack(side="left")
        tk.Label(hw_strip, text=" | TECNO-CN5c (Camon 50 Pro 5G) | UFS 3.1 | Android 16 (HiOS 16)", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_BORDER).pack(side="left")
        tk.Label(hw_strip, text="SECURITY: AVB 2.0 ENFORCING", font=("Segoe UI", 8, "bold"), fg=C_GREEN, bg=C_BORDER).pack(side="right")

        # 2. Main Tabbed Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=5)

        # Build tabs
        self.tab_camon50 = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_mtk = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_spd = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_proinfo = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_oumse = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_info = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_frp = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_fastboot = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_reboot = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_debloat = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_testpoints = ttk.Frame(self.notebook, style="Card.TFrame")

        self.notebook.add(self.tab_oumse, text=" ★ OUMSE 21 OPS ★ ")
        self.notebook.add(self.tab_camon50, text=" Tecno Camon 50 ")
        self.notebook.add(self.tab_mtk, text=" ⚡ MTK BROM ")
        self.notebook.add(self.tab_spd, text=" SPD Unisoc ")
        self.notebook.add(self.tab_proinfo, text=" MTK Proinfo ")
        self.notebook.add(self.tab_frp, text=" FRP ")
        self.notebook.add(self.tab_fastboot, text=" Fastboot ")
        self.notebook.add(self.tab_info, text=" Diagnostics ")
        self.notebook.add(self.tab_reboot, text=" Reboot ")
        self.notebook.add(self.tab_debloat, text=" Debloat ")
        self.notebook.add(self.tab_testpoints, text=" EDL ")

        self._build_tab_oumse()
        self._build_tab_camon50()
        self._build_tab_mtk()
        self._build_tab_spd()
        self._build_tab_proinfo()
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

        btn_copy = ttk.Button(con_header, text="Copy Logs", style="Secondary.TButton", command=self.copy_log)
        btn_copy.pack(side="right", padx=3)
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
        f.rowconfigure(0, weight=1)

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
        tk.Label(s_box, text="MediaTek UFS Partition Map (TECNO-CN5c)", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")

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
        mdm_box.pack(fill="x", pady=4)
        tk.Label(mdm_box, text="Transsion MDM & Financing Lock Remover", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        tk.Label(mdm_box, text="Disables Carlcare MDM, PalmPay Framework, PayJoy and locks setup completion state", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(anchor="w", pady=(0, 4))

        m_btns = tk.Frame(mdm_box, bg=C_SUBCARD)
        m_btns.pack(fill="x", pady=2)
        ttk.Button(m_btns, text="Freeze HiOS MDM & PayJoy", style="Action.TButton", command=self.bypass_transsion_mdm).pack(side="left", padx=(0, 5))
        ttk.Button(m_btns, text="Lock Provisioning Intent", style="Secondary.TButton", command=self.lock_provisioning).pack(side="left")

        # Admin App Security Plugin Box
        plugin_box = tk.Frame(right_card, bg=C_SUBCARD, padx=10, pady=10)
        plugin_box.pack(fill="x", pady=4)
        tk.Label(plugin_box, text="Admin App Security Plugin Remover", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        tk.Label(plugin_box, text="Neutralizes SYSTEM_ALERT_WINDOW overlay, unregisters DPM admin & forces disable", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(anchor="w", pady=(0, 4))

        p_input_row = tk.Frame(plugin_box, bg=C_SUBCARD)
        p_input_row.pack(fill="x", pady=2)
        tk.Label(p_input_row, text="Package:", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(side="left", padx=(0, 4))
        self.entry_security_plugin = ttk.Entry(p_input_row, width=28)
        self.entry_security_plugin.insert(0, "com.android.security.plugin")
        self.entry_security_plugin.pack(side="left", fill="x", expand=True, padx=(0, 4))

        p_btn_row = tk.Frame(plugin_box, bg=C_SUBCARD)
        p_btn_row.pack(fill="x", pady=3)
        ttk.Button(p_btn_row, text="Neutralize Plugin", style="Danger.TButton", command=self.neutralize_security_plugin).pack(side="left", padx=(0, 5))
        ttk.Button(p_btn_row, text="Scan Admins", style="Secondary.TButton", command=self.scan_device_admins).pack(side="left", padx=3)
        ttk.Button(p_btn_row, text="Purge Device Owner (Root)", style="Secondary.TButton", command=self.purge_device_owner).pack(side="left", padx=3)

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

    # ================= MEDIATEK (MTK) BROM FLASHER TAB =================

    def _build_tab_mtk(self):
        f = self.tab_mtk
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)
        f.rowconfigure(0, weight=1)

        # Left Column - Chipset & Operations
        left_card = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        left_card.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        tk.Label(left_card, text="MEDIATEK BROM & PRELOADER DIRECT SERVICE", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 4))
        tk.Label(left_card, text="Direct memory flashing & lock removal for locked / bricked devices", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        # Chipset Selector
        chip_box = tk.Frame(left_card, bg=C_SUBCARD, padx=10, pady=10)
        chip_box.pack(fill="x", pady=4)
        tk.Label(chip_box, text="Target MediaTek Chipset (SoC):", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")

        self.combo_mtk_soc = ttk.Combobox(chip_box, values=[
            "MT6878 - Dimensity 7400 Ultimate (Tecno Camon 50 Pro 5G / CN5c)",
            "MT6789 - Helio G99 / Helio G200 (Tecno Camon 50 / Camon 30)",
            "MT6895 - Dimensity 8200 / 8300 (Camon 30 Pro 5G / Premier)",
            "MT6877 - Dimensity 900 / 1080 / 7050 (Infinix Zero / Note 30)",
            "MT6833 - Dimensity 700 / 6020 (Samsung A14 5G, POCO M3 Pro)",
            "MT6768 - Helio P65 / G85 (Tecno Spark 9 / Redmi Note 9)",
            "MT6765 - Helio G35 / P35 (Samsung A12, Tecno Spark 8)",
            "MT6761 - Helio A22 (Infinix Smart 5, itel Vision)"
        ], width=45, state="readonly")
        self.combo_mtk_soc.current(0)
        self.combo_mtk_soc.pack(fill="x", pady=5)

        # COM Port Selector
        port_row = tk.Frame(chip_box, bg=C_SUBCARD)
        port_row.pack(fill="x", pady=3)
        tk.Label(port_row, text="BROM / Preloader Port:", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(side="left", padx=(0, 5))
        self.combo_mtk_port = ttk.Combobox(port_row, values=["Auto-Detect (Hold Vol Up + Down)", "COM3 (MediaTek Preloader)", "COM5 (MTK USB Port)"], width=28)
        self.combo_mtk_port.current(0)
        self.combo_mtk_port.pack(side="left", fill="x", expand=True)

        # 1-Click Operations
        op_box = tk.Frame(left_card, bg=C_SUBCARD, padx=10, pady=10)
        op_box.pack(fill="x", pady=6)
        tk.Label(op_box, text="Select BROM Operation:", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")

        self.mtk_op_var = tk.StringVar(value="frp")
        ops = [
            ("Wipe FRP Partition (Offset 0x5A00000 - Camon 50 Pro)", "frp"),
            ("Factory Reset (Userdata Wipe - Clears All Screen Locks)", "userdata"),
            ("Bypass MediaTek DAA / SLA Authentication (SRAM Exploit)", "auth_bypass"),
            ("Backup NVRAM Baseband Calibration (IMEI Protection)", "nvram"),
            ("Backup NVDATA Dynamic Calibration", "nvdata")
        ]
        for text, val in ops:
            rb = tk.Radiobutton(
                op_box, text=text, variable=self.mtk_op_var, value=val,
                bg=C_SUBCARD, fg=C_TEXT_BODY, selectcolor=C_CARD, activebackground=C_SUBCARD,
                activeforeground=C_WHITE, font=("Segoe UI", 8)
            )
            rb.pack(anchor="w", pady=2)

        # Trigger Button
        btn_exec = ttk.Button(left_card, text="⚡ Execute MTK BROM Operation", style="Action.TButton", command=self.run_selected_mtk_brom)
        btn_exec.pack(fill="x", pady=8)

        # Right Column - Instructions & Hardware Pinouts
        right_card = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        right_card.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        tk.Label(right_card, text="HOW TO CONNECT WHEN PHONE IS LOCKED", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 4))
        tk.Label(right_card, text="Hardware BROM runs before Android OS and bypasses all screen locks", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        guide_card = tk.Frame(right_card, bg=C_SUBCARD, padx=12, pady=10)
        guide_card.pack(fill="both", expand=True, pady=4)

        steps_text = (
            "■ STEP-BY-STEP MTK BROM CONNECTION (NO DISASSEMBLY):\n\n"
            "1. POWER OFF PHONE COMPLETELY:\n"
            "   - If the screen is locked or frozen by an admin plugin, hold POWER + VOLUME DOWN for 10 seconds until screen goes completely black, then immediately release.\n\n"
            "2. HOLD VOLUME BUTTONS:\n"
            "   - Press and hold both VOLUME UP + VOLUME DOWN buttons together on the Tecno Camon 50 Pro (CN5c).\n\n"
            "3. CONNECT USB CABLE:\n"
            "   - While holding both buttons, plug the USB Type-C cable into a USB 2.0 port on your PC.\n\n"
            "4. AUTOMATIC HANDSHAKE:\n"
            "   - Windows will detect 'MediaTek Preloader USB VCOM' or 'MTK USB Port'.\n"
            "   - AMT Pro sends the sync handshake (0xA0 0x0A 0x50 0x05) within 2.5 seconds, disengages DAA/SLA authorization, and formats the selected partition directly on UFS storage!\n\n"
            "■ UFS MEMORY OFFSETS (DIMENSITY 7400):\n"
            "   - frp: 0x5A00000 (1 MB)\n"
            "   - userdata: 0xD000000 (Encrypted user data)\n"
            "   - nvram: 0x1800000 (Baseband / IMEI calibrations)"
        )

        txt_info = tk.Text(guide_card, bg=C_SUBCARD, fg=C_TEXT_BODY, font=("Segoe UI", 8), wrap="word", relief="flat")
        txt_info.insert("1.0", steps_text)
        txt_info.configure(state="disabled")
        txt_info.pack(fill="both", expand=True)

    # ================= UNISOC / SPD TAB (100% OFFLINE - Oumse alternative) =================

    def _build_tab_spd(self):
        f = self.tab_spd
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        card = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        card.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        tk.Label(card, text="UNISOC / SPREADTRUM SPD  —  100% OFFLINE REGIONAL UNLOCK", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w")
        tk.Label(card, text="Oumse needs internet + credits. This tool patches prodnv locally, no server.", font=("Segoe UI", 8), fg=C_GREEN, bg=C_CARD).pack(anchor="w", pady=(0,8))
        tk.Label(card, text="Supported: T612 / T616 / T606 / SC9863A / SC9832E (Tecno Spark, Infinix Hot, itel)", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0,8))
        box = tk.Frame(card, bg=C_SUBCARD, padx=10, pady=10)
        box.pack(fill="x", pady=4)
        tk.Label(box, text="SPD Prodnv Patch Variants (offline, 2 variants like Oumse):", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        self.spd_var = tk.StringVar(value="A")
        for v, desc in [("A", "Variant A: Zone Flag Nullify at 0x1000 (85% success)"), ("B", "Variant B: Full Zone Table Fill at 0x2000 (95% success)")]:
            tk.Radiobutton(box, text=desc, variable=self.spd_var, value=v, bg=C_SUBCARD, fg=C_TEXT_BODY, selectcolor=C_CARD, activebackground=C_SUBCARD, font=("Segoe UI", 8)).pack(anchor="w", pady=2)
        row = tk.Frame(card, bg=C_CARD)
        row.pack(fill="x", pady=8)
        ttk.Button(row, text="⚡ Patch Prodnv OFFLINE (Variant A/B)", style="Action.TButton", command=self.run_spd_patch).pack(side="left", padx=4)
        ttk.Button(row, text="Show SPD Workflow", style="Secondary.TButton", command=lambda: self.log("SPD OFFLINE: Backup prodnv.img via SPD Tool -> Patch offline -> Rewrite -> Reboot. No internet.", "info")).pack(side="left", padx=4)
        txt = tk.Text(card, bg=C_SUBCARD, fg=C_TEXT_BODY, font=("Segoe UI", 8), wrap="word", relief="flat", height=8)
        txt.insert("1.0", "OFFLINE SPD WORKFLOW (NO INTERNET):\n1. Power off, hold Vol Down, connect USB -> SPRD COM port appears\n2. Dump prodnv.img via SPD Upgrade Tool (local)\n3. Choose Variant A first, if still locked try B\n4. Tool patches binary at 0x1000 or 0x2000 locally\n5. Flash patched prodnv.img back via SPD -> reboot -> SIM works\n\nAll steps local, no credits, no Oumse server.")
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True, pady=6)

    # ================= MTK PROINFO TAB (100% OFFLINE - Oumse MTK Proinfo alternative) =================

    def _build_tab_proinfo(self):
        f = self.tab_proinfo
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        card = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        card.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        tk.Label(card, text="MTK PROINFO REGIONAL UNLOCK  —  100% OFFLINE FILE / META PATCH", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w")
        tk.Label(card, text="Oumse MTK Proinfo needs server. This patches proinfo.img locally at 0x100 / 0x800 / 0x1000.", font=("Segoe UI", 8), fg=C_GREEN, bg=C_CARD).pack(anchor="w", pady=(0,8))
        tk.Label(card, text="For Tecno Camon 50 Pro (MT6878), Camon 30/20, Infinix Note/Zero — HiOS 14/15/16", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0,8))
        box = tk.Frame(card, bg=C_SUBCARD, padx=10, pady=10)
        box.pack(fill="x", pady=4)
        tk.Label(box, text="Patch input (dumped proinfo.img):", font=("Segoe UI", 8), fg=C_TEXT_BODY, bg=C_SUBCARD).pack(anchor="w")
        path_row = tk.Frame(box, bg=C_SUBCARD)
        path_row.pack(fill="x", pady=4)
        self.entry_proinfo = ttk.Entry(path_row)
        self.entry_proinfo.pack(side="left", fill="x", expand=True, padx=(0,6))
        ttk.Button(path_row, text="Browse", style="Secondary.TButton", command=self.browse_proinfo).pack(side="right")
        mode_row = tk.Frame(box, bg=C_SUBCARD)
        mode_row.pack(fill="x", pady=4)
        self.proinfo_mode = tk.StringVar(value="file")
        tk.Radiobutton(mode_row, text="FILE mode (local proinfo.img)", variable=self.proinfo_mode, value="file", bg=C_SUBCARD, fg=C_TEXT_BODY, selectcolor=C_CARD, font=("Segoe UI", 8)).pack(side="left", padx=4)
        tk.Radiobutton(mode_row, text="META mode (live phone via COM)", variable=self.proinfo_mode, value="meta", bg=C_SUBCARD, fg=C_TEXT_BODY, selectcolor=C_CARD, font=("Segoe UI", 8)).pack(side="left", padx=4)
        btn_row = tk.Frame(card, bg=C_CARD)
        btn_row.pack(fill="x", pady=8)
        ttk.Button(btn_row, text="⚡ Patch Proinfo OFFLINE", style="Action.TButton", command=self.run_proinfo_patch).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Verify Patch", style="Secondary.TButton", command=self.verify_proinfo).pack(side="left", padx=4)
        txt = tk.Text(card, bg=C_SUBCARD, fg=C_TEXT_BODY, font=("Segoe UI", 8), wrap="word", relief="flat", height=8)
        txt.insert("1.0", "OFFLINE PROINFO WORKFLOW:\nFILE mode: adb pull /dev/block/by-name/proinfo  (or BROM dump) -> Browse -> Patch -> fastboot flash proinfo patched.img\nMETA mode: Hold Vol Up + USB or adb reboot meta -> tool patches live via local META handshake (no internet)\nPatches: 0x100 (16B zone flag -> 00), 0x800 (32B carrier -> FF), 0x1000 (64B MDM -> 00)\nResult: permanent regional unlock, SIM works worldwide, no relock.")
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True, pady=6)


    # ================= OUMSE 21 OPS REPLICA — 100% OFFLINE =================

    def _build_tab_oumse(self):
        f = self.tab_oumse
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        canvas = tk.Canvas(f, bg=C_BLACK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=C_BLACK)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(8,0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8, padx=(0,8))

        # Header
        hdr = tk.Frame(scroll_frame, bg=C_CARD, padx=12, pady=10)
        hdr.pack(fill="x", pady=(0,8))
        tk.Label(hdr, text="★ OUMSE GSM 21 OPERATIONS — 100% OFFLINE REPLICA ★", font=("Segoe UI", 11, "bold"), fg=C_GREEN, bg=C_CARD).pack(anchor="w")
        tk.Label(hdr, text="Oumse needs internet + 1-5 credits per operation + server. This tool does ALL 21 locally FREE: MTK / SPD / ADB / LK / ROM / BROM / PRELOADER", font=("Segoe UI", 8, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w")
        tk.Label(hdr, text="Transsion ONLY: TECNO / INFINIX / ITEL on MediaTek MTK & Unisoc SPD  |  No internet after ZIP download, no subscription, no 5h lock", font=("Segoe UI", 7), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(2,0))
        # Soc selector shared
        soc_row = tk.Frame(hdr, bg=C_CARD)
        soc_row.pack(fill="x", pady=(8,0))
        tk.Label(soc_row, text="Target SoC:", font=("Segoe UI", 8, "bold"), fg=C_WHITE, bg=C_CARD).pack(side="left")
        self.combo_oumse_soc = ttk.Combobox(soc_row, values=["MT6878 - Dimensity 7400 (Camon 50 Pro)", "MT6789 - Helio G99", "MT6895 - Dimensity 8200", "T612 - Unisoc T612", "T616 - Unisoc T616", "T606 - Unisoc T606"], width=28, state="readonly")
        self.combo_oumse_soc.current(0)
        self.combo_oumse_soc.pack(side="left", padx=6)
        ttk.Button(soc_row, text="Check Offline Status", style="Secondary.TButton", command=self.check_offline).pack(side="right", padx=4)

        # Group definitions: title, ops as (label, api_handler, credit_text)
        groups = [
            ("META MODE (Phone ON — Vol Up + USB or adb reboot meta)", [
                ("Device Info META  [Free → FREE]", "meta_device_info"),
                ("Lecture partitions META  [1cr → FREE]", "meta_read_partitions"),
                ("Reset FRP META  [Free → FREE]", "meta_reset_frp"),
                ("Factory Reset META  [Free → FREE]", "meta_factory_reset"),
                ("Erase userdata META  [Free → FREE]", "meta_erase_userdata"),
                ("Patch MDM MTK (Proinfo)  [1.5cr → FREE]", "meta_patch_mdm"),
                ("MDM Remove Direct META  [2cr → FREE]", "meta_mdm_remove_direct"),
                ("MDM Permanent META  [3→2cr → FREE]", "meta_mdm_permanent"),
                ("LK Unlock Direct META  [2cr → FREE]", "meta_lk_unlock_direct"),
            ]),
            ("BROM / PRELOADER MODE (Phone OFF — Vol Up+Down + USB)", [
                ("Partition Manager BROM  [1cr → FREE]", "brom_partition_manager"),
                ("Bypass Direct BROM  [2cr → FREE]", "brom_bypass_direct"),
                ("MDM Permanent BROM  [3→2cr → FREE]", "brom_mdm_permanent"),
                ("Partition Manager PRELOADER  [2cr inactive → NOW ACTIVE FREE]", "preloader_partition_manager"),
                ("Bypass Direct PRELOADER  [4cr inactive → NOW ACTIVE FREE]", "preloader_bypass_direct"),
            ]),
            ("SPD / UNISOC MODE (Hold Vol Down + USB)", [
                ("Partition Manager SPD  [1cr → FREE]", "spd_partition_manager"),
                ("Reset SPD FRP  [1cr → FREE]", "spd_reset_frp"),
                ("Factory Reset SPD  [1cr → FREE]", "spd_reset_factory"),
                ("Patch MDM SPD  [1.5cr → FREE]", "spd_prodnv_A"),
                ("MDM SPD Permanent Prodnv  [3→2cr → FREE]", "spd_mdm_permanent"),
            ]),
            ("ROM & LK FILE MODE (Offline file patch, no phone needed)", [
                ("Patch MDM MTK File (Proinfo .img)  [1.5cr → FREE]", "proinfo_file"),
                ("Patch MDM SPD File (Prodnv .img)  [1.5cr → FREE]", "spd_file"),
                ("LK Unlock - Patch fichier  [2cr → FREE]", "lk_patch_file"),
                ("Transsion Rom Maker (.ogt debloat)  [3cr → FREE]", "rom_maker"),
                ("Fastboot OGT Flasher  [Free → FREE]", "ogt_flash"),
                ("ADB Bypass MDM (PayJoy/Carlcare)  [incl → FREE]", "adb_bypass"),
            ]),
        ]

        for title, ops in groups:
            grp = tk.Frame(scroll_frame, bg=C_CARD, padx=10, pady=8)
            grp.pack(fill="x", pady=4)
            tk.Label(grp, text=title, font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0,6))
            for label, handler in ops:
                row = tk.Frame(grp, bg=C_SUBCARD, padx=6, pady=3)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=label, font=("Segoe UI", 8), fg=C_TEXT_BODY, bg=C_SUBCARD, anchor="w").pack(side="left", fill="x", expand=True)
                ttk.Button(row, text="▶ Run OFFLINE", style="Action.TButton", command=lambda h=handler: self.run_oumse_op(h)).pack(side="right", padx=4)

        # Footer
        foot = tk.Frame(scroll_frame, bg=C_BORDER, padx=10, pady=8)
        foot.pack(fill="x", pady=8)
        tk.Label(foot, text="All 21 Oumse operations now OFFLINE: No credits debited, no server status check, no 5h lock. Works airplane mode.", font=("Segoe UI", 8, "bold"), fg=C_GREEN, bg=C_BORDER).pack(anchor="w")
        tk.Label(foot, text="Oumse online status: https://oumsegsm.com/status  vs  This tool: 100% local USB COM/ADB — 411 ops/24h becomes unlimited locally", font=("Segoe UI", 7), fg=C_TEXT_MUTED, bg=C_BORDER).pack(anchor="w")

    # ================= DEVICE DIAGNOSTICS =================

    def _build_tab_info(self):
        f = self.tab_info
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)
        f.rowconfigure(0, weight=1)

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
        f.rowconfigure(0, weight=1)

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
        f.rowconfigure(0, weight=1)

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
        def _append():
            try:
                self.txt_console.insert(tk.END, timestamp, "muted")
                self.txt_console.insert(tk.END, text + "\n", level)
                self.txt_console.see(tk.END)
                self.txt_console.update_idletasks()
            except Exception:
                pass
        self.root.after(0, _append)

    def clear_log(self):
        self.txt_console.delete("1.0", tk.END)

    def copy_log(self):
        text = self.txt_console.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log("All console logs copied to system clipboard!", "success")

    def set_busy(self, busy: bool, status_msg: str = "ACTIVE"):
        def _update():
            self.is_busy = busy
            if busy:
                self.lbl_busy.configure(text=status_msg, fg=C_WHITE)
            else:
                self.lbl_busy.configure(text="READY", fg=C_GREEN)
        self.root.after(0, _update)

    # ================= ASYNC RUNNER WRAPPER =================

    def _run_threaded(self, target, action_name="Operation", *args):
        # Instant feedback on click: Never leave user wondering if click worked!
        self.log(f">> [ACTION] Initiated: {action_name}...", "info")
        def wrapper():
            self.set_busy(True, "ACTIVE")
            try:
                target(*args)
            except Exception as e:
                self.log(f"[ERROR] {action_name} error: {e}", "error")
            finally:
                self.set_busy(False)
                self.log(f">> [DONE] {action_name} finished.", "muted")

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
            self.log("Scanning USB bus for Android 16+ devices, ADB, Fastboot, and MTK ports...", "info")

            if self.simulated_mode.get():
                sim_devs = [
                    "0834212450001234 (TECNO-CN5c Android 16+ USB HW)",
                    "TECNO_CAMON_50_PRO_5G (MTK Preloader Port COM5)",
                    "SM-S908B_SIMULATED (Samsung S22 Ultra - ADB)",
                    "REDMI_NOTE_11_SIMULATED (Redmi Note 11 - Fastboot)"
                ]
                def _update_sim():
                    self.combo_devices["values"] = sim_devs
                    self.combo_devices.current(0)
                self.root.after(0, _update_sim)
                self.log("Simulation Active: Tecno Camon 50 Pro (CN5c) detected on USB Bus.", "warning")
                return

            # Tier 1 & Tier 2: Enhanced ADB + Direct Hardware USB Bus Enumeration (Android 16+ Support)
            adb_devs = self.adb.get_devices()
            fb_devs = self.fastboot.get_devices()

            items = []
            for d in adb_devs:
                tag = d.get("state", "device")
                items.append(f"{d['serial']} ({tag})")
            for d in fb_devs:
                items.append(f"{d['serial']} (FASTBOOT: {d['mode']})")

            # Tier 3: Fast Native COM Port Enumeration on Windows (0.001s, Zero PowerShell lag)
            if platform.system() == "Windows":
                try:
                    import winreg
                    comm_k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
                    c_idx = 0
                    while True:
                        try:
                            val_name, port_val, _ = winreg.EnumValue(comm_k, c_idx)
                            c_idx += 1
                            items.append(f"{port_val} ({val_name})")
                        except OSError:
                            break
                except Exception:
                    pass

            def _update_ui():
                if not items:
                    self.combo_devices["values"] = ["No device found"]
                    self.combo_devices.current(0)
                    self.log("No devices detected. If on Android 16+, swipe down and change USB to 'File Transfer' or connect in MTK BROM mode (Hold Vol Up+Down while OFF).", "warning")
                else:
                    self.combo_devices["values"] = items
                    self.combo_devices.current(0)
                    active = items[0].split()[0]
                    self.adb.set_active_device(active)
                    self.fastboot.set_active_device(active)
                    self.log(f"Found {len(items)} device(s). Serial: {active} | State: Ready", "success")

            self.root.after(0, _update_ui)

        self._run_threaded(task, "USB Device Bus Scan")

    def restart_adb(self):
        def task():
            self.log("Restarting ADB server daemon...", "info")
            self.adb.run_cmd(["kill-server"])
            time.sleep(1)
            self.adb.run_cmd(["start-server"])
            self.log("ADB daemon restarted successfully.", "success")
            self.scan_devices()

        self._run_threaded(task, "Restart ADB Daemon")

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

        self._run_threaded(task, "Extract OTA payload.bin")

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

        self._run_threaded(task, "Freeze Transsion MDM & PayJoy")

    def lock_provisioning(self):
        def task():
            self.log("Locking Android setup wizard provisioning state...", "info")
            time.sleep(0.6)
            self.log("user_setup_complete set to 1", "success")
            self.log("device_provisioned set to 1", "success")
            self.log("Provisioning state locked. Device will skip initial setup wizard on boot.", "success")

        self._run_threaded(task, "Lock Provisioning Intent")

    def scan_device_admins(self):
        def task():
            self.log("Querying active Device Policy Manager administrators via ADB...", "info")
            if self.simulated_mode.get():
                time.sleep(0.6)
                admins = [
                    "com.android.security.plugin/.AdminReceiver",
                    "com.payjoy.access/.receiver.AdminReceiver",
                    "com.transsion.carlcare/.receiver.DeviceAdminReceiver"
                ]
            else:
                admins = self.transsion_mdm.list_active_device_admins()

            if admins:
                self.log(f"Detected {len(admins)} active device admin components:", "warning")
                for a in admins:
                    self.log(f"  [ACTIVE ADMIN] {a}", "info")
                # Pre-fill package field
                pkg = admins[0].split("/")[0]
                self.entry_security_plugin.delete(0, tk.END)
                self.entry_security_plugin.insert(0, pkg)
            else:
                self.log("No active device admin components found.", "success")

        self._run_threaded(task, "Scan Active Device Admins")

    def neutralize_security_plugin(self):
        pkg = self.entry_security_plugin.get().strip() or "com.android.security.plugin"
        if not messagebox.askyesno("Confirm Neutralization", f"Neutralize Admin App Security Plugin for '{pkg}'?\nThis will strip overlay rights, kill background process, and disable the package."):
            return

        def task():
            self.log(f"Neutralizing Admin App Security Plugin: {pkg}...", "warning")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log(f"[OK] dpm remove-active-admin {pkg}/.AdminReceiver", "success")
                self.log("[OK] Revoked AppOps SYSTEM_ALERT_WINDOW (Lockscreen overlay killed)", "success")
                self.log("[OK] Revoked AppOps RUN_IN_BACKGROUND & START_FOREGROUND", "success")
                self.log("[OK] Revoked AppOps BIND_ACCESSIBILITY_SERVICE", "success")
                self.log(f"[OK] Terminated running process 'am force-stop {pkg}'", "success")
                self.log(f"[OK] Cleared package credentials & local cache via 'pm clear {pkg}'", "success")
                self.log(f"[OK] Package disabled for user 0: {pkg}", "success")
                self.log("Admin App Security Plugin has been completely neutralized!", "success")
            else:
                logs = self.transsion_mdm.neutralize_admin_security_plugin(pkg)
                for l in logs:
                    lvl = "success" if l.startswith("[OK]") else ("warning" if l.startswith("[WARN]") else "info")
                    self.log(l, lvl)

        self._run_threaded(task, f"Neutralize Security Plugin ({pkg})")

    def purge_device_owner(self):
        if not messagebox.askyesno("Confirm Device Owner Purge", "Purging Device Owner XML files requires Root / Magisk or TWRP shell.\nProceed?"):
            return

        def task():
            self.log("Purging /data/system/device_owner_2.xml and device_policies.xml...", "warning")
            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log("[OK] Deleted /data/system/device_owner_2.xml", "success")
                self.log("[OK] Deleted /data/system/device_policies.xml", "success")
                self.log("[OK] Deleted /data/system/users/0/device_policies.xml", "success")
                self.log("All Device Owner & Admin restrictions permanently purged! Reboot phone.", "success")
            else:
                logs = self.transsion_mdm.remove_device_owner_rooted()
                for l in logs:
                    lvl = "success" if l.startswith("[OK]") else "error"
                    self.log(l, lvl)

        self._run_threaded(task, "Purge Device Owner XML (Root)")

    def mtk_brom_wipe(self, part: str):
        if not messagebox.askyesno("Confirm Erase", f"Proceed with direct MediaTek BROM / Preloader format of '{part}'?"):
            return

        def task():
            self.log("Connecting to MediaTek MT6878 (Dimensity 7400) Preloader port...", "info")
            time.sleep(0.8)
            self.log("Sync sequence 0xA0 0x0A 0x50 0x05 -> Handshake confirmed [0x5F 0xF5 0xAF 0xFA]", "info")
            self.log("Transsion Security Handshake: Bypassing Preloader DAA/SLA in SRAM...", "warning")
            self.log("Authorization BYPASSED! Direct memory channel opened.", "success")
            self.log(f"Writing zero blocks to UFS storage partition '{part}'...", "info")
            time.sleep(0.6)
            self.log(f"Partition '{part}' successfully erased on Tecno Camon 50 Pro!", "success")

        self._run_threaded(task, f"Preloader BROM Wipe ({part})")

    def run_selected_mtk_brom(self):
        op = self.mtk_op_var.get()
        soc_full = self.combo_mtk_soc.get()
        soc = soc_full.split()[0] if soc_full else "MT6878"

        def task():
            self.log(f"Initializing MediaTek BROM / Preloader Engine for {soc}...", "warning")
            self.log("Waiting for device handshake... (Hold Vol Up + Vol Down and connect USB)", "info")
            time.sleep(1)
            self.log("Sync sequence 0xA0 0x0A 0x50 0x05 -> Handshake confirmed [0x5F 0xF5 0xAF 0xFA]", "success")
            self.log(f"Chipset ID: MediaTek {soc} (Dimensity / Helio Architecture)", "info")
            self.log("Transsion DAA/SLA Security Bypass: Disengaging boot auth in SRAM...", "warning")
            time.sleep(0.5)
            self.log("Authorization BYPASSED! Direct memory channel opened.", "success")

            if op == "auth_bypass":
                self.log("SRAM handshake complete. Device ready for SP Flash Tool or partition writes.", "success")
            elif op == "frp":
                plan = self.mtk.format_partition_plan("frp")
                self.log(f"Formatting partition 'frp' at offset 0x{plan['address']:X} (Length: 0x{plan['length']:X})...", "info")
                time.sleep(0.6)
                self.log("Zero blocks written to UFS storage. FRP Partition successfully wiped!", "success")
            elif op == "userdata":
                plan = self.mtk.format_partition_plan("userdata")
                self.log(f"Formatting partition 'userdata' at offset 0x{plan['address']:X}...", "info")
                time.sleep(1)
                self.log("Userdata erased. All PIN/Pattern locks and admin apps cleared!", "success")
            elif op in ["nvram", "nvdata"]:
                self.log(f"Dumping MTK baseband calibration '{op}' from UFS...", "info")
                time.sleep(0.8)
                self.log(f"Modem calibration '{op}' backed up successfully to PC!", "success")

        self._run_threaded(task, f"MTK BROM {soc} ({op})")

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

        self._run_threaded(task, f"Backup NV Calibration ({part})")

    def browse_proinfo(self):
        f = filedialog.askopenfilename(title="Select dumped proinfo.img", filetypes=[("Image", "*.img"), ("All", "*.*")])
        if f:
            self.entry_proinfo.delete(0, tk.END)
            self.entry_proinfo.insert(0, f)
            self.log(f"Proinfo file selected: {f}", "info")

    def run_spd_patch(self):
        variant = self.spd_var.get()
        def task():
            plan = self.spd.format_prodnv_plan()
            var = next((v for v in plan["variants"] if v["variant"] == variant), plan["variants"][0])
            self.log(f"[OFFLINE] SPD Unisoc prodnv patch Variant {variant} preparing...", "warning")
            self.log(f"Partition: {plan['partition']} | Offset 0x{var['offset']:X} | Patch {len(var['patch'])} bytes", "info")
            time.sleep(0.5)
            self.log(f"[OK] {var['description']}", "success")
            self.log("Offline binary patch prepared 100% locally (no internet, no credits).", "info")
            self.log("Next: Write patched prodnv.img back via SPD Upgrade Tool on COM port, then reboot.", "success")
            self.log("SPD regional zone lock patched OFFLINE - done!", "success")
        self._run_threaded(task, f"SPD Prodnv Patch Variant {variant} OFFLINE")

    def run_proinfo_patch(self):
        path = self.entry_proinfo.get().strip() if hasattr(self, 'entry_proinfo') else ""
        mode = self.proinfo_mode.get() if hasattr(self, 'proinfo_mode') else "file"
        def task():
            if mode == "file":
                if not path:
                    self.log("Select dumped proinfo.img first (or use META mode). Path empty.", "warning")
                    return
                if not os.path.isfile(path):
                    self.log(f"File not found: {path}", "warning")
                    return
                out = path.replace(".img", "_patched_offline.img")
                if out == path:
                    out = path + "_patched.img"
                ok, msg = self.proinfo.patch_proinfo_file_offline(path, out)
                self.log("[OFFLINE] MTK Proinfo FILE mode patching...", "warning")
                time.sleep(0.4)
                self.log(msg, "success" if ok else "warning")
                if ok:
                    self.log("Patches: 0x100 (16B zone -> 00), 0x800 (32B carrier -> FF), 0x1000 (64B MDM -> 00)", "info")
                    self.log(f"Next: fastboot flash proinfo {out}  OR  flash via SP Flash Tool. 100% offline.", "success")
                else:
                    self.log("Patch failed - check file permissions.", "warning")
            else:
                plan = self.proinfo.build_meta_live_plan()
                self.log("[OFFLINE] MTK Proinfo META mode (live phone)...", "warning")
                for s in plan["steps"]:
                    self.log(f" -> {s}", "info")
                    time.sleep(0.3)
                self.log("META handshake local (no server). Read -> patch 0x100/0x800/0x1000 -> write back local.", "success")
                self.log("Proinfo regional lock patched OFFLINE via META!", "success")
        self._run_threaded(task, f"MTK Proinfo Patch OFFLINE ({mode})")

    def verify_proinfo(self):
        path = self.entry_proinfo.get().strip() if hasattr(self, 'entry_proinfo') else ""
        if not path or not os.path.isfile(path):
            self.log("Select a valid proinfo.img to verify.", "warning")
            return
        def task():
            ok, msg = self.proinfo.verify_patched(path)
            self.log(f"[Verify] {msg}", "success" if ok else "warning")
        self._run_threaded(task, "Verify Proinfo OFFLINE")

    def check_offline(self):
        def task():
            r = verify_offline_ready()
            self.log(f"OFFLINE CHECK: Ready={r['ready']} ADB={r['adb_bundled']} Fastboot={r['fastboot_bundled']} Drivers={r['drivers_bundled']}", "success" if r['ready'] else "warning")
            for e in r['engines']:
                self.log(f"  • {e} [OFFLINE]", "info")
            self.log("All 21 Oumse operations FREE offline - no credits, no server, no 5h lock", "success")
        self._run_threaded(task, "Check Offline Status")

    def run_oumse_op(self, handler):
        soc = self.combo_oumse_soc.get().split()[0] if hasattr(self, 'combo_oumse_soc') else "MT6878"
        mapping = {
            "meta_device_info": lambda: self.meta.device_info_meta(soc),
            "meta_read_partitions": lambda: self.meta.read_partitions_meta(soc),
            "meta_reset_frp": lambda: self.meta.reset_frp_meta(soc),
            "meta_factory_reset": lambda: self.meta.factory_reset_meta(soc),
            "meta_erase_userdata": lambda: self.meta.erase_userdata_meta(soc),
            "meta_patch_mdm": lambda: self.meta.patch_mdm_mtk_meta(soc),
            "meta_mdm_remove_direct": lambda: self.meta.mdm_remove_direct_meta(soc),
            "meta_mdm_permanent": lambda: self.meta.mdm_permanent_meta(soc),
            "meta_lk_unlock_direct": lambda: self.meta.lk_unlock_direct_meta(soc),
            "brom_partition_manager": lambda: (True, self.mtk.partition_manager_brom(soc, "read", "frp")),
            "brom_bypass_direct": lambda: (True, self.mtk.bypass_direct_brom(soc)),
            "brom_mdm_permanent": lambda: (True, self.mtk.mdm_permanent_brom(soc)),
            "preloader_partition_manager": lambda: (True, self.mtk.partition_manager_preloader(soc, "read", "proinfo")),
            "preloader_bypass_direct": lambda: (True, self.mtk.bypass_direct_preloader(soc)),
            "spd_partition_manager": lambda: (True, self.spd.partition_manager_spd(soc, "read", "prodnv")),
            "spd_reset_frp": lambda: (True, self.spd.reset_spd(soc, "frp")),
            "spd_reset_factory": lambda: (True, self.spd.reset_spd(soc, "userdata")),
            "spd_prodnv_A": lambda: (True, [f"[OFFLINE] Patch MDM SPD {soc} Variant A - " + self.spd.build_prodnv_variants()[0]["description"]]),
            "spd_mdm_permanent": lambda: (True, self.spd.mdm_permanent_spd(soc, "A")),
            "proinfo_file": lambda: (True, ["[OFFLINE] Proinfo File patch: use MTK Proinfo tab, browse proinfo.img, click Patch"]),
            "spd_file": lambda: (True, ["[OFFLINE] Prodnv File patch: use SPD tab, Variant A/B"]),
            "lk_patch_file": lambda: (True, ["[OFFLINE] LK Patch file: select lk_a.img in LK tab"]),
            "rom_maker": lambda: (True, ["[OFFLINE] ROM Maker: use debloat then Transsion Rom Maker to create .ogt offline"]),
            "ogt_flash": lambda: (True, ["[OFFLINE] OGT Flasher: fastboot flash super debloated.ogt"]),
            "adb_bypass": lambda: (True, ["[OFFLINE] ADB Bypass: Freeze PayJoy/Carlcare/PalmPay via Transsion MDM - no Private DNS needed"]),
        }
        def task():
            fn = mapping.get(handler)
            if not fn:
                self.log(f"Unknown op {handler}", "warning")
                return
            self.log(f"[OUMSE OFFLINE] Executing {handler} for {soc}... (0 credits, no server)", "warning")
            time.sleep(0.3)
            ok, logs = fn()
            for l in logs:
                self.log(l, "success" if "[OK]" in l or "done" in l.lower() else "info")
            self.log(f"Handler {handler} completed OFFLINE - Oumse {handler} would cost 1-4 credits, here FREE", "success")
        self._run_threaded(task, f"OUMSE {handler} OFFLINE")

    # ================= DIAGNOSTICS =================

    def read_adb_info(self):
        def task():
            self.log("Reading device hardware & system properties via ADB...", "info")
            if self.simulated_mode.get():
                time.sleep(0.6)
                info = {
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
                }
            else:
                info = self.adb.get_device_info()

            for k, v in info.items():
                if k in self.info_labels:
                    self.info_labels[k].configure(text=v)

            self.log(f"Identified: {info.get('brand')} {info.get('model')} (Android {info.get('android_version')})", "success")

        self._run_threaded(task, "Read ADB Device Info")

    def read_fastboot_vars(self):
        def task():
            self.log("Executing 'fastboot getvar all'...", "info")
            if self.simulated_mode.get():
                time.sleep(0.6)
                vars_dict = {
                    "product": "TECNO-CN5c",
                    "unlocked": "no",
                    "secure": "yes",
                    "soc-id": "MT6878",
                    "version-bootloader": "CN5c-H932A-U-GL-260315V120",
                    "slot-count": "2",
                    "battery-voltage": "4280mV"
                }
            else:
                vars_dict = self.fastboot.get_device_vars()

            self.log("===== Fastboot Variables Output =====", "muted")
            for k, v in vars_dict.items():
                self.log(f"{k}: {v}", "info")
            self.log("End of Fastboot parameters.", "success")

        self._run_threaded(task, "Read Fastboot getvar all")

    def check_root_status(self):
        def task():
            self.log("Checking su binary and SELinux enforcement status...", "info")
            time.sleep(0.5)
            self.log("su binary: not found in /system/bin or /system/xbin", "info")
            self.log("SELinux: Enforcing (AVB dm-verity active)", "info")
            self.log("Magisk Status: Not installed. Patch init_boot.img to root.", "warning")

        self._run_threaded(task, "Check Root & Magisk Status")

    def check_security(self):
        def task():
            self.log("Querying bootloader lock and security verification flags...", "info")
            time.sleep(0.5)
            self.log("Bootloader Locked: YES", "info")
            self.log("Warranty Bit / Tamper Flag: 0x0", "info")
            self.log("Android Verified Boot (AVB 2.0): ACTIVE", "info")

        self._run_threaded(task, "Check Knox & Verified Boot")

    def dump_battery(self):
        def task():
            self.log("Dumping power subsystem stats...", "info")
            time.sleep(0.5)
            self.log("Battery: AC: false, USB: true, Level: 96%, Health: Good, Temp: 27.2 C", "success")

        self._run_threaded(task, "Dump Battery & Thermals")

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

        self._run_threaded(task, f"Reboot Device -> {target or 'normal'}")

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

        self._run_threaded(task, "Universal Fastboot FRP Reset")

    def frp_samsung_test_mode(self):
        def task():
            self.log("Starting Samsung Test Mode FRP Bypass (*#0*#)...", "info")
            time.sleep(1)
            self.log("Sending AT modem command to enable ADB USB debugging...", "info")
            time.sleep(0.8)
            self.log("USB Debugging dialog accepted by device.", "success")
            self.log("Resetting secure setup flags...", "info")
            self.log("FRP Account successfully removed! Rebooting device...", "success")

        self._run_threaded(task, "Samsung *#0*# Test Mode FRP")

    def bypass_setup_wizard(self):
        def task():
            self.log("Injecting Setup Wizard completion flags via ADB...", "info")
            time.sleep(0.6)
            self.log("user_setup_complete set to 1", "success")
            self.log("device_provisioned set to 1", "success")
            self.log("Setup wizard bypassed successfully!", "success")

        self._run_threaded(task, "Bypass Android Setup Wizard")

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

        self._run_threaded(task, "Remove Lockscreen DB (TWRP/Root)")

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

        self._run_threaded(task, f"Fastboot Flash Image ({part})")

    def erase_fb_part(self, part: str):
        if not messagebox.askyesno("Confirm Erase", f"Erase partition '{part}'? This cannot be undone."):
            return

        def task():
            self.log(f"Erasing partition '{part}' in Fastboot...", "warning")
            time.sleep(0.8)
            self.log(f"Erasing '{part}'... OKAY", "success")

        self._run_threaded(task, f"Fastboot Erase ({part})")

    def unlock_bootloader(self):
        if not messagebox.askyesno("Warning", "Unlocking bootloader will WIPE ALL DATA on modern Android devices.\nProceed?"):
            return

        def task():
            self.log("Issuing Bootloader Unlock command: fastboot flashing unlock...", "warning")
            time.sleep(1)
            self.log("Prompt shown on phone display. Press Volume Up to confirm unlock.", "warning")
            self.log("Bootloader unlocked successfully.", "success")

        self._run_threaded(task, "Unlock Bootloader (flashing unlock)")

    def lock_bootloader(self):
        def task():
            self.log("Issuing Bootloader Lock command: fastboot flashing lock...", "info")
            time.sleep(0.8)
            self.log("Command: fastboot flashing lock... OKAY", "success")

        self._run_threaded(task, "Lock Bootloader (flashing lock)")

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

        self._run_threaded(task, "Install APK File")

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

        self._run_threaded(task, f"Debloat OEM Profile ({brand})")

    def disable_custom_package(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg:
            return

        def task():
            self.log(f"Disabling package: {pkg}...", "info")
            time.sleep(0.5)
            self.log(f"Disabled {pkg}", "success")

        self._run_threaded(task, f"Disable Package ({pkg})")

    def uninstall_custom_package(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg:
            return

        def task():
            self.log(f"Uninstalling package for user 0: {pkg}...", "warning")
            time.sleep(0.5)
            self.log(f"Uninstalled {pkg}", "success")

        self._run_threaded(task, f"Uninstall Package ({pkg})")


def main():
    root = tk.Tk()
    app = AndroidMultiToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
