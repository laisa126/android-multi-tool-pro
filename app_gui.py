"""
Android Multi-Tool Pro - Main Desktop GUI Application
Strict Monochrome High-Contrast Edition (Black & White, <= 10 Colors)
Engineered for Tecno Camon 50 Pro 4G (Helio G200 Ultimate / MT6789 / HiOS 16) & All Brands
"""

import os
import sys
import time
import threading
import subprocess
import platform
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
from core.device_matrix import SUPPORTED_DEVICE_CATALOG, find_device_matches
from core.downloader import ensure_binaries
from core.detection import run_full_detection, selectable_devices
from core.connection_guide import CONNECTION_SCENARIOS, ADB_STATE_GUIDANCE
from core.serial_ports import build_custom_adb_inf
from core.dependency_installer import (
    ensure_runtime_dependencies, run_windows_driver_installer, driver_install_guidance
)

APP_NAME = "Android Multi-Tool Pro"
APP_VERSION = "v2.5.0 (Tecno Camon 50 Pro 4G Edition)"

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
C_ACCENT = "#22d3ee"  # UnlockTool-style cyan accent for active nav


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

        # ---- Persistent session logging (audit trail for every op) ----
        self.logs_dir = os.path.join(self.base_dir, "logs")
        try:
            os.makedirs(self.logs_dir, exist_ok=True)
        except Exception:
            self.logs_dir = self.base_dir
        self._log_lock = threading.Lock()
        self.log_file_path = os.path.join(
            self.logs_dir, time.strftime("amt_pro_%Y%m%d_%H%M%S.log")
        )
        try:
            self._log_file = open(self.log_file_path, "a", encoding="utf-8", errors="replace")
        except Exception:
            self._log_file = None

        # Live command echo: engine -> console/file log
        self.adb.log_callback = self._engine_log
        self.fastboot.log_callback = self._engine_log

        # State
        self.simulated_mode = tk.BooleanVar(value=False)
        self.selected_device = tk.StringVar(value="None")
        self.is_busy = False
        # display-label -> {"kind": "adb"|"fastboot", "serial": ...} for the combobox
        self.device_entries: dict = {}
        # Auto-connect monitor state (watches for a device being plugged in)
        self._auto_connect_active = False
        self._auto_connect_stop = threading.Event()
        self._auto_connect_stop.set()  # idle by default

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
        self.combo_devices.bind("<<ComboboxSelected>>", self._on_device_selected)

        btn_scan = ttk.Button(dev_box, text="Scan Devices", style="Action.TButton", command=self.scan_devices)
        btn_scan.pack(side="left", padx=4)

        self.btn_auto_connect = ttk.Button(dev_box, text="Auto-Connect", style="Action.TButton", command=self.auto_connect)
        self.btn_auto_connect.pack(side="left", padx=4)

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
        tk.Label(hw_strip, text="TARGET: MediaTek MT6789 (Helio G200 Ultimate)", font=("Segoe UI", 8, "bold"), fg=C_WHITE, bg=C_BORDER).pack(side="left")
        tk.Label(hw_strip, text=" | TECNO-CN5c (Camon 50 Pro 4G) | UFS 2.2 | Android 16 (HiOS 16)", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_BORDER).pack(side="left")
        self.lbl_conn_state = tk.Label(hw_strip, text="● NOT CONNECTED", font=("Segoe UI", 8, "bold"), fg=C_RED, bg=C_BORDER)
        self.lbl_conn_state.pack(side="left", padx=(16, 0))
        tk.Label(hw_strip, text="SECURITY: AVB 2.0 ENFORCING", font=("Segoe UI", 8, "bold"), fg=C_GREEN, bg=C_BORDER).pack(side="right")

        # 2. Main Content — UnlockTool-style left navigation rail + workspace
        self.content_shell = tk.Frame(self.root, bg=C_BORDER)
        self.content_shell.pack(fill="both", expand=True, padx=15, pady=5)

        # --- Left navigation rail ---
        self.nav_rail = tk.Frame(self.content_shell, bg=C_BORDER, width=224)
        self.nav_rail.pack(side="left", fill="y")
        self.nav_rail.pack_propagate(False)

        tk.Label(self.nav_rail, text="ANDROID MULTI-TOOL", font=("Segoe UI", 10, "bold"),
                 fg=C_WHITE, bg=C_BORDER).pack(anchor="w", padx=16, pady=(16, 2))
        tk.Label(self.nav_rail, text="PRO · v2.5 — OFFLINE GSM SUITE", font=("Segoe UI", 7),
                 fg=C_TEXT_MUTED, bg=C_BORDER).pack(anchor="w", padx=16, pady=(0, 12))

        self._nav_buttons = {}
        nav_sections = [
            ("SERVICE", [
                ("camon50",    "  \U0001F4F1  Tecno Camon 50 Suite"),
                ("mtk",        "  \u26A1  MTK BROM Flasher"),
                ("fastboot",   "  \U0001F680  Fastboot Flasher"),
                ("frp",        "  \U0001F513  FRP & Screen Lock"),
                ("debloat",    "  \U0001F9F9  Debloat & Apps"),
                ("testpoints", "  \U0001F3AF  EDL & Test Points"),
            ]),
            ("DIAGNOSTICS", [
                ("info",    "  \U0001FA7A  Diagnostics"),
                ("connect", "  \U0001F50C  Connection Guide"),
                ("reboot",  "  \U0001F501  Reboot Switcher"),
            ]),
            ("REFERENCE", [
                ("devices", "  \U0001F4CB  Supported Devices"),
            ]),
        ]
        for section, items in nav_sections:
            tk.Label(self.nav_rail, text=section, font=("Segoe UI", 7, "bold"),
                     fg=C_TEXT_MUTED, bg=C_BORDER).pack(anchor="w", padx=18, pady=(12, 2))
            for key, label in items:
                btn = tk.Button(
                    self.nav_rail, text=label, font=("Segoe UI", 9, "bold"),
                    fg=C_TEXT_MUTED, bg=C_BORDER, activebackground=C_SUBCARD,
                    activeforeground=C_WHITE, relief="flat", bd=0, anchor="w",
                    padx=12, pady=8, cursor="hand2", highlightthickness=0,
                    command=lambda k=key: self.show_tab(k),
                )
                btn.pack(fill="x", padx=6, pady=1)
                self._nav_buttons[key] = btn

        # --- Right workspace: scrollable canvas hosting the tab frames ---
        self.content = tk.Frame(self.content_shell, bg=C_CARD)
        self.content.pack(side="left", fill="both", expand=True)

        self._workspace_canvas = tk.Canvas(self.content, bg=C_CARD, highlightthickness=0, borderwidth=0)
        self._workspace_vbar = ttk.Scrollbar(self.content, orient="vertical", command=self._workspace_canvas.yview)
        self._workspace_canvas.configure(yscrollcommand=self._workspace_vbar.set)
        self._workspace_vbar.pack(side="right", fill="y")
        self._workspace_canvas.pack(side="left", fill="both", expand=True)

        self._tab_host = tk.Frame(self._workspace_canvas, bg=C_CARD)
        self._canvas_window = self._workspace_canvas.create_window((0, 0), window=self._tab_host, anchor="nw")
        self._tab_host.bind("<Configure>", lambda e: self._workspace_canvas.configure(
            scrollregion=self._workspace_canvas.bbox("all")))
        self._workspace_canvas.bind("<Configure>", lambda e: self._workspace_canvas.itemconfigure(
            self._canvas_window, width=e.width))

        self.tab_camon50 = tk.Frame(self._tab_host, bg=C_CARD)
        self.tab_mtk = tk.Frame(self._tab_host, bg=C_CARD)
        self.tab_info = tk.Frame(self._tab_host, bg=C_CARD)
        self.tab_frp = tk.Frame(self._tab_host, bg=C_CARD)
        self.tab_fastboot = tk.Frame(self._tab_host, bg=C_CARD)
        self.tab_reboot = tk.Frame(self._tab_host, bg=C_CARD)
        self.tab_debloat = tk.Frame(self._tab_host, bg=C_CARD)
        self.tab_testpoints = tk.Frame(self._tab_host, bg=C_CARD)
        self.tab_connect = tk.Frame(self._tab_host, bg=C_CARD)
        self.tab_devices = tk.Frame(self._tab_host, bg=C_CARD)

        self._tab_frames = {
            "camon50": self.tab_camon50,
            "mtk": self.tab_mtk,
            "info": self.tab_info,
            "frp": self.tab_frp,
            "fastboot": self.tab_fastboot,
            "reboot": self.tab_reboot,
            "debloat": self.tab_debloat,
            "testpoints": self.tab_testpoints,
            "connect": self.tab_connect,
            "devices": self.tab_devices,
        }

        self._build_tab_camon50()
        self._build_tab_connect()
        self._build_tab_devices()
        self._build_tab_mtk()
        self._build_tab_info()
        self._build_tab_frp()
        self._build_tab_fastboot()
        self._build_tab_reboot()
        self._build_tab_debloat()
        self._build_tab_testpoints()

        self.show_tab("camon50")

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
        btn_open = ttk.Button(con_header, text="Open Logs Folder", style="Secondary.TButton", command=self.open_logs_folder)
        btn_open.pack(side="right", padx=3)
        btn_save = ttk.Button(con_header, text="Save Log", style="Secondary.TButton", command=self.save_log)
        btn_save.pack(side="right", padx=3)

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

        # Mouse-wheel scrolling for the workspace canvas (console/treeviews keep native scroll)
        self._bind_mousewheel()

    def _bind_mousewheel(self):
        """Bind the mouse wheel so it scrolls the workspace canvas under the pointer."""
        def _on_wheel(event):
            w = self.root.winfo_containing(event.x_root, event.y_root)
            if w is None:
                return
            # Walk up: if the pointer is over a natively-scrolling widget (Text,
            # Treeview, Listbox), let that widget scroll instead of the canvas.
            cur = w
            while cur is not None and cur is not self._tab_host:
                if isinstance(cur, (tk.Text, ttk.Treeview, tk.Listbox)):
                    return
                cur = getattr(cur, "master", None)
            if cur is None:
                return  # pointer not inside the scrollable workspace
            delta = getattr(event, "delta", 0)
            if delta:
                step = -1 if delta > 0 else 1
            else:
                step = -1 if getattr(event, "num", 0) == 4 else 1
            self._workspace_canvas.yview_scroll(step, "units")

        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.root.bind_all(seq, _on_wheel, add="+")

        # Linux (X11) reports the wheel as Button-4/Button-5 and Tk does NOT
        # auto-scroll Text/Listbox/Treeview for those events. Add class-level
        # bindings so every scrollable widget rolls under the wheel on Linux.
        # (Windows/macOS already use <MouseWheel> natively; these are no-ops.)
        def _wheel_text(event):
            event.widget.yview_scroll(-1 if getattr(event, "num", 0) == 4 else 1, "units")
            return "break"

        def _wheel_listbox(event):
            event.widget.yview_scroll(-1 if getattr(event, "num", 0) == 4 else 1, "units")
            return "break"

        def _wheel_tree(event):
            event.widget.yview_scroll(-1 if getattr(event, "num", 0) == 4 else 1, "units")
            return "break"

        for cls, fn in (("Text", _wheel_text), ("Listbox", _wheel_listbox), ("Treeview", _wheel_tree)):
            self.root.bind_class(cls, "<Button-4>", fn, add="+")
            self.root.bind_class(cls, "<Button-5>", fn, add="+")

    def show_tab(self, key: str):
        """Switch the visible workspace pane (UnlockTool-style sidebar nav)."""
        for k, frame in self._tab_frames.items():
            if k == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg=C_ACCENT, bg=C_SUBCARD)
            else:
                btn.configure(fg=C_TEXT_MUTED, bg=C_BORDER)
        self.log(f"Navigation: opened [{key}]", "muted")

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
        ttk.Button(b_row1, text="Wipe FRP (BROM)", style="Danger.TButton", command=lambda: self.mtk_brom_wipe("frp")).pack(side="left", padx=(0, 5))
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
            "MT6789 - Helio G200 Ultimate (Tecno Camon 50 Pro 4G / CN5c)",
            "MT6878 - Dimensity 7400 Ultimate (Tecno Camon 50 Pro 5G / CN7c)",
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
        self.combo_mtk_port = ttk.Combobox(port_row, values=["Auto-Detect (Preloader -> BROM crash)", "COM3 (MediaTek Preloader)", "COM5 (MTK USB Port)"], width=28)
        self.combo_mtk_port.current(0)
        self.combo_mtk_port.pack(side="left", fill="x", expand=True)

        # 1-Click Operations
        op_box = tk.Frame(left_card, bg=C_SUBCARD, padx=10, pady=10)
        op_box.pack(fill="x", pady=6)
        tk.Label(op_box, text="Select BROM Operation:", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")

        self.mtk_op_var = tk.StringVar(value="frp")
        ops = [
            ("Wipe FRP Partition (offset from firmware scatter - Camon 50 Pro)", "frp"),
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
        btn_detect = ttk.Button(left_card, text="🔍 Detect BROM Port & Handshake (locked phone)", style="Secondary.TButton", command=self.mtk_detect_handshake)
        btn_detect.pack(fill="x", pady=(0, 4))
        btn_info = ttk.Button(left_card, text="🆔 Read BROM Chip Info (HW code / target config)", style="Secondary.TButton", command=self.brom_read_info)
        btn_info.pack(fill="x", pady=(0, 4))

        # Download Agent upload (advanced — SLA/DAA gated)
        da_card = tk.Frame(left_card, bg=C_SUBCARD, padx=10, pady=8)
        da_card.pack(fill="x", pady=4)
        tk.Label(da_card, text="Download Agent (DA) upload:", font=("Segoe UI", 8, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        da_row = tk.Frame(da_card, bg=C_SUBCARD)
        da_row.pack(fill="x", pady=4)
        self.entry_da_path = ttk.Entry(da_row, width=20)
        self.entry_da_path.pack(side="left", padx=(0, 4), fill="x", expand=True)
        ttk.Button(da_row, text="Browse", style="Secondary.TButton", command=self.browse_da).pack(side="left", padx=2)
        ttk.Button(da_row, text="Upload DA", style="Secondary.TButton", command=self.run_send_da).pack(side="left", padx=2)

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
            "■ UFS MEMORY OFFSETS (HELIO G200 / MT6789 - from firmware scatter):\n"
            "   - frp: from CN5c firmware scatter (do not hardcode)\n"
            "   - userdata: Encrypted user data (wipe clears all screen locks)\n"
            "   - nvram / nvdata: Baseband / IMEI calibrations (backup first)"
        )

        txt_info = tk.Text(guide_card, bg=C_SUBCARD, fg=C_TEXT_BODY, font=("Segoe UI", 8), wrap="word", relief="flat")
        txt_info.insert("1.0", steps_text)
        txt_info.configure(state="disabled")
        txt_info.pack(fill="both", expand=True)

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

        # Recovery Sideload (works with USB debugging DISABLED)
        sl_card = tk.Frame(p, bg=C_SUBCARD, padx=12, pady=12)
        sl_card.pack(fill="x", pady=6)
        tk.Label(sl_card, text="Recovery ADB Sideload (no USB debugging needed)", font=("Segoe UI", 9, "bold"), fg=C_WHITE, bg=C_SUBCARD).pack(anchor="w")
        tk.Label(sl_card, text="Boot to Recovery -> 'Apply update from ADB'. Recovery adbd needs NO USB debugging.", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_SUBCARD).pack(anchor="w", pady=(0, 6))

        sl_row = tk.Frame(sl_card, bg=C_SUBCARD)
        sl_row.pack(fill="x", pady=4)
        self.entry_ota_path = ttk.Entry(sl_row, width=32)
        self.entry_ota_path.pack(side="left", padx=(0, 5), fill="x", expand=True)
        ttk.Button(sl_row, text="Browse", style="Secondary.TButton", command=self.browse_ota).pack(side="left", padx=3)
        ttk.Button(sl_row, text="Sideload OTA", style="Action.TButton", command=self.run_sideload).pack(side="left", padx=3)

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

    # ================= SUPPORTED DEVICES TAB =================

    def _build_tab_devices(self):
        f = self.tab_devices
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)

        header = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))

        tk.Label(header, text="SUPPORTED DEVICE MATRIX", font=("Segoe UI", 11, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w")
        tk.Label(header, text=f"{len(SUPPORTED_DEVICE_CATALOG)} categories | ADB, Fastboot, MTK BROM, EDL & test-point servicing",
                 font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(2, 0))

        search_row = tk.Frame(header, bg=C_CARD)
        search_row.pack(fill="x", pady=(8, 0))
        tk.Label(search_row, text="Search:", font=("Segoe UI", 9, "bold"), fg=C_TEXT_BODY, bg=C_CARD).pack(side="left", padx=(0, 6))
        self.entry_device_search = ttk.Entry(search_row)
        self.entry_device_search.pack(side="left", fill="x", expand=True)
        self.entry_device_search.bind("<KeyRelease>", self._on_device_search)

        body = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        body.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        cols = ("brand", "series", "models", "chipset")
        self.tree_devices = ttk.Treeview(body, columns=cols, show="headings")
        self.tree_devices.heading("brand", text="Brand")
        self.tree_devices.heading("series", text="Series")
        self.tree_devices.heading("models", text="Models")
        self.tree_devices.heading("chipset", text="Chipset")
        self.tree_devices.column("brand", width=100, stretch=False)
        self.tree_devices.column("series", width=190, stretch=False)
        self.tree_devices.column("models", width=360)
        self.tree_devices.column("chipset", width=230)

        vsb = ttk.Scrollbar(body, orient="vertical", command=self.tree_devices.yview)
        self.tree_devices.configure(yscrollcommand=vsb.set)
        self.tree_devices.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._populate_device_tree("")

    def _populate_device_tree(self, query: str):
        self.tree_devices.delete(*self.tree_devices.get_children())
        q = query.strip().lower()
        for cat in SUPPORTED_DEVICE_CATALOG:
            if q and not (
                q in cat["brand"].lower()
                or q in cat["series"].lower()
                or any(q in m.lower() for m in cat["models"])
                or q in cat["chipset"].lower()
            ):
                continue
            self.tree_devices.insert("", "end", values=(
                cat["brand"], cat["series"], ", ".join(cat["models"]), cat["chipset"]
            ))

    def _on_device_search(self, event=None):
        self._populate_device_tree(self.entry_device_search.get())

    # ================= LOGGING & CONSOLE =================

    def log(self, text: str, level: str = "info"):
        """Log a line to BOTH the on-screen console and the session log file."""
        timestamp = time.strftime("[%H:%M:%S] ")
        # 1. Persist to file (synchronous, thread-safe)
        try:
            with self._log_lock:
                if self._log_file is not None:
                    full_ts = time.strftime("%Y-%m-%d %H:%M:%S")
                    self._log_file.write(f"[{full_ts}] [{level.upper():<7}] {text}\n")
                    self._log_file.flush()
        except Exception:
            pass
        # 2. Update console (thread-safe via main loop)
        def _append():
            try:
                self.txt_console.insert(tk.END, timestamp, "muted")
                self.txt_console.insert(tk.END, text + "\n", level)
                self.txt_console.see(tk.END)
                self.txt_console.update_idletasks()
            except Exception:
                pass
        self.root.after(0, _append)

    def _engine_log(self, line: str, level: str = "info"):
        """Callback used by ADB/Fastboot engines to echo real command output."""
        self.log(line, level)

    def clear_log(self):
        self.txt_console.delete("1.0", tk.END)
        self.log("Console cleared (session log file retained).", "muted")

    def copy_log(self):
        text = self.txt_console.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log("All console logs copied to system clipboard!", "success")

    def save_log(self):
        dest = filedialog.asksaveasfilename(
            title="Save Session Log",
            defaultextension=".log",
            initialfile=os.path.basename(self.log_file_path),
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not dest:
            return
        try:
            with self._log_lock:
                if self._log_file is not None:
                    self._log_file.flush()
            text = ""
            try:
                with open(self.log_file_path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except Exception:
                text = self.txt_console.get("1.0", tk.END)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(text)
            self.log(f"Session log exported to: {dest}", "success")
        except Exception as e:
            self.log(f"Failed to save log: {e}", "error")

    def open_logs_folder(self):
        try:
            if os.name == "nt":
                os.startfile(self.logs_dir)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", self.logs_dir])
            else:
                subprocess.run(["xdg-open", self.logs_dir])
            self.log(f"Opened logs folder: {self.logs_dir}", "success")
        except Exception as e:
            self.log(f"Could not open logs folder: {e}", "warning")

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
            self.set_busy(True, f"ACTIVE: {action_name}")
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
            self.log(f"Session log file: {self.log_file_path}", "muted")
            self.log("Verifying Android Debug Bridge & Fastboot binaries...", "info")
            ensure_runtime_dependencies(self.bin_dir, lambda msg: self.log(msg, "info"))
            self.log(driver_install_guidance(), "muted")
            self.log("ADB / Fastboot local engine loaded successfully.", "success")
            self.scan_devices()

        threading.Thread(target=task, daemon=True).start()

    def install_tools_and_drivers(self):
        def task():
            self.log("Installing required tools & drivers...", "info")
            ensure_runtime_dependencies(self.bin_dir, lambda msg: self.log(msg, "info"))
            if platform.system() == "Windows":
                ok, msg = run_windows_driver_installer(self.base_dir)
                self.log(msg, "success" if ok else "warning")
            else:
                self.log(driver_install_guidance(), "info")
            self.log("Dependency install pass finished. Re-scan devices when done.", "success")

        self._run_threaded(task, "Install Tools & Drivers")

    def scan_devices(self):
        def task():
            self.log("Scanning USB bus for ADB, Fastboot, MTK/EDL ports, and hardware devices...", "info")

            if self.simulated_mode.get():
                sim_devs = [
                    "0834212450001234 (TECNO-CN5c - ADB)",
                    "SM-S908B_SIMULATED (Samsung S22 Ultra - ADB)",
                    "REDMI_NOTE_11_SIMULATED (Redmi Note 11 - FASTBOOT)",
                ]
                def _update_sim():
                    self.combo_devices["values"] = sim_devs
                    self.combo_devices.current(0)
                self.root.after(0, _update_sim)
                self._set_conn_state("● SIMULATION", C_WHITE)
                self.log("Simulation Mode Active: showing simulated devices only.", "warning")
                return

            res = run_full_detection(self.adb, self.fastboot, self.mtk)
            sel = selectable_devices(res)
            entries = {d["label"]: d for d in sel}
            labels = list(entries.keys())
            mtk_ports = res.get("mtk_ports", []) or []
            edl_ports = res.get("edl_ports", []) or []
            hw = res.get("hardware", []) or []
            issues = res.get("issues", []) or []

            def _update_ui():
                self.device_entries = entries
                if labels:
                    self.combo_devices["values"] = labels
                    self.combo_devices.current(0)
                else:
                    self.combo_devices["values"] = ["No device found"]
                    self.combo_devices.current(0)

                # Populate the MTK tab port selector with real ports
                port_vals = ["Auto-Detect (Preloader -> BROM crash)"]
                for p in mtk_ports:
                    port_vals.append(f"{p['port']} ({p.get('description') or 'MediaTek Preloader'})")
                for p in edl_ports:
                    port_vals.append(f"{p['port']} (EDL 9008 - {p.get('description') or 'QDLoader'})")
                self.combo_mtk_port["values"] = port_vals
                self.combo_mtk_port.current(0)

            self.root.after(0, _update_ui)

            # ---- logging ----
            try:
                self.log(f"ADB version: {self.adb.get_adb_version()}", "muted")
            except Exception:
                pass
            for d in res["adb"]:
                lvl = "success" if d.get("state") == "device" else "warning"
                self.log(f"ADB: {d['serial']} [{d['state']}]", lvl)
                g = d.get("guidance") or {}
                if g.get("severity") in ("warning", "error"):
                    for f_ in g.get("fix", [])[:2]:
                        self.log(f"   -> {f_}", "info")
            for d in res["fastboot"]:
                self.log(f"FASTBOOT: {d['serial']} [{d.get('mode','fastboot')}]", "success")
            for p in mtk_ports:
                self.log(f"MTK PORT: {p['port']} - {p.get('description') or p.get('hwid','')} (VID {p.get('vid') or '?'})", "success")
            for p in edl_ports:
                self.log(f"EDL PORT: {p['port']} - {p.get('description') or p.get('hwid','')} (VID {p.get('vid') or '?'})", "success")
            for h in hw:
                self.log(f"USB HW BUS (diagnostic only): {h.get('serial','?')} - {h.get('details','')}", "muted")

            if not res["adb"] and not res["fastboot"] and hw:
                self.log(
                    "Device is on the USB bus but NOT in ADB. If the phone is LOCKED (USB debugging can't be enabled), "
                    "use the ⚡ MTK BROM tab — BROM needs no USB debugging and clears FRP/screen lock directly.",
                    "warning"
                )

            # ---- Windows USB driver binding diagnostics (the Camon 50 Pro fix) ----
            usb_driver = res.get("usb_driver", []) or []
            for d in usb_driver:
                state = "ADB OK" if d.get("adb_visible") else "NOT ADB"
                lvl = "success" if d.get("adb_visible") else "warning"
                self.log(
                    f"USB DRIVER: {d.get('hardware_id','?')} [{d.get('description','?')}] -> service={d.get('service') or 'none'} ({state})",
                    lvl
                )

            tecno_driver_issue = any(
                (d.get("vid") or "").upper() == "2E04" and not d.get("adb_visible")
                for d in usb_driver
            )
            tecno_on_bus = any((h.get("vid") or "").upper() == "2E04" for h in hw)
            if tecno_driver_issue or (tecno_on_bus and not res["adb"]):
                hwids = [d.get("hardware_id", "") for d in usb_driver if (d.get("vid") or "").upper() == "2E04"]
                if not hwids:
                    hwids = [f"USB\\VID_{h.get('vid','2E04')}&PID_????&MI_01" for h in hw if (h.get('vid') or '').upper() == '2E04']
                try:
                    inf_path = build_custom_adb_inf(hwids, os.path.join(self.logs_dir, "tecno_adb_driver_custom.inf"))
                    self.log(f"Generated device-specific Tecno ADB driver INF: {inf_path}", "info")
                    self.log("Install it (admin, signature enforcement OFF): pnputil /add-driver \"%s\" /install" % inf_path, "info")
                except Exception as e:
                    self.log(f"Could not generate custom INF: {e}", "error")

            # connection state indicator
            if res["adb"] or res["fastboot"]:
                self._set_conn_state("● CONNECTED", C_GREEN)
            elif mtk_ports or edl_ports:
                self._set_conn_state("● BROM/EDL PORT", C_WHITE)
            else:
                self._set_conn_state("● NOT CONNECTED", C_RED)

            if issues:
                for iss in issues:
                    self.log(f"[GUIDE] {iss.get('title','')}", "warning")
                    for f_ in iss.get("fix", []):
                        self.log(f"   -> {f_}", "info")
            elif labels or mtk_ports or edl_ports:
                self.log(f"Scan complete: {len(res['adb'])} ADB, {len(res['fastboot'])} fastboot, {len(mtk_ports)} MTK port(s), {len(edl_ports)} EDL port(s).", "success")
            else:
                self.log("No devices detected. Open the 'Connection Guide' tab for step-by-step help.", "warning")

        self._run_threaded(task, "USB Device Bus Scan")

    # ================= AUTO-CONNECT (PLUG-IN WATCHER + HANDSHAKE) =================

    def auto_connect(self):
        """Toggle the plug-in watcher: keeps scanning until a device appears,
        then handshakes it (ADB / fastboot / MTK BROM / EDL) and logs every step.
        """
        if self._auto_connect_active:
            self.log("AUTO-CONNECT: stop requested — finishing the current scan...", "info")
            self._auto_connect_stop.set()
            return
        self._auto_connect_active = True
        self._auto_connect_stop = threading.Event()

        def _btn_on():
            self.btn_auto_connect.configure(text="Auto-Connect: ON (stop)")
            self.set_busy(True, "AUTO-CONNECT: WAITING FOR DEVICE")
        self.root.after(0, _btn_on)

        threading.Thread(target=self._auto_connect_watch, daemon=True).start()

    def _finish_auto_connect(self, success: bool):
        self._auto_connect_active = False

        def _btn_off():
            self.btn_auto_connect.configure(text="Auto-Connect")
            self.set_busy(False)
        self.root.after(0, _btn_off)
        if success:
            self.log("AUTO-CONNECT: device connected and ready.", "success")
        else:
            self.log("AUTO-CONNECT: monitoring stopped.", "muted")

    def _auto_connect_watch(self):
        """Background loop: watch the USB bus, handshake whatever shows up, log it."""
        self.log("AUTO-CONNECT: monitoring started — plug in the device now.", "info")
        self.log("  • ADB:        unlock screen + enable USB debugging, then plug in.", "muted")
        self.log("  • FASTBOOT:   Volume Down + power to bootloader, then plug in.", "muted")
        self.log("  • MTK BROM:   power OFF, plug USB with NO buttons (Preloader) - the tool crashes it into BROM. Don't hold Vol Up+Down: that's Recovery.", "muted")
        self._set_conn_state("● LISTENING FOR DEVICE", C_WHITE)

        waited = 0
        while not self._auto_connect_stop.is_set():
            if self.simulated_mode.get():
                # Simulated plug-in: fabricate a BROM handshake clearly labelled as simulation.
                waited += 1
                if waited == 2:
                    self.log("SIMULATION: MediaTek BROM port COM5 appeared (simulated).", "warning")
                    self.log("SIMULATION: Handshake confirmed [0x5F 0xF5 0xAF 0xFA] (simulated).", "warning")
                    self._set_conn_state("● SIMULATION CONNECTED", C_WHITE)
                    self._finish_auto_connect(True)
                    return
                time.sleep(1.0)
                continue

            try:
                res = run_full_detection(self.adb, self.fastboot, self.mtk)
            except Exception as e:
                self.log(f"AUTO-CONNECT: detection error: {e}", "error")
                time.sleep(1.0)
                continue

            adb_devs = res.get("adb") or []
            fb_devs = res.get("fastboot") or []
            mtk_ports = res.get("mtk_ports") or []
            edl_ports = res.get("edl_ports") or []

            # ---- 1. ADB device plugged ----
            if adb_devs:
                d = adb_devs[0]
                serial = d.get("serial", "?")
                self.log(f"DEVICE PLUGGED (ADB): {serial} [{d.get('state','?')}]", "success")
                self.adb.set_active_device(serial)
                self._set_conn_state("● CONNECTED (ADB)", C_GREEN)
                try:
                    info = self.adb.get_device_info()
                    for k in ("brand", "model", "device", "build_id", "android_version", "security_patch", "battery_level", "root_status"):
                        val = (info or {}).get(k)
                        if val and val not in ("Unknown", "N/A", ""):
                            self.log(f"  {k}: {val}", "info")
                except Exception:
                    pass
                self._finish_auto_connect(True)
                return

            # ---- 2. Fastboot device plugged ----
            if fb_devs:
                d = fb_devs[0]
                self.log(f"DEVICE PLUGGED (FASTBOOT): {d.get('serial','?')} [{d.get('mode','fastboot')}]", "success")
                self.fastboot.set_active_device(d.get("serial"))
                self._set_conn_state("● CONNECTED (FASTBOOT)", C_GREEN)
                self._finish_auto_connect(True)
                return

            # ---- 3. MediaTek BROM / Preloader port ----
            if mtk_ports:
                p = mtk_ports[0]
                port = p.get("port")
                self.log(f"DEVICE PLUGGED: MediaTek BROM/Preloader on {port} ({p.get('description') or p.get('hwid','')})", "success")
                self.log(f"Handshaking BootROM on {port}...", "info")
                probe = self.mtk.probe_port(port)
                if probe.get("ok"):
                    self.log(f"HANDSHAKE CONFIRMED on {port} (reply 0x{probe.get('reply','')})", "success")
                    self._set_conn_state("● BROM HANDSHAKE OK", C_GREEN)
                    # read real chip identity
                    hw = self.mtk.read_hw_code(port)
                    sw = self.mtk.read_hw_sw_ver(port)
                    cfg = self.mtk.read_target_config(port)
                    if hw.get("ok") and hw.get("value") is not None:
                        self.log(f"HW Code: 0x{hw['value']:X} ({hw.get('reply','')})", "info")
                    else:
                        self.log(f"HW Code read failed: {hw.get('error','no reply')}", "warning")
                    if sw.get("ok") and sw.get("value") is not None:
                        self.log(f"HW SW Version: 0x{sw['value']:X} ({sw.get('reply','')})", "info")
                    else:
                        self.log(f"HW SW read failed: {sw.get('error','no reply')}", "warning")
                    if cfg.get("ok") and cfg.get("value") is not None:
                        self.log(f"Target Config: 0x{cfg['value']:X} | storage={cfg.get('storage','?')} | SLA={cfg.get('sla')} | DAA={cfg.get('daa')}", "info")
                    else:
                        self.log(f"Target Config: {cfg.get('error','no reply')}", "warning")

                    def _fill_port():
                        vals = [f"{port} (MediaTek BROM — auto-detected)"]
                        for p2 in mtk_ports:
                            vals.append(f"{p2['port']} ({p2.get('description') or 'MediaTek Preloader'})")
                        self.combo_mtk_port["values"] = vals
                        self.combo_mtk_port.current(0)
                    self.root.after(0, _fill_port)

                    self.log("Device CONNECTED and handshaked. Run a BROM operation (FRP wipe / Factory Reset) next.", "success")
                else:
                    self.log(f"HANDSHAKE FAILED on {port}: {probe.get('error','no reply')}", "error")
                    self.log("  → Power the phone fully OFF, then plug into a USB 2.0 port with NO buttons (Preloader mode). Don't hold Vol Up + Vol Down - that boots Recovery.", "warning")
                    self.log("  → If the port shows as unknown, install the MediaTek VCOM (BROM) driver.", "warning")
                    self._set_conn_state("● BROM PORT (retrying handshake)", C_WHITE)
                    time.sleep(1.5)
                    continue
                self._finish_auto_connect(True)
                return

            # ---- 4. Qualcomm EDL port ----
            if edl_ports:
                p = edl_ports[0]
                self.log(f"DEVICE PLUGGED (EDL 9008): {p.get('port')} ({p.get('description') or p.get('hwid','')})", "success")
                self._set_conn_state("● EDL 9008 PORT", C_WHITE)
                self._finish_auto_connect(True)
                return

            # ---- 5. Nothing yet: keep waiting ----
            waited += 1
            if waited == 1:
                self.log("Waiting for device... plug it in now (original cable, USB 2.0 port).", "info")
            elif waited % 5 == 0:
                self.log(f"Still waiting ({waited} checks) — for BROM: power OFF and plug USB with NO buttons; for ADB: USB debugging ON.", "muted")
            time.sleep(1.2)

        self._finish_auto_connect(False)

    def _set_conn_state(self, text: str, color: str):
        def _do():
            try:
                self.lbl_conn_state.configure(text=text, fg=color)
            except Exception:
                pass
        self.root.after(0, _do)

    def _on_device_selected(self, event=None):
        label = self.selected_device.get()
        entries = self.device_entries if isinstance(self.device_entries, dict) else {}
        entry = entries.get(label)
        if not entry:
            return
        kind = entry.get("kind")
        serial = entry.get("serial")
        if kind == "adb":
            self.adb.set_active_device(serial)
            self.fastboot.set_active_device(None)
            self.log(f"Active ADB device set to {serial}", "success")
        elif kind == "fastboot":
            self.fastboot.set_active_device(serial)
            self.adb.set_active_device(None)
            self.log(f"Active FASTBOOT device set to {serial}", "success")

    # ================= CONNECTION GUIDE TAB =================

    def _build_tab_connect(self):
        f = self.tab_connect
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=2)
        f.rowconfigure(0, weight=1)

        # Left column: scenario selector + actions
        left_card = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        left_card.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        tk.Label(left_card, text="DEVICE CONNECTION TUTORIALS", font=("Segoe UI", 10, "bold"), fg=C_WHITE, bg=C_CARD).pack(anchor="w", pady=(0, 4))
        tk.Label(left_card, text="Step-by-step guides for every way a device can connect", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD).pack(anchor="w", pady=(0, 8))

        sc_frame = tk.Frame(left_card, bg=C_SUBCARD, padx=6, pady=6)
        sc_frame.pack(fill="both", expand=True)

        self.lbox_scenarios = tk.Listbox(
            sc_frame, bg=C_SUBCARD, fg=C_TEXT_BODY, selectbackground=C_GRAY_MID,
            selectforeground=C_WHITE, highlightthickness=0, relief="flat",
            font=("Segoe UI", 9), activestyle="none"
        )
        self.lbox_scenarios.pack(fill="both", expand=True, side="left")
        sc_scroll = ttk.Scrollbar(sc_frame, orient="vertical", command=self.lbox_scenarios.yview)
        self.lbox_scenarios.configure(yscrollcommand=sc_scroll.set)
        sc_scroll.pack(side="right", fill="y")

        for sc in CONNECTION_SCENARIOS:
            self.lbox_scenarios.insert(tk.END, f"{sc['icon']}  {sc['title']}")
        self.lbox_scenarios.bind("<<ListboxSelect>>", self._on_scenario_selected)
        self.lbox_scenarios.selection_set(0)

        btn_troubleshoot = ttk.Button(left_card, text="🔍 Troubleshoot My Connection Now", style="Action.TButton", command=self.troubleshoot_connection)
        btn_troubleshoot.pack(fill="x", pady=(8, 0))
        btn_auto = ttk.Button(left_card, text="⚡ Auto-Connect (watch for plug-in + handshake)", style="Action.TButton", command=self.auto_connect)
        btn_auto.pack(fill="x", pady=(4, 0))
        btn_scan = ttk.Button(left_card, text="Scan Devices", style="Secondary.TButton", command=self.scan_devices)
        btn_scan.pack(fill="x", pady=(4, 0))
        btn_install = ttk.Button(left_card, text="⬇ Install Tools & Drivers", style="Secondary.TButton", command=self.install_tools_and_drivers)
        btn_install.pack(fill="x", pady=(4, 0))

        # Right column: scenario detail
        right_card = tk.Frame(f, bg=C_CARD, padx=15, pady=12)
        right_card.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        self.lbl_scenario_title = tk.Label(right_card, text="", font=("Segoe UI", 11, "bold"), fg=C_WHITE, bg=C_CARD, anchor="w")
        self.lbl_scenario_title.pack(fill="x")
        self.lbl_scenario_when = tk.Label(right_card, text="", font=("Segoe UI", 8), fg=C_TEXT_MUTED, bg=C_CARD, anchor="w", justify="left")
        self.lbl_scenario_when.pack(fill="x", pady=(0, 6))

        self.txt_scenario = tk.Text(right_card, bg=C_SUBCARD, fg=C_TEXT_BODY, font=("Segoe UI", 9), wrap="word", relief="flat", padx=8, pady=6)
        self.txt_scenario.pack(fill="both", expand=True)

        self._render_scenario(0)

    def _on_scenario_selected(self, event=None):
        sel = self.lbox_scenarios.curselection()
        if sel:
            self._render_scenario(sel[0])

    def _render_scenario(self, index: int):
        if index < 0 or index >= len(CONNECTION_SCENARIOS):
            return
        sc = CONNECTION_SCENARIOS[index]
        self.lbl_scenario_title.configure(text=f"{sc['icon']} {sc['title']}   [{sc['mode']}]")
        self.lbl_scenario_when.configure(text=f"When to use: {sc['use_when']}")

        lines = ["PREREQUISITES:"]
        for p in sc.get("prerequisites", []):
            lines.append(f"  • {p}")
        lines.append("")
        lines.append("STEP-BY-STEP:")
        for i, s in enumerate(sc.get("steps", []), 1):
            lines.append(f"  {i}. {s}")
        lines.append("")
        lines.append(f"VERIFY: {sc.get('verify', '')}")
        if sc.get("failures"):
            lines.append("")
            lines.append("COMMON FAILURES & FIXES:")
            for fl in sc["failures"]:
                lines.append(f"  ✖ {fl['symptom']}")
                lines.append(f"      → {fl['fix']}")

        self.txt_scenario.delete("1.0", tk.END)
        self.txt_scenario.insert("1.0", "\n".join(lines))

    def troubleshoot_connection(self):
        def task():
            self.log("Running connection diagnostics...", "info")
            res = run_full_detection(self.adb, self.fastboot, self.mtk)
            issues = res.get("issues", []) or []
            if issues:
                for iss in issues:
                    self.log(f"[DIAG] {iss.get('title','')}", "warning")
                    if iss.get("cause"):
                        self.log(f"   cause: {iss['cause']}", "muted")
                    for f_ in iss.get("fix", []):
                        self.log(f"   -> {f_}", "info")
            else:
                self.log("No connection problems detected — device looks healthy.", "success")

        self._run_threaded(task, "Connection Troubleshoot")

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
            ok, partitions, msg = self.payload_extractor.inspect_payload(path)
            if not ok:
                self.log(msg, "error")
                return
            self.log(msg, "success")
            self.log(f"Partitions found in payload: {', '.join(partitions)}", "info")

            out_folder = os.path.join(self.base_dir, "extracted")
            try:
                extracted = self.payload_extractor.extract_critical_partitions(path, out_folder)
                for f in extracted:
                    self.log(f"Extracted: {f}", "success")
                self.log(f"Extraction complete -> {out_folder}", "success")
            except Exception as e:
                self.log(f"Extraction failed: {e}", "error")

        self._run_threaded(task, "Extract OTA payload.bin")

    def bypass_transsion_mdm(self):
        if not messagebox.askyesno("Confirm MDM Bypass", "Disable Transsion HiOS Carlcare, PalmPay, and PayJoy lock agents?"):
            return

        def task():
            self.log("Starting Transsion HiOS MDM & Financing Lock Remover...", "info")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log("[OK] Disabled com.transsion.palmpay (PalmPay Framework)", "success")
                self.log("[OK] Disabled com.transsion.carlcare (Carlcare MDM Agent)", "success")
                self.log("[OK] Disabled com.payjoy.access (PayJoy Device Lock)", "success")
                self.log("[OK] Disabled com.transsion.magicshow (Remote Provisioning)", "success")
                self.log("[OK] Injected: settings put global device_provisioned 1", "success")
                self.log("[OK] Injected: settings put secure user_setup_complete 1", "success")
                self.log("HiOS Financing and MDM background locks successfully bypassed!", "success")
                return

            for pkg, ok, desc in self.transsion_mdm.disable_mdm_services():
                lvl = "success" if ok else "warning"
                self.log(f"[{'OK' if ok else 'SKIP'}] {pkg} - {desc}", lvl)
            for line in self.transsion_mdm.freeze_provisioning_intents():
                self.log(line, "success" if line.startswith("[OK]") else "info")
            self.log("HiOS Financing and MDM background locks bypass process complete.", "success")

        self._run_threaded(task, "Freeze Transsion MDM & PayJoy")

    def lock_provisioning(self):
        def task():
            self.log("Locking Android setup wizard provisioning state...", "info")
            if self.simulated_mode.get():
                time.sleep(0.6)
                self.log("user_setup_complete set to 1", "success")
                self.log("device_provisioned set to 1", "success")
                self.log("Provisioning state locked. Device will skip initial setup wizard on boot.", "success")
                return
            c1, _, e1 = self.adb.run_cmd(["shell", "settings", "put", "global", "device_provisioned", "1"])
            c2, _, e2 = self.adb.run_cmd(["shell", "settings", "put", "secure", "user_setup_complete", "1"])
            if c1 == 0 and c2 == 0:
                self.log("device_provisioned=1 and user_setup_complete=1 applied via ADB.", "success")
            else:
                self.log(f"Provisioning write failed: {e1 or e2 or 'device not reachable'}", "error")

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
                self.log(f"[OK] Revoked AppOps SYSTEM_ALERT_WINDOW (Lockscreen overlay killed)", "success")
                self.log(f"[OK] Revoked AppOps RUN_IN_BACKGROUND & START_FOREGROUND", "success")
                self.log(f"[OK] Revoked AppOps BIND_ACCESSIBILITY_SERVICE", "success")
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
        if not messagebox.askyesno("Confirm Erase", f"Proceed with a REAL MediaTek BROM wipe of '{part}' via mtkclient?\n\n"
                                                    "This will erase data on the phone (screen locks / FRP)."):
            return

        cmd_map = {
            "frp": ["e", "frp"],
            "userdata": ["e", "metadata,userdata,md_udc"],
            "metadata": ["e", "metadata,md_udc"],
            "misc": ["e", "misc"],
        }
        args = cmd_map.get(part, ["e", part])

        def task():
            self.log(f"MediaTek BROM wipe of '{part}' (Camon 50 Pro 4G · MT6789) via mtkclient...", "info")
            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log(f"Simulation Mode: no real erase. Real command:  mtk {' '.join(args)}", "warning")
                return
            if not self.mtk.mtkclient_available():
                self.log("mtkclient is NOT installed — no real erase can run.", "error")
                self.log("Install (free):  pip install mtkclient", "warning")
                return
            self.log("Power the phone OFF, then plug USB into a USB 2.0 port with NO buttons (Preloader) - do NOT hold Vol Up + Vol Down (that boots Recovery).", "warning")
            ok, tail = self.mtk.run_mtkclient(args, log_cb=lambda line, lvl="info": self.log(line, lvl))
            if ok:
                self.log(f"Wipe complete — {tail}", "success")
            else:
                self.log(f"Wipe failed: {tail}", "error")
                self.log("Check: MTK VCOM driver installed, USB 2.0 port, phone fully OFF, and plug with NO buttons (Preloader -> auto-crash to BROM).", "warning")

        self._run_threaded(task, f"Preloader BROM Wipe ({part})")

    def _mtk_resolve_port(self):
        """Resolve an MTK BROM/Preloader port from the UI selection or auto-detect.

        Returns the port string (e.g. 'COM5') or None if none found.
        """
        sel_port = self.combo_mtk_port.get()
        if sel_port and (sel_port.startswith("COM") or sel_port.startswith("/dev")):
            return sel_port.split()[0]
        detected = self.mtk.detect_ports().get("mtk", [])
        if detected:
            p = detected[0]
            self.log(f"Auto-detected MediaTek port: {p['port']} ({p.get('description','')})", "info")
            return p["port"]
        return None

    def mtk_detect_handshake(self):
        """Standalone: find the MTK BROM/Preloader port and perform the real handshake.

        This is the path for a LOCKED phone where USB debugging can't be enabled —
        BROM runs before Android and needs no ADB.
        """
        def task():
            self.log("Scanning for MediaTek Preloader/BROM port (no ADB needed)...", "info")
            if self.simulated_mode.get():
                self.log("Simulation: COM5 (MediaTek Preloader) detected.", "warning")
                return
            detected = self.mtk.detect_ports().get("mtk", [])
            if not detected:
                self.log("No MediaTek BROM/Preloader port found.", "warning")
                self.log("Power the phone OFF, then plug USB with NO buttons (Preloader mode). Don't hold Vol Up + Vol Down - that boots Recovery.", "warning")
                self.log("If still nothing, install the MTK VCOM driver: Connection Guide -> Install Tools & Drivers.", "warning")
                return
            p = detected[0]
            self.log(f"Found MediaTek port: {p['port']} ({p.get('description') or p.get('hwid','')})", "success")
            probe = self.mtk.probe_port(p["port"])
            if probe.get("ok"):
                self.log(f"Handshake CONFIRMED on {p['port']} (reply {probe.get('reply','')})", "success")
                self.log("Device is in BROM mode and reachable. Run a BROM operation (FRP / userdata wipe) next.", "success")
            else:
                self.log(f"Handshake on {p['port']}: {probe.get('error','no reply')}", "error")

        self._run_threaded(task, "Detect BROM Port & Handshake")

    def brom_read_info(self):
        """Read hardware code / SW version / target config from BROM (no debugging needed)."""
        def task():
            self.log("Reading MediaTek BROM chip info (no USB debugging needed)...", "info")
            if self.simulated_mode.get():
                self.log("Simulation: HW code 0x0788, SW ver 0x0000, UFS, SLA+DAA.", "warning")
                return
            port = self._mtk_resolve_port()
            if not port:
                self.log("No MediaTek BROM/Preloader port found. Power OFF, plug USB with NO buttons (Preloader). Don't hold Vol Up + Vol Down - that boots Recovery.", "warning")
                return
            hw = self.mtk.read_hw_code(port)
            sw = self.mtk.read_hw_sw_ver(port)
            cfg = self.mtk.read_target_config(port)
            self.log(f"HW Code: {hw.get('reply','-')}" + (f" (0x{hw['value']:X})" if hw.get("ok") and hw.get("value") is not None else f" — {hw.get('error','no reply')}"), "success" if hw.get("ok") else "warning")
            self.log(f"HW SW Version: {sw.get('reply','-')}" + (f" (0x{sw['value']:X})" if sw.get("ok") and sw.get("value") is not None else f" — {sw.get('error','no reply')}"), "success" if sw.get("ok") else "warning")
            if cfg.get("ok") and cfg.get("value") is not None:
                self.log(f"Target Config: 0x{cfg['value']:X} | Storage: {cfg.get('storage','?')} | SLA: {cfg.get('sla')} | DAA: {cfg.get('daa')}", "info")
            else:
                self.log(f"Target Config read failed: {cfg.get('error','no reply')}", "warning")

        self._run_threaded(task, "Read BROM Chip Info")

    def browse_da(self):
        f = filedialog.askopenfilename(filetypes=[("Download Agent", "*.bin *.da"), ("All Files", "*.*")])
        if f:
            self.entry_da_path.delete(0, tk.END)
            self.entry_da_path.insert(0, f)

    def run_send_da(self):
        da_path = self.entry_da_path.get().strip()
        if not da_path:
            messagebox.showerror("Missing File", "Select a Download Agent (DA) binary for this chipset first.")
            return

        def task():
            self.log(f"Uploading Download Agent: {os.path.basename(da_path)}...", "warning")
            self.log("NOTE: the chip will only accept a DA signed for this SoC and an SLA/DAA bypass. Results are reported verbatim.", "info")
            if self.simulated_mode.get():
                self.log("Simulation: DA uploaded and jumped.", "warning")
                return
            port = self._mtk_resolve_port()
            if not port:
                self.log("No MediaTek BROM/Preloader port found.", "warning")
                return
            res = self.mtk.send_da(da_path, port)
            for line in res.get("log", []):
                self.log(line, "info")
            if res.get("ok"):
                self.log(f"DA uploaded ({res.get('bytes', 0)} bytes) and JUMP_DA issued on {port}.", "success")
            else:
                self.log(f"DA upload failed: {res.get('error','unknown error')}", "error")
                self.log("Typical causes: SLA/DAA lock (needs a per-SoC auth-bypass payload), or the DA isn't signed for this chip.", "warning")

        self._run_threaded(task, "Upload DA to BROM")

    def run_selected_mtk_brom(self):
        op = self.mtk_op_var.get()
        soc_full = self.combo_mtk_soc.get()
        soc = soc_full.split()[0] if soc_full else "MT6789"

        # Map each BROM action to a real mtkclient command (the proven free path).
        op_commands = {
            "frp": ["e", "frp"],
            "userdata": ["e", "metadata,userdata,md_udc"],
            "auth_bypass": ["payload"],
            "nvram": ["r", "nvram", "nvram_backup.bin"],
            "nvdata": ["r", "nvdata", "nvdata_backup.bin"],
        }
        op_desc = {
            "frp": "wipe FRP (Google account lock)",
            "userdata": "factory reset + clear all screen locks",
            "auth_bypass": "run the SLA/DAA bypass payload",
            "nvram": "backup nvram (IMEI / radio calibration)",
            "nvdata": "backup nvdata (dynamic calibration)",
        }

        def task():
            self.log(f"MediaTek BROM operation: {op_desc.get(op, op)} — chip {soc}", "info")

            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log("Simulation Mode: no real device operation was performed.", "warning")
                self.log(f"Real command would be:  mtk {' '.join(op_commands.get(op, ['e','frp']))}", "info")
                return

            if not self.mtk.mtkclient_available():
                self.log("mtkclient is NOT installed — the built-in formatter cannot erase partitions on its own.", "error")
                self.log("It is the free tool that performs the real MediaTek exploit. Install it:", "warning")
                self.log("    pip install mtkclient", "warning")
                self.log("  or: git clone https://github.com/bkerler/mtkclient && pip install -r requirements.txt", "warning")
                self.log("For the Camon 50 Pro 4G (MT6789 / Helio G200) no auth file is needed — mtkclient works out of the box.", "info")
                return

            args = list(op_commands.get(op, ["e", "frp"]))
            if soc.startswith("MT6878"):
                self.log("MT6878 (Dimensity 7300/7400) needs a signed DA + auth file on protected units.", "warning")
                da = (self.entry_da_path.get() or "").strip()
                if da:
                    args += ["--loader", da]
                else:
                    self.log("No DA selected — a protected MT6878 will stop at 'Auth file is required'.", "warning")

            self.log("Connecting via mtkclient — power the phone OFF, then plug USB with NO buttons (Preloader; mtkclient crashes it into BROM). Don't hold Vol Up + Vol Down - that boots Recovery.", "warning")
            ok, tail = self.mtk.run_mtkclient(args, log_cb=lambda line, lvl="info": self.log(line, lvl))
            if ok:
                self.log(f"mtkclient finished OK — {tail}", "success")
                self.log("If the phone was lock-screen protected, it will now boot to setup (data wiped).", "success")
            else:
                self.log(f"mtkclient did not complete: {tail}", "error")
                self.log("Check: MTK VCOM driver installed, USB 2.0 port, phone fully OFF, buttons held until handshake.", "warning")
                self.log("Some devices need preloader mode instead of BROM: connect WITHOUT holding buttons, or use 'mtk crash'.", "warning")

        self._run_threaded(task, f"MTK BROM {soc} ({op})")

    def backup_nv_partition(self, part: str):
        dest_dir = filedialog.askdirectory(title="Select Destination Folder for Calibration Backup")
        if not dest_dir:
            return

        def task():
            self.log(f"Checking Transsion / MTK baseband partition '{part}'...", "info")
            if self.simulated_mode.get():
                time.sleep(0.8)
                out_file = os.path.join(dest_dir, f"Tecno_Camon50Pro_{part}.img")
                self.log(f"Tecno Camon 50 Pro modem calibration '{part}' backed up to: {out_file}", "success")
                return
            ok, msg = self.efs.backup_partition(part, dest_dir)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task, f"Backup NV Calibration ({part})")

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
            self.log("Checking su binary and root privileges...", "info")
            if self.simulated_mode.get():
                time.sleep(0.5)
                self.log("su binary: not found in /system/bin or /system/xbin", "info")
                self.log("Magisk Status: Not installed. Patch init_boot.img to root.", "warning")
                return
            ok, msg = self.root_engine.check_root_status()
            self.log(msg, "success" if ok else "info")

        self._run_threaded(task, "Check Root & Magisk Status")

    def check_security(self):
        def task():
            self.log("Querying bootloader lock and verified-boot flags...", "info")
            if self.simulated_mode.get():
                time.sleep(0.5)
                self.log("Bootloader Locked: YES", "info")
                self.log("Warranty Bit / Tamper Flag: 0x0", "info")
                self.log("Android Verified Boot (AVB 2.0): ACTIVE", "info")
                return
            props = {
                "verifiedbootstate": "ro.boot.verifiedbootstate",
                "vbmeta_state": "ro.boot.vbmeta.device_state",
                "bootloader_lock": "ro.boot.flash.locked",
                "warranty_bit": "ro.warranty_bit",
            }
            any_found = False
            for label, prop in props.items():
                code, out, _ = self.adb.run_cmd(["shell", "getprop", prop])
                val = out.strip() if code == 0 else ""
                if val:
                    any_found = True
                    self.log(f"{label}: {val}", "info")
            if not any_found:
                self.log("Could not read security props (device locked or no ADB). Check in Fastboot via 'fastboot getvar all'.", "warning")

        self._run_threaded(task, "Check Knox & Verified Boot")

    def dump_battery(self):
        def task():
            self.log("Dumping power subsystem stats...", "info")
            if self.simulated_mode.get():
                time.sleep(0.5)
                self.log("Battery: AC: false, USB: true, Level: 96%, Health: Good, Temp: 27.2 C", "success")
                return
            code, out, _ = self.adb.run_cmd(["shell", "dumpsys", "battery"])
            if code != 0 or not out:
                self.log("Battery dump failed (device not reachable).", "error")
                return
            interesting = ("level:", "health:", "temperature:", "AC powered:", "USB powered:", "status:")
            for line in out.splitlines():
                s = line.strip()
                if any(s.startswith(k) for k in interesting):
                    self.log(s, "info")

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

        self._run_threaded(task, f"Reboot Device -> {target or normal}")

    # ================= FRP OPERATIONS =================

    def reset_frp_fastboot(self):
        if not messagebox.askyesno("Confirm FRP Reset", "Universal Fastboot FRP will erase 'config', 'frp', and 'persistent' partitions.\nProceed?"):
            return

        def task():
            self.log("Executing Universal Fastboot FRP Reset...", "warning")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log("[FASTBOOT] Erasing partition 'frp'... OKAY [0.035s]", "success")
                self.log("[FASTBOOT] Erasing partition 'config'... OKAY [0.021s]", "success")
                self.log("[FASTBOOT] Erasing partition 'persistent'... OKAY [0.040s]", "success")
                self.log("Universal Fastboot FRP Reset completed successfully!", "success")
                return
            for part, ok, msg in self.frp.reset_frp_fastboot():
                self.log(f"[FASTBOOT] {msg}", "success" if ok else "error")

        self._run_threaded(task, "Universal Fastboot FRP Reset")

    def frp_samsung_test_mode(self):
        def task():
            self.log("Starting Samsung Test Mode FRP Bypass (*#0*#)...", "info")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log("Sending AT modem command to enable ADB USB debugging...", "info")
                time.sleep(0.8)
                self.log("USB Debugging dialog accepted by device.", "success")
                self.log("FRP Account successfully removed! Rebooting device...", "success")
                return
            ok, logs = self.samsung_modem.send_at_sequence()
            for line in logs:
                self.log(line, "info" if "->" in line else "warning")
            if ok:
                self.log("AT sequence sent. Watch the phone for the 'Allow USB debugging' prompt, then run 'Bypass Setup Wizard'.", "success")
            else:
                self.log("Samsung modem AT channel unavailable. Open *#0*# manually, then use 'Bypass Setup Wizard' once ADB is authorized.", "warning")

        self._run_threaded(task, "Samsung *#0*# Test Mode FRP")

    def bypass_setup_wizard(self):
        def task():
            self.log("Injecting Setup Wizard completion flags via ADB...", "info")
            if self.simulated_mode.get():
                time.sleep(0.6)
                self.log("user_setup_complete set to 1", "success")
                self.log("device_provisioned set to 1", "success")
                self.log("Setup wizard bypassed successfully!", "success")
                return
            ok, logs = self.frp.bypass_frp_adb_setupwizard()
            for line in logs:
                self.log(line, "success" if line.startswith("[OK]") else "warning")
            self.log("Setup wizard bypass complete." if ok else "Setup wizard bypass failed — device may need USB debugging enabled.", "success" if ok else "error")

        self._run_threaded(task, "Bypass Android Setup Wizard")

    def remove_screen_lock(self):
        if not messagebox.askyesno("Confirm Lock Reset", "Removing screen lock files requires Root or TWRP Recovery mode.\nProceed?"):
            return

        def task():
            self.log("Searching and removing screen lock key databases...", "warning")
            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log("[DELETED] /data/system/gesture.key", "success")
                self.log("[DELETED] /data/system/password.key", "success")
                self.log("[DELETED] /data/system/locksettings.db", "success")
                self.log("Pattern/PIN lock successfully cleared! Reboot phone now.", "success")
                return
            ok, logs = self.frp.remove_screen_lock_rooted()
            for line in logs:
                self.log(line, "success" if line.startswith("[DELETED]") else "warning")
            self.log("Lock files cleared. Reboot the phone." if ok else "Could not remove lock files (no root/TWRP shell). Use MTK BROM on a locked Tecno.", "success" if ok else "error")

        self._run_threaded(task, "Remove Lockscreen DB (TWRP/Root)")

    # ================= RECOVERY SIDELOAD (no USB debugging needed) =================

    def browse_ota(self):
        f = filedialog.askopenfilename(filetypes=[("OTA / Update ZIP", "*.zip"), ("All Files", "*.*")])
        if f:
            self.entry_ota_path.delete(0, tk.END)
            self.entry_ota_path.insert(0, f)

    def run_sideload(self):
        ota = self.entry_ota_path.get().strip()
        if not ota:
            messagebox.showerror("Missing File", "Select an OTA/update ZIP to sideload first.")
            return

        def task():
            self.log(f"Sideloading OTA: {os.path.basename(ota)}...", "info")
            self.log("Recovery sideload works with USB debugging DISABLED — boot to recovery -> 'Apply update from ADB'.", "info")
            if self.simulated_mode.get():
                time.sleep(1.2)
                self.log("Serving: 100% | Total xfer: 2.10x", "success")
                self.log("Install from ADB complete.", "success")
                return
            ok, msg = self.adb.sideload_ota(ota)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task, "ADB Sideload OTA")

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
            if self.simulated_mode.get():
                time.sleep(1)
                self.log(f"Sending '{part}' (32768 KB)... OKAY [0.65s]", "info")
                self.log(f"Writing '{part}'... OKAY [0.24s]", "info")
                self.log(f"Finished flashing {part} successfully.", "success")
                return
            ok, msg = self.fastboot.flash_partition(part, img_path)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task, f"Fastboot Flash Image ({part})")

    def erase_fb_part(self, part: str):
        if not messagebox.askyesno("Confirm Erase", f"Erase partition '{part}'? This cannot be undone."):
            return

        def task():
            self.log(f"Erasing partition '{part}' in Fastboot...", "warning")
            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log(f"Erasing '{part}'... OKAY", "success")
                return
            ok, msg = self.fastboot.erase_partition(part)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task, f"Fastboot Erase ({part})")

    def unlock_bootloader(self):
        if not messagebox.askyesno("Warning", "Unlocking bootloader will WIPE ALL DATA on modern Android devices.\nProceed?"):
            return

        def task():
            self.log("Issuing Bootloader Unlock command: fastboot flashing unlock...", "warning")
            if self.simulated_mode.get():
                time.sleep(1)
                self.log("Prompt shown on phone display. Press Volume Up to confirm unlock.", "warning")
                self.log("Bootloader unlocked successfully.", "success")
                return
            ok, msg = self.fastboot.unlock_bootloader()
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task, "Unlock Bootloader (flashing unlock)")

    def lock_bootloader(self):
        def task():
            self.log("Issuing Bootloader Lock command: fastboot flashing lock...", "info")
            if self.simulated_mode.get():
                time.sleep(0.8)
                self.log("Command: fastboot flashing lock... OKAY", "success")
                return
            ok, msg = self.fastboot.lock_bootloader()
            self.log(msg, "success" if ok else "error")

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
            if self.simulated_mode.get():
                time.sleep(1.2)
                self.log(f"Success: {os.path.basename(apk)} installed.", "success")
                return
            ok, msg = self.adb.install_apk(apk, grant_permissions=True)
            self.log(msg, "success" if ok else "error")

        self._run_threaded(task, "Install APK File")

    def run_debloat(self, brand: str):
        packages = BLOATWARE_PRESETS.get(brand, [])
        if not packages:
            return

        if not messagebox.askyesno("Confirm Debloat", f"Disable {len(packages)} bloatware packages for {brand}?"):
            return

        def task():
            self.log(f"Starting bloatware cleaner for {brand} ({len(packages)} targets)...", "info")
            if self.simulated_mode.get():
                for pkg in packages:
                    time.sleep(0.1)
                    self.log(f"Disabled: {pkg}", "info")
                self.log(f"Debloat complete: {len(packages)} packages disabled.", "success")
                return
            done = 0
            for pkg in packages:
                ok, msg = self.adb.disable_package(pkg)
                self.log(msg, "success" if ok else "warning")
                done += 1 if ok else 0
            self.log(f"Debloat complete: {done}/{len(packages)} packages disabled.", "success")

        self._run_threaded(task, f"Debloat OEM Profile ({brand})")

    def disable_custom_package(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg:
            return

        def task():
            self.log(f"Disabling package: {pkg}...", "info")
            if self.simulated_mode.get():
                time.sleep(0.5)
                self.log(f"Disabled {pkg}", "success")
                return
            ok, msg = self.adb.disable_package(pkg)
            self.log(msg, "success" if ok else "warning")

        self._run_threaded(task, f"Disable Package ({pkg})")

    def uninstall_custom_package(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg:
            return

        def task():
            self.log(f"Uninstalling package for user 0: {pkg}...", "warning")
            if self.simulated_mode.get():
                time.sleep(0.5)
                self.log(f"Uninstalled {pkg}", "success")
                return
            ok, msg = self.adb.uninstall_package(pkg, keep_data=False)
            self.log(msg, "success" if ok else "warning")

        self._run_threaded(task, f"Uninstall Package ({pkg})")


def main():
    root = tk.Tk()
    app = AndroidMultiToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
