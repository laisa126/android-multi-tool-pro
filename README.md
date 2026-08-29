# Android Multi-Tool Pro (Standalone Windows EXE & Web Suite)
### Specialized for Tecno Camon 50 Pro (`TECNO-CN5c`), Samsung, Xiaomi & Multi-Brand Servicing

**Android Multi-Tool Pro (AMT Pro)** is a professional-grade, offline-capable hardware and firmware utility engineered for mobile technicians, GSM repair labs, and power users. Designed with a strict 10-color monochrome high-contrast interface, it features full offline servicing for the **Tecno Camon 50 Pro 5G (`TECNO-CN5c`)** powered by the **MediaTek Dimensity 7400 Ultimate (MT6878)** on **HiOS 16 / Android 16**.

---

## ⚡ How to Install as an App on PC

### Method 1: One-Click Windows Desktop Installer (Recommended)
1. Download the latest release package: `AndroidMultiTool-Windows-v2.5.zip`.
2. Extract the ZIP archive on your PC.
3. Right-click **`install_app_on_pc.bat`** and click **Run as administrator** (or double-click it).
4. The installer automatically:
   * Installs the app to `%LOCALAPPDATA%\Programs\AndroidMultiToolPro`.
   * Places an **Android Multi-Tool Pro** icon on your **Windows Desktop**.
   * Creates a **Windows Start Menu** shortcut (search *"Android Multi-Tool"* in Windows).
   * Registers the app in **Windows Settings $\rightarrow$ Installed Apps** (Control Panel).
   * Auto-configures the Transsion ADB Vendor ID (`0x2E04`) so Tecno devices are detected.

