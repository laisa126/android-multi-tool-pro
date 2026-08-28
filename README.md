# Android Multi-Tool Pro (Standalone Windows EXE & Source)

**Android Multi-Tool Pro** is a modern, modular PC utility engineered for mobile phone technicians, hardware repair labs, and Android developers. It delivers high-speed device diagnostics, multi-mode reboot sequences, universal FRP resets, bootloader flashing, and vendor bloatware removal.

---

## 🚀 Key Feature Matrix

| Category | Features Included |
| :--- | :--- |
| **📱 Device Diagnostics** | Read Brand, Model, Codename, Android OS version, SDK Level, Security Patch date, Build Display ID, CPU ABI, Battery health & voltage telemetry, Root status check. |
| **🔄 Power & Reboot** | Normal System Reboot, Recovery Mode (TWRP/Stock), Fastboot/Bootloader, Fastbootd (Dynamic Partitions), Qualcomm EDL Mode (HS-USB 9008), Samsung Download / Odin Mode, ADB Sideload, Clean Power Off. |
| **🔓 FRP & Screen Lock** | Samsung Test Mode (`*#0*#`) ADB authorization exploit, Universal Fastboot FRP partition wipe (`config`, `frp`, `persistent`, `devinfo`), Setup Wizard bypass injector (`user_setup_complete = 1`), Pattern/PIN/Password key database cleaner (Root/TWRP), MTP YouTube/Chrome browser intent push. |
| **⚡ Fastboot Flasher** | Modern OEM Bootloader Unlock (`flashing unlock` & `oem unlock`), Bootloader Relock, Partition Flasher (`boot`, `recovery`, `vbmeta`, `super`, `system`, `vendor`, `dtbo`), Fastboot Userdata & Cache format. |
| **📦 Debloat & Apps** | One-click OEM bloatware removers for Samsung OneUI, Xiaomi MIUI/HyperOS, Transsion (Tecno/Infinix/itel), and BBK (Oppo/Realme/Vivo). Direct APK installer and custom package disabler. |
| **🛠️ Hardware Test-Points** | Interactive reference database for Qualcomm Snapdragon EDL 9008 and MediaTek BROM/Preloader test points. |
| **💻 Terminal Log** | Real-time ANSI color-coded technician console with timestamps, command verification, and error handling. |

---

## 📂 Project Architecture

```text
android-multi-tool/
├── bin/                             # Embedded official binaries & DLLs
│   ├── adb.exe                      # Windows ADB daemon
│   ├── fastboot.exe                 # Windows Fastboot flasher
│   ├── AdbWinApi.dll                # Windows USB driver DLL
│   ├── AdbWinUsbApi.dll             # Windows USB bridge DLL
│   ├── libwinpthread-1.dll          # Win32 threading runtime
│   ├── adb                          # Linux/Unix ADB executable
│   └── fastboot                     # Linux/Unix Fastboot executable
├── core/                            # Core protocol engines
│   ├── __init__.py
│   ├── adb_engine.py                # ADB socket wrapper & property parser
│   ├── fastboot_engine.py           # Fastboot partition flasher & variables
│   ├── frp_engine.py                # FRP exploit & lock removal logic
│   ├── device_profiles.py           # OEM bloatware packages & test point data
│   └── downloader.py                # Automatic Google platform-tools fetcher
├── web/                             # Live Interactive Web Suite
│   ├── index.html                   # Dark-themed technician GUI
│   └── server.py                    # Multi-tool API backend (Port 3000)
├── app_gui.py                       # Native Desktop GUI (Tkinter + ttk)
├── build_exe.py                     # PyInstaller automated build pipeline
├── AndroidMultiTool.spec            # PyInstaller spec file for Windows
├── download_windows_binaries.py     # Binary downloader utility
├── build.bat                        # 1-Click Windows build script
└── README.md                        # Documentation & Technician Guide
```

---

## 🛠️ How to Compile into `AndroidMultiTool.exe` on Windows

You can build a single, portable, standalone `.exe` that runs on Windows 10/11 without needing Python or external SDKs installed on the client machine:

### Option 1: One-Click Batch Script
1. Download or copy the `android-multi-tool` folder to your Windows PC.
2. Double-click **`build.bat`**.
3. The script will:
   - Check and configure Python.
   - Install `pyinstaller`.
   - Verify official Google `adb.exe`, `fastboot.exe`, and WinUSB DLLs in `bin/`.
   - Compile everything into a standalone executable.
4. Your finished executable will appear at:
   ```text
   dist\AndroidMultiTool.exe
   ```

### Option 2: Manual Terminal Build
```cmd
# 1. Navigate to the project directory:
cd android-multi-tool

# 2. Install PyInstaller:
pip install pyinstaller

# 3. Build using the spec file:
python -m PyInstaller --clean --noconfirm AndroidMultiTool.spec
```

The output `dist\AndroidMultiTool.exe` embeds `adb.exe`, `fastboot.exe`, and all dependencies into a single file.

---

## 🔌 Required PC Drivers for Technicians

To service phones via this tool, ensure the proper Windows USB drivers are installed:
1. **Google Universal ADB / Fastboot Driver**: For USB Debugging and Fastboot modes.
2. **Samsung USB Driver for Mobile Phones**: For Galaxy MTP, ADB, and Download Mode.
3. **Qualcomm HS-USB QDLoader 9008 Driver**: Required for EDL test-point unbricking.
4. **MediaTek (MTK) VCOM Driver**: Required for BROM / Preloader format & flashing.
