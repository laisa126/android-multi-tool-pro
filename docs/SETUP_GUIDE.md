Android Multi-Tool Pro — Windows Setup (like Oumse)
====================================================
Installer: AndroidMultiTool_Setup_v2.5.exe
Engine  : Inno Setup 6 — LZMA2/Ultra64 — Modern Wizard
Size    : ~55 MB (includes adb.exe, fastboot.exe, drivers)
Windows : 7 / 8 / 10 / 11 (64-bit, admin required)

WHERE IT INSTALLS
-----------------
Install folder   : C:\Program Files\AndroidMultiToolPro
                 (DefaultDirName {autopf}\AndroidMultiToolPro)
Executable       : C:\Program Files\AndroidMultiToolPro\AndroidMultiTool.exe
Bundled tools    : C:\Program Files\AndroidMultiToolPro\bin\adb.exe
                   C:\Program Files\AndroidMultiToolPro\bin\fastboot.exe
                   C:\Program Files\AndroidMultiToolPro\bin\drivers\*
Start Menu       : Start → Android Multi-Tool Pro
Desktop shortcut : C:\Users\%USERNAME%\Desktop\Android Multi-Tool Pro.lnk
Uninstall        : Settings → Installed Apps → Android Multi-Tool Pro
                  or Start Menu → Uninstall Android Multi-Tool Pro
Registry         : HKLM\SOFTWARE\AndroidMultiToolPro

BUILD IT (on Windows)
---------------------
1. Install Python 3.10+ (tick Add to PATH)
2. Install Inno Setup 6 from https://jrsoftware.org/isdl.php
3. Open CMD in project root and run:
       build_installer.bat
   Or manually:
       python -m PyInstaller --clean --noconfirm AndroidMultiTool.spec
       iscc installer_setup.iss
4. Output: dist\installer\AndroidMultiTool_Setup_v2.5.exe

INSTALL IT (like Oumse)
-----------------------
1. Right-click AndroidMultiTool_Setup_v2.5.exe → Run as administrator
2. Wizard: Welcome → License (README.md) → Choose folder → Tasks
   - [ ] Create desktop icon
   - [ ] Install MediaTek + Transsion USB drivers (VID 0x0E8D / 0x2E04)
3. Click Install → Finish → [✓] Launch Android Multi-Tool Pro
4. If drivers needed later: Start Menu → Install Drivers (install_drivers.bat)
   This writes adb_usb.ini with 0x2e04 / 0x0e8d.

PORTABLE FALLBACK (no admin)
-----------------------------
If you cannot run Setup as admin, use:
   AndroidMultiTool-Windows-v2.5.zip → extract → double-click install_app_on_pc.bat
This copies to %LOCALAPPDATA%\Programs\AndroidMultiToolPro, creates desktop/Start Menu
shortcuts, registers in Installed Apps, and configures %PATH% + adb_usb.ini.

OFFLINE — NO CREDITS
--------------------
All 21 Oumse operations (META / BROM / SPD / LK / ROM) run 100% offline via local USB.
No https://oumsegsm.com, no credits, no Telegram, no internet.

---
### Code Signing (like Oumse Signed)
- Oumse v2.1.0 is signed `OumseGsm225`. Our `AndroidMultiTool_Setup_v2.5.exe` is **unsigned** until you sign it:
  ```
  signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\installer\AndroidMultiTool_Setup_v2.5.exe
  ```
  Without signing, Windows SmartScreen will show “Unknown publisher — Run anyway”.

### Icons (new, clean monochrome like Oumse)
- `assets/icon.ico` (16/24/32/48/64/128/256) — chip + green bar + AMT PRO
- `assets/wizard.bmp` 164x314 + `wizard-small.bmp` 55x58 for Inno Setup wizard
- EXE icon set via `AndroidMultiTool.spec: icon='assets/icon.ico'`

### Build on GitHub Actions (automatic Setup)
- Workflow `.github/workflows/build-exe.yml` now:
  1. Builds `dist/AndroidMultiTool.exe` (PyInstaller)
  2. `choco install innosetup` → `iscc installer_setup.iss` → `dist/installer/AndroidMultiTool_Setup_v2.5.exe`
  3. Uploads artifact `AndroidMultiTool-Windows-v2.5` with EXE + ZIP + Setup.exe

### Multi-Language (FR/EN/AR/PT like Oumse)
- Title bar EN/FR/AR/PT switcher (data-i18n) covers sidebar nav, hardware strip, install button.
- Arabic flips to RTL (`dir=rtl`) and swaps sidebar border.
- Persisted in `localStorage amt_lang`.

