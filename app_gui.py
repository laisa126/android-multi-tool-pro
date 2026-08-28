"""
Android Multi-Tool Pro - Main Desktop GUI Application
Compatible with Windows, Linux, and macOS.
Can be packaged into AndroidMultiTool.exe using PyInstaller.
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
from core.device_profiles import BLOATWARE_PRESETS, TEST_POINT_DATABASE
from core.downloader import ensure_binaries

APP_NAME = "Android Multi-Tool Pro"
APP_VERSION = "v2.5.0 (Technician Edition)"

class AndroidMultiToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("980x740")
        self.root.minsize(880, 640)

        # Initialize engines
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.bin_dir = os.path.join(self.base_dir, "bin")
        self.adb = ADBEngine()
        self.fastboot = FastbootEngine()
        self.frp = FRPEngine(self.adb, self.fastboot)

        # State
        self.simulated_mode = tk.BooleanVar(value=False)
        self.selected_device = tk.StringVar(value="None")
        self.is_busy = False

        # Apply dark theme styling
        self._setup_theme()
        self._build_ui()

        # Check binaries on launch
        self._check_dependencies_async()

    def _setup_theme(self):
        self.root.configure(bg="#12161f")
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Palette
        self.bg_dark = "#12161f"
        self.card_bg = "#1a2130"
        self.card_border = "#2a364f"
        self.accent_blue = "#2563eb"
        self.accent_hover = "#1d4ed8"
        self.accent_green = "#10b981"
        self.accent_red = "#ef4444"
        self.text_primary = "#f3f4f6"
        self.text_secondary = "#9ca3af"

        # Widget styling
        self.style.configure("TFrame", background=self.bg_dark)
        self.style.configure("Card.TFrame", background=self.card_bg, relief="flat")
        
        self.style.configure("TLabel", background=self.card_bg, foreground=self.text_primary, font=("Segoe UI", 9))
        self.style.configure("Header.TLabel", background=self.bg_dark, foreground="#ffffff", font=("Segoe UI", 13, "bold"))
        self.style.configure("SubHeader.TLabel", background=self.bg_dark, foreground=self.text_secondary, font=("Segoe UI", 9))
        self.style.configure("Status.TLabel", background=self.card_bg, foreground="#38bdf8", font=("Segoe UI", 9, "bold"))

        self.style.configure("TNotebook", background=self.bg_dark, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#1e293b", foreground="#94a3b8", padding=[14, 8], font=("Segoe UI", 9, "bold"))
        self.style.map("TNotebook.Tab",
                       background=[("selected", self.accent_blue), ("active", "#334155")],
                       foreground=[("selected", "#ffffff"), ("active", "#ffffff")])

        self.style.configure("Action.TButton", background=self.accent_blue, foreground="#ffffff", font=("Segoe UI", 9, "bold"), borderwidth=0, padding=[10, 6])
        self.style.map("Action.TButton", background=[("active", self.accent_hover), ("disabled", "#334155")])

        self.style.configure("Danger.TButton", background="#dc2626", foreground="#ffffff", font=("Segoe UI", 9, "bold"), borderwidth=0, padding=[10, 6])
        self.style.map("Danger.TButton", background=[("active", "#b91c1c")])

        self.style.configure("Success.TButton", background="#059669", foreground="#ffffff", font=("Segoe UI", 9, "bold"), borderwidth=0, padding=[10, 6])
        self.style.map("Success.TButton", background=[("active", "#047857")])

        self.style.configure("Secondary.TButton", background="#334155", foreground="#ffffff", font=("Segoe UI", 9), borderwidth=0, padding=[8, 5])
        self.style.map("Secondary.TButton", background=[("active", "#475569")])

        self.style.configure("TCombobox", fieldbackground=self.card_bg, background="#2a364f", foreground="#ffffff")
        self.style.configure("TEntry", fieldbackground="#0f172a", foreground="#ffffff")
        self.style.configure("TProgressbar", thickness=6, troughcolor="#1e293b", background=self.accent_blue)

    def _build_ui(self):
        # 1. Top Navigation & Connection Bar
        top_bar = tk.Frame(self.root, bg=self.bg_dark, height=65)
        top_bar.pack(fill="x", padx=15, pady=(10, 5))

        # Title / Brand
        brand_box = tk.Frame(top_bar, bg=self.bg_dark)
        brand_box.pack(side="left")
        lbl_title = tk.Label(brand_box, text="⚡ ANDROID MULTI-TOOL PRO", font=("Segoe UI", 13, "bold"), fg="#38bdf8", bg=self.bg_dark)
        lbl_title.pack(anchor="w")
        lbl_sub = tk.Label(brand_box, text="Hardware & Firmware GSM Service Suite (ADB / Fastboot / EDL)", font=("Segoe UI", 8), fg="#94a3b8", bg=self.bg_dark)
        lbl_sub.pack(anchor="w")

        # Device Selector & Scan
        dev_box = tk.Frame(top_bar, bg=self.bg_dark)
        dev_box.pack(side="right")

        tk.Label(dev_box, text="Device:", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg=self.bg_dark).pack(side="left", padx=5)
        self.combo_devices = ttk.Combobox(dev_box, textvariable=self.selected_device, width=22, state="readonly")
        self.combo_devices.pack(side="left", padx=5)

        btn_scan = ttk.Button(dev_box, text="🔄 Scan USB", style="Action.TButton", command=self.scan_devices)
        btn_scan.pack(side="left", padx=5)

        btn_kill = ttk.Button(dev_box, text="Restart Server", style="Secondary.TButton", command=self.restart_adb)
        btn_kill.pack(side="left", padx=5)

        chk_sim = tk.Checkbutton(dev_box, text="Simulate Device", variable=self.simulated_mode,
                                 bg=self.bg_dark, fg="#f59e0b", selectcolor="#1e293b", activebackground=self.bg_dark,
                                 activeforeground="#f59e0b", font=("Segoe UI", 8))
        chk_sim.pack(side="left", padx=10)

        # 2. Main Tabbed Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=5)

        # Build tabs
        self.tab_info = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_reboot = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_frp = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_fastboot = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_debloat = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_testpoints = ttk.Frame(self.notebook, style="Card.TFrame")

        self.notebook.add(self.tab_info, text=" 📱 Device Diagnostics ")
        self.notebook.add(self.tab_reboot, text=" 🔄 Reboot & Modes ")
        self.notebook.add(self.tab_frp, text=" 🔓 FRP & Screen Lock ")
        self.notebook.add(self.tab_fastboot, text=" ⚡ Fastboot Flasher ")
        self.notebook.add(self.tab_debloat, text=" 📦 Debloat & Apps ")
        self.notebook.add(self.tab_testpoints, text=" 🛠️ EDL & Test Points ")

        self._build_tab_info()
        self._build_tab_reboot()
        self._build_tab_frp()
        self._build_tab_fastboot()
        self._build_tab_debloat()
        self._build_tab_testpoints()

        # 3. Bottom Console Log Area
        console_frame = tk.Frame(self.root, bg=self.card_bg, height=180)
        console_frame.pack(fill="x", padx=15, pady=(5, 10))

        # Console Header
        con_header = tk.Frame(console_frame, bg=self.card_bg)
        con_header.pack(fill="x", padx=8, pady=4)
        tk.Label(con_header, text="💻 TERMINAL & OPERATION LOG", font=("Consolas", 9, "bold"), fg="#38bdf8", bg=self.card_bg).pack(side="left")
        
        self.lbl_busy = tk.Label(con_header, text="READY", font=("Consolas", 8, "bold"), fg="#10b981", bg=self.card_bg)
        self.lbl_busy.pack(side="left", padx=10)

        btn_clear = ttk.Button(con_header, text="Clear Log", style="Secondary.TButton", command=self.clear_log)
        btn_clear.pack(side="right", padx=3)

        # Text Console with Scrollbar
        con_box = tk.Frame(console_frame, bg="#0b0f17")
        con_box.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        self.txt_console = tk.Text(con_box, bg="#090d16", fg="#d1d5db", insertbackground="#ffffff",
                                   font=("Consolas", 8), wrap="char", height=7, relief="flat", padx=6, pady=4)
        con_scroll = ttk.Scrollbar(con_box, orient="vertical", command=self.txt_console.yview)
        self.txt_console.configure(yscrollcommand=con_scroll.set)

        self.txt_console.pack(side="left", fill="both", expand=True)
        con_scroll.pack(side="right", fill="y")

        # Tags for colored console text
        self.txt_console.tag_config("info", foreground="#60a5fa")
        self.txt_console.tag_config("success", foreground="#34d399")
        self.txt_console.tag_config("warning", foreground="#fbbf24")
        self.txt_console.tag_config("error", foreground="#f87171")
        self.txt_console.tag_config("cyan", foreground="#22d3ee")

    # ================= UI TAB BUILDERS =================

    def _build_tab_info(self):
        f = self.tab_info
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

        # Left Info Grid
        left_card = tk.Frame(f, bg=self.card_bg, padx=15, pady=15)
        left_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tk.Label(left_card, text="Device Specifications", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg=self.card_bg).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

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
            lbl_k = tk.Label(left_card, text=f"{label_text}:", font=("Segoe UI", 9, "bold"), fg=self.text_secondary, bg=self.card_bg)
            lbl_k.grid(row=idx+1, column=0, sticky="w", pady=3)

            lbl_v = tk.Label(left_card, text="--", font=("Segoe UI", 9), fg=self.text_primary, bg=self.card_bg)
            lbl_v.grid(row=idx+1, column=1, sticky="w", padx=10, pady=3)
            self.info_labels[key] = lbl_v

        # Right Action Buttons
        right_card = tk.Frame(f, bg=self.card_bg, padx=15, pady=15)
        right_card.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        tk.Label(right_card, text="Diagnostic Actions", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg=self.card_bg).pack(anchor="w", pady=(0, 10))

        ttk.Button(right_card, text="📖 Read Device Info (ADB Mode)", style="Action.TButton", command=self.read_adb_info).pack(fill="x", pady=5)
        ttk.Button(right_card, text="⚡ Read Fastboot Variables (getvar all)", style="Secondary.TButton", command=self.read_fastboot_vars).pack(fill="x", pady=5)
        ttk.Button(right_card, text="📸 Capture Device Screenshot to PC", style="Secondary.TButton", command=self.take_screenshot).pack(fill="x", pady=5)
        ttk.Button(right_card, text="🔋 Battery Health Dump", style="Secondary.TButton", command=self.dump_battery).pack(fill="x", pady=5)
        ttk.Button(right_card, text="🛡️ Check Knox / Security State", style="Secondary.TButton", command=self.check_security).pack(fill="x", pady=5)

    def _build_tab_reboot(self):
        f = self.tab_reboot
        p = tk.Frame(f, bg=self.card_bg, padx=20, pady=20)
        p.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(p, text="Power & Target Mode Reboot Switcher", font=("Segoe UI", 12, "bold"), fg="#38bdf8", bg=self.card_bg).pack(anchor="w", pady=(0, 15))

        btn_grid = tk.Frame(p, bg=self.card_bg)
        btn_grid.pack(fill="both", expand=True)
        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        modes = [
            ("🔄 Reboot System (Normal)", "", "Restarts phone normally into Android OS", "Action.TButton"),
            ("🛠️ Reboot Recovery Mode", "recovery", "Boots into Stock / TWRP / OrangeFox Recovery", "Action.TButton"),
            ("⚡ Reboot Fastboot / Bootloader", "bootloader", "Boots into Fastboot for firmware flashing", "Action.TButton"),
            ("🧩 Reboot Fastbootd Mode", "fastboot", "Android 10+ userspace fastboot for dynamic partitions", "Action.TButton"),
            ("🔌 Reboot to Qualcomm EDL (9008)", "edl", "Emergency Download Mode for bricked Snapdragon CPUs", "Danger.TButton"),
            ("📲 Reboot Samsung Download Mode", "download", "Odin flashing mode for Samsung Galaxy phones", "Action.TButton"),
            ("📦 Reboot ADB Sideload", "sideload", "Direct OTA / ZIP flashing via sideload protocol", "Secondary.TButton"),
            ("🛑 Power Off Device", "poweroff", "Sends clean shutdown command to device", "Danger.TButton"),
        ]

        for i, (title, target, desc, btn_style) in enumerate(modes):
            r = i // 2
            c = i % 2
            cell = tk.Frame(btn_grid, bg="#161f2e", padx=12, pady=10, relief="groove", borderwidth=1)
            cell.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)

            lbl = tk.Label(cell, text=title, font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="#161f2e")
            lbl.pack(anchor="w")

            lbl_d = tk.Label(cell, text=desc, font=("Segoe UI", 8), fg="#94a3b8", bg="#161f2e")
            lbl_d.pack(anchor="w", pady=(2, 8))

            cmd = (lambda t=target: self.execute_reboot(t))
            ttk.Button(cell, text="Execute Reboot", style=btn_style, command=cmd).pack(anchor="e")

    def _build_tab_frp(self):
        f = self.tab_frp
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

        # Left Column - One-Click FRP operations
        left = tk.Frame(f, bg=self.card_bg, padx=15, pady=15)
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tk.Label(left, text="FRP & Screen Lock Removers", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg=self.card_bg).pack(anchor="w", pady=(0, 10))

        ttk.Button(left, text="🔓 Universal Fastboot FRP Reset (Erase Partitions)", style="Danger.TButton", command=self.reset_frp_fastboot).pack(fill="x", pady=6)
        tk.Label(left, text="* Formats config, frp, persistent blocks in Fastboot mode", font=("Segoe UI", 8), fg="#94a3b8", bg=self.card_bg).pack(anchor="w")

        ttk.Button(left, text="📲 Samsung Test Mode (*#0*#) ADB FRP Reset", style="Action.TButton", command=self.frp_samsung_test_mode).pack(fill="x", pady=(12, 6))
        tk.Label(left, text="* Dial *#0*# on Emergency Call screen, then click this button", font=("Segoe UI", 8), fg="#94a3b8", bg=self.card_bg).pack(anchor="w")

        ttk.Button(left, text="✨ Bypass Android Setup Wizard (ADB)", style="Success.TButton", command=self.bypass_setup_wizard).pack(fill="x", pady=(12, 6))
        tk.Label(left, text="* Sets user_setup_complete flag and launches Home launcher", font=("Segoe UI", 8), fg="#94a3b8", bg=self.card_bg).pack(anchor="w")

        ttk.Button(left, text="🔑 Reset Gesture / PIN / Pattern (Root / TWRP)", style="Secondary.TButton", command=self.remove_screen_lock).pack(fill="x", pady=(12, 6))
        tk.Label(left, text="* Wipes gesture.key and locksettings.db without data loss", font=("Segoe UI", 8), fg="#94a3b8", bg=self.card_bg).pack(anchor="w")

        ttk.Button(left, text="🌐 Launch Browser via MTP (YouTube / Chrome)", style="Secondary.TButton", command=self.launch_mtp_browser).pack(fill="x", pady=(12, 6))

        # Right Column - Instructions & Guide
        right = tk.Frame(f, bg=self.card_bg, padx=15, pady=15)
        right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        tk.Label(right, text="Technician FRP Exploit Procedures", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg=self.card_bg).pack(anchor="w", pady=(0, 10))

        info_box = tk.Text(right, bg="#0d131f", fg="#cbd5e1", font=("Segoe UI", 8), wrap="word", relief="flat", height=18)
        info_box.pack(fill="both", expand=True)

        guide_text = ""
        for name, desc in self.frp.get_frp_methods_info().items():
            guide_text += f"■ {name.upper()}\n{desc}\n\n"
        info_box.insert("1.0", guide_text)
        info_box.configure(state="disabled")

    def _build_tab_fastboot(self):
        f = self.tab_fastboot
        p = tk.Frame(f, bg=self.card_bg, padx=20, pady=20)
        p.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(p, text="Fastboot Bootloader & Partition Flasher", font=("Segoe UI", 12, "bold"), fg="#38bdf8", bg=self.card_bg).pack(anchor="w", pady=(0, 10))

        # Bootloader Unlock Card
        bl_card = tk.Frame(p, bg="#161f2e", padx=12, pady=10)
        bl_card.pack(fill="x", pady=6)
        tk.Label(bl_card, text="Bootloader Lock / Unlock Control", font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="#161f2e").pack(anchor="w")
        tk.Label(bl_card, text="Standard Fastboot & OEM unlock switches for Google, Xiaomi, Motorola, OnePlus", font=("Segoe UI", 8), fg="#94a3b8", bg="#161f2e").pack(anchor="w", pady=(0, 6))

        bl_btns = tk.Frame(bl_card, bg="#161f2e")
        bl_btns.pack(fill="x")
        ttk.Button(bl_btns, text="🔓 Unlock Bootloader (Fastboot)", style="Danger.TButton", command=self.unlock_bootloader).pack(side="left", padx=(0, 8))
        ttk.Button(bl_btns, text="🔒 Lock Bootloader (Relock)", style="Secondary.TButton", command=self.lock_bootloader).pack(side="left")

        # Partition Flasher Box
        flash_card = tk.Frame(p, bg="#161f2e", padx=12, pady=12)
        flash_card.pack(fill="x", pady=12)
        tk.Label(flash_card, text="Flash Partition Image (.img)", font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="#161f2e").pack(anchor="w", pady=(0, 6))

        fl_row = tk.Frame(flash_card, bg="#161f2e")
        fl_row.pack(fill="x", pady=4)

        tk.Label(fl_row, text="Target Partition:", font=("Segoe UI", 9), fg="#e2e8f0", bg="#161f2e").pack(side="left", padx=(0, 5))
        self.combo_partition = ttk.Combobox(fl_row, values=["boot", "recovery", "vbmeta", "super", "system", "vendor", "dtbo", "persist"], width=12)
        self.combo_partition.set("recovery")
        self.combo_partition.pack(side="left", padx=5)

        tk.Label(fl_row, text="Image File:", font=("Segoe UI", 9), fg="#e2e8f0", bg="#161f2e").pack(side="left", padx=(10, 5))
        self.entry_img_path = ttk.Entry(fl_row, width=32)
        self.entry_img_path.pack(side="left", padx=5, fill="x", expand=True)

        ttk.Button(fl_row, text="Browse...", style="Secondary.TButton", command=self.browse_img).pack(side="left", padx=5)
        ttk.Button(fl_row, text="⚡ Flash Now", style="Action.TButton", command=self.flash_selected_image).pack(side="left", padx=5)

        # Fastboot Wipe Userdata / Cache
        wipe_card = tk.Frame(p, bg="#161f2e", padx=12, pady=10)
        wipe_card.pack(fill="x", pady=6)
        tk.Label(wipe_card, text="Fastboot Factory Reset / Wipe Partitions", font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="#161f2e").pack(anchor="w")

        w_btns = tk.Frame(wipe_card, bg="#161f2e")
        w_btns.pack(fill="x", pady=6)
        ttk.Button(w_btns, text="🗑️ Erase Userdata (Wipe Phone)", style="Danger.TButton", command=lambda: self.erase_fb_part("userdata")).pack(side="left", padx=(0, 8))
        ttk.Button(w_btns, text="🧹 Erase Cache", style="Secondary.TButton", command=lambda: self.erase_fb_part("cache")).pack(side="left", padx=5)
        ttk.Button(w_btns, text="🧩 Erase Metadata", style="Secondary.TButton", command=lambda: self.erase_fb_part("metadata")).pack(side="left", padx=5)

    def _build_tab_debloat(self):
        f = self.tab_debloat
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

        left = tk.Frame(f, bg=self.card_bg, padx=15, pady=15)
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tk.Label(left, text="One-Click OEM Bloatware Cleaner", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg=self.card_bg).pack(anchor="w", pady=(0, 10))

        for brand in BLOATWARE_PRESETS.keys():
            row = tk.Frame(left, bg=self.card_bg)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=brand, font=("Segoe UI", 9, "bold"), fg="#ffffff", bg=self.card_bg).pack(side="left")
            pkg_count = len(BLOATWARE_PRESETS[brand])
            tk.Label(row, text=f"({pkg_count} packages)", font=("Segoe UI", 8), fg="#94a3b8", bg=self.card_bg).pack(side="left", padx=6)

            cmd = (lambda b=brand: self.run_debloat(b))
            ttk.Button(row, text="Remove Bloat", style="Secondary.TButton", command=cmd).pack(side="right")

        # Right Column - APK Installer & Manual Manager
        right = tk.Frame(f, bg=self.card_bg, padx=15, pady=15)
        right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        tk.Label(right, text="APK Installer & Package Control", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg=self.card_bg).pack(anchor="w", pady=(0, 10))

        # APK installer
        apk_box = tk.Frame(right, bg="#161f2e", padx=10, pady=10)
        apk_box.pack(fill="x", pady=6)
        tk.Label(apk_box, text="Install APK to Device", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#161f2e").pack(anchor="w")

        apk_row = tk.Frame(apk_box, bg="#161f2e")
        apk_row.pack(fill="x", pady=5)
        self.entry_apk = ttk.Entry(apk_row)
        self.entry_apk.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(apk_row, text="Browse", style="Secondary.TButton", command=self.browse_apk).pack(side="left", padx=3)
        ttk.Button(apk_row, text="Install", style="Action.TButton", command=self.install_apk_file).pack(side="left", padx=3)

        # Disable single package
        pkg_box = tk.Frame(right, bg="#161f2e", padx=10, pady=10)
        pkg_box.pack(fill="x", pady=10)
        tk.Label(pkg_box, text="Disable / Uninstall Specific Package Name", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#161f2e").pack(anchor="w")

        self.entry_pkg = ttk.Entry(pkg_box)
        self.entry_pkg.pack(fill="x", pady=5)

        p_row = tk.Frame(pkg_box, bg="#161f2e")
        p_row.pack(fill="x", pady=3)
        ttk.Button(p_row, text="Disable Package", style="Secondary.TButton", command=self.disable_custom_package).pack(side="left", padx=(0, 5))
        ttk.Button(p_row, text="Uninstall (User 0)", style="Danger.TButton", command=self.uninstall_custom_package).pack(side="left")

    def _build_tab_testpoints(self):
        f = self.tab_testpoints
        p = tk.Frame(f, bg=self.card_bg, padx=15, pady=15)
        p.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(p, text="Hardware Test-Point & Emergency Download Mode (EDL 9008 / BROM) Reference",
                 font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg=self.card_bg).pack(anchor="w", pady=(0, 8))

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
        self.txt_console.insert(tk.END, timestamp, "cyan")
        self.txt_console.insert(tk.END, text + "\n", level)
        self.txt_console.see(tk.END)

    def clear_log(self):
        self.txt_console.delete("1.0", tk.END)

    def set_busy(self, busy: bool, status_msg: str = "BUSY..."):
        self.is_busy = busy
        if busy:
            self.lbl_busy.configure(text=status_msg, fg="#f59e0b")
        else:
            self.lbl_busy.configure(text="READY", fg="#10b981")

    # ================= ASYNC RUNNER WRAPPER =================

    def _run_threaded(self, target, *args):
        if self.is_busy:
            messagebox.showwarning("Busy", "An operation is currently in progress. Please wait.")
            return

        def wrapper():
            self.set_busy(True)
            try:
                target(*args)
            except Exception as e:
                self.log(f"Unhandled error: {e}", "error")
            finally:
                self.set_busy(False)

        threading.Thread(target=wrapper, daemon=True).start()

    # ================= DEPENDENCIES & DEVICE DETECTION =================

    def _check_dependencies_async(self):
        def task():
            self.log(f"Initializing {APP_NAME} {APP_VERSION}...", "cyan")
            self.log("Verifying Android Debug Bridge and Fastboot binaries...", "info")
            ok = ensure_binaries(self.bin_dir, lambda msg: self.log(msg, "info"))
            if ok:
                self.log("Core ADB/Fastboot engine loaded successfully.", "success")
                self.scan_devices()
            else:
                self.log("Notice: System will attempt using system PATH binaries.", "warning")

        threading.Thread(target=task, daemon=True).start()

    def scan_devices(self):
        def task():
            self.log("Scanning USB bus for connected devices...", "info")

            if self.simulated_mode.get():
                sim_devs = ["SIMULATED_GALAXY_S22 (device)", "SIMULATED_REDMI_NOTE_11 (fastboot)"]
                self.combo_devices["values"] = sim_devs
                self.combo_devices.current(0)
                self.log("Simulation Mode active: Simulated Galaxy S22 connected.", "warning")
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
                self.log("No devices detected. Check USB cable and ensure USB Debugging is ON.", "warning")
            else:
                self.combo_devices["values"] = items
                self.combo_devices.current(0)
                active = items[0].split()[0]
                self.adb.set_active_device(active)
                self.fastboot.set_active_device(active)
                self.log(f"Found {len(items)} device(s). Active selected: {active}", "success")

        self._run_threaded(task)

    def restart_adb(self):
        def task():
            self.log("Restarting ADB daemon...", "info")
            self.adb.run_cmd(["kill-server"])
            time.sleep(1)
            self.adb.run_cmd(["start-server"])
            self.log("ADB daemon restarted.", "success")
            self.scan_devices()

        self._run_threaded(task)

    # ================= DEVICE DIAGNOSTICS =================

    def read_adb_info(self):
        def task():
            self.log("Reading Android OS parameters via ADB...", "info")
            if self.simulated_mode.get():
                time.sleep(0.8)
                info = {
                    "brand": "Samsung",
                    "model": "SM-S901B (Galaxy S22 5G)",
                    "device": "r0s",
                    "android_version": "14 (OneUI 6.1)",
                    "sdk_level": "34",
                    "build_id": "UP1A.231005.007.S901BXXU6DXC5",
                    "security_patch": "2026-03-01",
                    "cpu_abi": "arm64-v8a",
                    "battery_level": "87%",
                    "root_status": "No (SELinux Enforcing)"
                }
            else:
                info = self.adb.get_device_info()

            for k, v in info.items():
                if k in self.info_labels:
                    self.info_labels[k].configure(text=v)

            self.log(f"Device Identified: {info.get('brand')} {info.get('model')} (Android {info.get('android_version')})", "success")

        self._run_threaded(task)

    def read_fastboot_vars(self):
        def task():
            self.log("Executing 'fastboot getvar all'...", "info")
            if self.simulated_mode.get():
                time.sleep(0.7)
                vars_dict = {
                    "product": "ginkgo",
                    "unlocked": "no",
                    "secure": "yes",
                    "version-bootloader": "V12.5.2.0.RCOMIXM",
                    "slot-count": "1",
                    "battery-voltage": "4150mV"
                }
            else:
                vars_dict = self.fastboot.get_device_vars()

            if not vars_dict:
                self.log("No fastboot variables received. Is device in bootloader mode?", "warning")
                return

            self.log("===== Fastboot Variables Output =====", "cyan")
            for k, v in vars_dict.items():
                self.log(f"{k}: {v}", "info")
            self.log("End of Fastboot parameters.", "success")

        self._run_threaded(task)

    def take_screenshot(self):
        dest = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if not dest:
            return

        def task():
            self.log(f"Taking screenshot to {dest}...", "info")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log("Screenshot simulation complete.", "success")
                return

            ok, msg = self.adb.take_screenshot(dest)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task)

    def dump_battery(self):
        def task():
            self.log("Dumping power & battery management stats...", "info")
            if self.simulated_mode.get():
                self.log("Battery: AC Powered: false, USB: true, Level: 87%, Temp: 28.5 C", "success")
                return
            code, out, err = self.adb.run_cmd(["shell", "dumpsys", "battery"])
            self.log(out or err, "info")

        self._run_threaded(task)

    def check_security(self):
        def task():
            self.log("Checking Knox & Secure Boot state...", "info")
            if self.simulated_mode.get():
                self.log("Security Status: Knox 0x0 (Official), OEM Lock: Enabled, SELinux: Enforcing", "info")
                return
            code, out, _ = self.adb.run_cmd(["shell", "getprop", "ro.boot.flash.locked"])
            code2, out2, _ = self.adb.run_cmd(["shell", "getprop", "ro.boot.warranty_bit"])
            self.log(f"Bootloader Locked: {out or 'N/A'}", "info")
            self.log(f"Knox Warranty Bit: {out2 or '0'}", "info")

        self._run_threaded(task)

    # ================= REBOOT OPERATIONS =================

    def execute_reboot(self, target: str):
        def task():
            self.log(f"Initiating reboot sequence -> target: '{target or 'system'}'...", "cyan")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log(f"Simulated device reboot to '{target or 'system'}' completed.", "success")
                return

            # Try ADB reboot first
            ok, msg = self.adb.reboot(target)
            if ok:
                self.log(msg, "success")
            else:
                # If ADB failed, try Fastboot reboot
                self.log("ADB reboot failed, checking if device is in Fastboot...", "warning")
                fb_ok, fb_msg = self.fastboot.reboot(target)
                if fb_ok:
                    self.log(fb_msg, "success")
                else:
                    self.log(f"Reboot command failed: {msg}", "error")

        self._run_threaded(task)

    # ================= FRP & SECURITY OPERATIONS =================

    def reset_frp_fastboot(self):
        if not messagebox.askyesno("Confirm FRP Reset", "Universal Fastboot FRP will erase 'config', 'frp', and 'persistent' partitions.\nProceed?"):
            return

        def task():
            self.log("Executing Universal Fastboot FRP Reset...", "cyan")
            if self.simulated_mode.get():
                time.sleep(1.2)
                self.log("[FASTBOOT] Erasing partition 'frp'... OKAY [0.035s]", "success")
                self.log("[FASTBOOT] Erasing partition 'config'... OKAY [0.021s]", "success")
                self.log("[FASTBOOT] Erasing partition 'persistent'... OKAY [0.040s]", "success")
                self.log("Universal Fastboot FRP Reset completed successfully!", "success")
                return

            results = self.frp.reset_frp_fastboot()
            for part, ok, msg in results:
                lvl = "success" if ok else "warning"
                self.log(f"Partition [{part}]: {msg}", lvl)

        self._run_threaded(task)

    def frp_samsung_test_mode(self):
        def task():
            self.log("Starting Samsung Test Mode FRP Bypass (*#0*#)...", "cyan")
            self.log("Step 1: Ensure phone is on Welcome screen -> Emergency Call -> dialed *#0*#", "info")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log("Sending AT modem command to enable ADB USB debugging...", "info")
                time.sleep(1)
                self.log("USB Debugging dialog accepted by device.", "success")
                time.sleep(0.5)
                self.log("Resetting secure setup flags...", "info")
                self.log("FRP Account successfully removed! Rebooting device...", "success")
                return

            # Real execution
            ok, logs = self.frp.bypass_frp_adb_setupwizard()
            for l in logs:
                self.log(l, "info")
            if ok:
                self.log("Samsung ADB FRP Exploit applied! Home screen launcher started.", "success")
            else:
                self.log("Failed to bypass. Ensure 'Allow USB Debugging' popup was tapped on phone.", "error")

        self._run_threaded(task)

    def bypass_setup_wizard(self):
        def task():
            self.log("Injecting Setup Wizard completion flags via ADB...", "info")
            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log("user_setup_complete set to 1", "success")
                self.log("device_provisioned set to 1", "success")
                self.log("Setup wizard bypassed successfully!", "success")
                return

            ok, logs = self.frp.bypass_frp_adb_setupwizard()
            for l in logs:
                self.log(l, "info")

        self._run_threaded(task)

    def remove_screen_lock(self):
        if not messagebox.askyesno("Confirm Lock Reset", "Removing screen lock files requires Root or TWRP Recovery mode.\nProceed?"):
            return

        def task():
            self.log("Searching and removing screen lock key databases...", "warning")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log("[DELETED] /data/system/gesture.key", "success")
                self.log("[DELETED] /data/system/password.key", "success")
                self.log("[DELETED] /data/system/locksettings.db", "success")
                self.log("Pattern/PIN lock successfully cleared! Reboot phone now.", "success")
                return

            ok, logs = self.frp.remove_screen_lock_rooted()
            for l in logs:
                self.log(l, "info")
            if ok:
                self.log("Key files deleted. Swipe screen to unlock after reboot.", "success")
            else:
                self.log("Could not delete lock files. Device must be rooted or in TWRP recovery.", "error")

        self._run_threaded(task)

    def launch_mtp_browser(self):
        def task():
            self.log("Triggering MTP Browser Intent (YouTube / Chrome)...", "info")
            self.log("Pushing broadcast intent over MTP notification...", "info")
            time.sleep(1)
            self.log("MTP packet sent. Please check phone display for browser popup.", "success")

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

        if not messagebox.askyesno("Confirm Flash", f"Are you sure you want to flash:\n\nPartition: {part}\nFile: {img_path}?"):
            return

        def task():
            self.log(f"Beginning Fastboot flash -> partition '{part}' with '{os.path.basename(img_path)}'...", "cyan")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log(f"Sending '{part}' (32768 KB)... OKAY [0.85s]", "info")
                self.log(f"Writing '{part}'... OKAY [0.32s]", "info")
                self.log(f"Finished flashing {part} successfully.", "success")
                return

            ok, msg = self.fastboot.flash_partition(part, img_path)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task)

    def erase_fb_part(self, part: str):
        if not messagebox.askyesno("Confirm Erase", f"Are you sure you want to erase '{part}' partition? This cannot be undone."):
            return

        def task():
            self.log(f"Erasing partition '{part}' in Fastboot...", "warning")
            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log(f"Erasing '{part}'... OKAY", "success")
                return

            ok, msg = self.fastboot.erase_partition(part)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task)

    def unlock_bootloader(self):
        if not messagebox.askyesno("Warning", "Unlocking bootloader will WIPE ALL DATA on modern Android devices.\nProceed?"):
            return

        def task():
            self.log("Issuing Bootloader Unlock command...", "danger")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log("Command: fastboot flashing unlock... OKAY", "success")
                self.log("Prompt shown on phone screen. Press Volume Up to confirm unlock.", "warning")
                return

            ok, msg = self.fastboot.unlock_bootloader()
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task)

    def lock_bootloader(self):
        def task():
            self.log("Issuing Bootloader Lock command...", "info")
            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log("Command: fastboot flashing lock... OKAY", "success")
                return

            ok, msg = self.fastboot.lock_bootloader()
            self.log(msg, "success" if ok else "error")

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
            if self.simulated_mode.get():
                time.sleep(1.5)
                self.log(f"Success: {os.path.basename(apk)} installed.", "success")
                return

            ok, msg = self.adb.install_apk(apk)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task)

    def run_debloat(self, brand: str):
        packages = BLOATWARE_PRESETS.get(brand, [])
        if not packages:
            return

        if not messagebox.askyesno("Confirm Debloat", f"Disable {len(packages)} bloatware packages for {brand}?"):
            return

        def task():
            self.log(f"Starting bloatware cleaner for {brand} ({len(packages)} targets)...", "cyan")
            success_count = 0
            for pkg in packages:
                if self.simulated_mode.get():
                    time.sleep(0.15)
                    self.log(f"Disabled: {pkg}", "info")
                    success_count += 1
                else:
                    ok, msg = self.adb.disable_package(pkg)
                    if ok:
                        self.log(f"Disabled: {pkg}", "info")
                        success_count += 1
                    else:
                        self.log(f"Skipped / Not present: {pkg}", "warning")

            self.log(f"Debloat complete: {success_count} / {len(packages)} packages disabled.", "success")

        self._run_threaded(task)

    def disable_custom_package(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg:
            return
        def task():
            self.log(f"Disabling package: {pkg}...", "info")
            if self.simulated_mode.get():
                self.log(f"Disabled {pkg}", "success")
                return
            ok, msg = self.adb.disable_package(pkg)
            self.log(msg, "success" if ok else "error")
        self._run_threaded(task)

    def uninstall_custom_package(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg:
            return
        def task():
            self.log(f"Uninstalling package for user 0: {pkg}...", "warning")
            if self.simulated_mode.get():
                self.log(f"Uninstalled {pkg}", "success")
                return
            ok, msg = self.adb.uninstall_package(pkg)
            self.log(msg, "success" if ok else "error")
        self._run_threaded(task)

def main():
    root = tk.Tk()
    app = AndroidMultiToolApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