### Method 2: Browser Desktop Standalone App (Chrome / Edge PWA)
1. Launch the web suite in Google Chrome, Microsoft Edge, or Brave (`http://localhost:3000`).
2. Click **`Install as PC App`** on the top bar (or click the **Install** icon in your browser's address bar).
3. The tool installs as a native, borderless desktop application, pinned to your Windows Taskbar.

---

## 📱 Tecno Camon 50 Pro 5G (`TECNO-CN5c`) Features

* **Admin App Security Plugin Remover**:
  * Strips `SYSTEM_ALERT_WINDOW`, `RUN_IN_BACKGROUND`, and accessibility hijacking via AppOps to immediately kill persistent lockscreen overlay banners.
  * Deactivates registered Device Administrators via `dpm remove-active-admin` and clears credential caches via `pm clear`.
  * Purges `/data/system/device_owner_2.xml` and `/data/system/device_policies.xml` for permanent clean removal.
* **HiOS 16 MDM & Financing Lock Freeze**:
  * Freezes Carlcare MDM (`com.transsion.carlcare`), PalmPay (`com.transsion.palmpay`), PayJoy (`com.payjoy.access`), and `com.transsion.magicshow`.
  * Injects `device_provisioned = 1` and `user_setup_complete = 1` to prevent cloud zero-touch re-enrollment.
* **Stock ROM `payload.bin` Extractor**:
  * Decompresses `init_boot.img` (Android 15/16 Kernel Ramdisk for Magisk root), `vbmeta.img` (AVB 2.0 verification), and `boot.img` directly from official Transsion OTA archives.
* **Preloader DAA / SLA Bypass & BROM Memory Format**:
  * Direct memory formatting of `frp` (offset `0x5A00000`) and `userdata` via MediaTek MT6878 Preloader port without cloud dongles.
* **UFS 3.1 Hardware Partition Map**:
  * Complete partition table (`preloader_tecno_cn5c.bin`, `init_boot`, `vbmeta`, `super`, `nvram`, `nvdata`).

---

## 🧭 Interactive USB Plugged-In Guided Wizard

When a device is connected, the top banner guides the technician step-by-step with dual instructions:

```
[USB Plugged In] ──► Step 1: Handshake ──► Step 2: Scan Admins ──► Step 3: Strip Overlay
                                                                        │
[100% COMPLETE] ◄── Step 6: Safe Reboot ◄── Step 5: Freeze MDM ◄─────── Step 4: Deactivate
```

1. **Step 1: USB Plugged In & Authorized**: Handshake verification with Dimensity 7400.
2. **Step 2: Detect Active Admin Security Plugins**: Queries `dpm list-active-admins`.
3. **Step 3: Strip Op-Overlay & Kill Banner**: Revokes overlay rights; kills lock banner.
4. **Step 4: Deactivate Device Admin & Clear Cache**: Unregisters admin; wipes tokens.
5. **Step 5: Freeze HiOS MDM & Provisioning**: Sets provisioned flags to 1 permanently.
6. **Step 6: Safe Reboot & Verification**: Reboots into unlocked OS; 100% complete!

---

## 🎨 Strict 10-Color Monochrome Palette

The interface is styled exclusively using **exactly 10 colors**:

| Hex Code | Role |
|---|---|
| `#000000` | Pure Black (Root background, terminal background) |
| `#0c0c0c` | Dark Charcoal (Card backgrounds, container wrappers) |
| `#161616` | Deep Gray (Sub-cards, input boxes, code blocks) |
| `#222222` | Divider Gray (Card borders, inactive tab borders) |
| `#333333` | Medium Gray (Secondary buttons, scrollbars) |
| `#888888` | Muted Gray (Secondary subheaders, timestamps) |
| `#cccccc` | Body Gray (General text, parameter labels) |
| `#ffffff` | High-Contrast White (Headings, active tabs, action buttons) |
| `#22c55e` | Status Green (Terminal success indicator, OKAY logs) |
| `#ef4444` | Safety Red (Destructive actions: partition erase, format) |

---

## 🛠️ Complete Tab Matrix

1. **Connection Guide (NEW)**: Step-by-step connection tutorials for ADB (USB & Wi-Fi), Fastboot, Recovery/Sideload, MTK BROM/Preloader, Qualcomm EDL 9008, and Samsung Download mode — plus a one-click "Troubleshoot Now" that scans and prints the exact fix list.
2. **Diagnostics**: Real-time read of parameters for `TECNO-CN5c`, Samsung, Xiaomi, etc.
3. **Tecno Camon 50 Suite**: Preloader wipe, MDM disabler, Security Plugin remover, payload unpacker.
4. **Process Tutorials**: 6 milestones with sequential next-step roadmap and dynamic jump buttons.
5. **Supported Devices**: Searchable matrix of all major OEM chipsets and models.
6. **MTK BROM Flasher**: Preloader DAA bypass, partition address plan for MT6878/Helio/Dimensity. Now with real serial-port enumeration (VID 0E8D) and BROM handshake probing.
7. **Windows 11 Fixer**: Automated resolutions for Code 28, Transsion `0x2E04`, Core Isolation, USB 3.0 bugs.
8. **Reboot Modes**: 8 power switches (System, Recovery, Fastboot, Fastbootd, EDL 9008, Download).
9. **FRP & MDM**: Universal Fastboot FRP, Samsung Test Mode `*#0*#`, setup wizard bypass.
10. **Root & Magisk**: GKI `init_boot` flasher, AVB `--disable-verity` vbmeta flasher, Magisk installer.
11. **EFS & NVRAM**: Modem calibration backup and restore (`nvram.img`, `nvdata.img`).
12. **Fastboot Flasher**: Bootloader unlock/lock, partition flashing, cache and userdata format.
13. **HiOS Debloat**: 1-click bloatware cleaners and APK package manager.

---

## 🚀 Building from Source

```cmd
:: 1. Clone repository
git clone https://github.com/emmanuellaisa00/android-multi-tool-pro.git
cd android-multi-tool-pro

:: 2. Install dependencies
pip install -r requirements.txt

:: 3. Run GUI locally
python app_gui.py

:: 4. Run Web Suite locally
python web/server.py

:: 5. Compile Standalone Windows EXE
build.bat
```
*(GitHub Actions automatically compiles `AndroidMultiTool.exe` on every push with 100% green status).*
