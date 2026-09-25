# Hardware Test Checklist — Tecno Camon 50 Pro 5G (CN5c) Real Device
**Like Oumse live validation — 100% offline, no credits**

### 1. File-Patch Offline Proof (DONE ✓)
- [x] Proinfo dummy 3MB `FF` → patched `0x100 00 / 0x800 FF / 0x1000 00` preserved
- [x] Prodnv A `0x1000 00` / B `0x2000 FF`
- [x] LK `0x1000 01→00` unlocked
- [x] OGT zip with `META-INF/manifest.txt`
- [x] `verify_offline_ready` → `ready:true`

### 2. Live USB — Requires Real CN5c (needs hardware)
- [ ] **MTK Preloader** `Volume Up+Down + USB 2.0` → `MediaTek Preloader USB VCOM (VID 0x0e8d)` caught in 1.5s, `DAA/SLA bypass` log `0xA0 → 0x5F 0xF5`
- [ ] **BROM** `Bypass Direct BROM` → `[BROM] direct memory channel open` offline
- [ ] **META** `0xA0 0x0A 0x50 0x05 → META confirmed` → `Device Info META`, `Patch MDM MTK 1.5`, `MDM Permanent META 3` all FREE offline
- [ ] **SPD** `T612/T616` `prodnv` patch BROM/SPD `Variant A/B`
- [ ] **Fastbootd** `super` dynamic partition flash + `init_boot` KernelSU/Magisk + `vbmeta --disable-verity`
- [ ] **ADB** `transsion MDM freeze`, `device_owner_2.xml` purge, HiOS debloat

**How to test on Windows 11:**
1. Install `dist/installer/AndroidMultiTool_Setup_v2.5.exe` as admin → Program Files
2. Run `Start Menu → Install Drivers` (or `install_drivers.bat`) → `0x2e04 / 0x0e8d` in `adb_usb.ini`
3. Power off CN5c completely (hold Power 10s if locked)
4. Hold `Vol Up + Vol Down`, insert high-quality Type-C to **USB 2.0** port (Ryzen: avoid USB3)
5. In AMT Pro, untick `DEMO` → `Scan USB` should show `TECNO-CN5c MT6878` (if DEMO OFF and empty → check cable/port)
6. Execute `★ OUMSE 21 OPS` → each button should log `[OK] ... done offline` without `https://oumsegsm.com`

### 3. Known Limitations
- Placeholder `Setup.exe` is **unsigned** until `signtool` with EV cert (Oumse is signed OumseGsm225)
- Real `Setup.exe` size ~55 MB only after `iscc` on `windows-latest` (GitHub Actions now does it)
- Without real CN5c, logs are simulated but file-patch is real binary

