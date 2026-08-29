# Tecno Camon 50 Pro — Deep-Dive Research Report

**Purpose:** How the Tecno Camon 50 Pro is *managed* (boot chain, security, flash architecture) and every way it can be *connected* — with the developer files located, verified, and (where public) downloaded into this repo.

**Date:** 2026-08-29 · **Compiled from:** mtkclient source & issue tracker, XDA, Hovatek, NeedRom, Reddit (r/TECNOphone, r/androidroot), GSMarena/Nanoreview/91mobiles, UnlockTool changelog, and the Diablosat DA archive.

---

## 1. TL;DR — the single most important correction

The Camon 50 Pro ships in **two variants with different MediaTek chipsets**. Everything (DA file, scatter, whether a free unlock is possible) depends on which one you have:

| Variant | Model code | Project | Chipset | MTK part | CPU | GPU | Free mtkclient support |
|---|---|---|---|---|---|---|---|
| **Camon 50 Pro 4G** | **CN5c** | `h8924` | **Helio G200 Ultimate (6 nm)** | **MT6789** family (G99→G100→G200) | 2×A76 @2.2 + 6×A55 @2.0 | Mali-G57 MC2 | ✅ Yes — mature, built-in DA + payload |
| **Camon 50 Pro 5G** | **CN7c** | `h788` | **Dimensity 7300 / 7400 "Ultimate" (4 nm)** | **MT6878** | 4×A78 @2.6 + 4×A55 @2.0 | Mali-G615 MC2 | ⚠️ WIP — no bundled DA, needs `--loader`, no free auth yet |

> ⚠️ The tool's catalog previously labelled **CN5c = "Camon 50 Pro 5G / MT6878"**. That is **wrong**: CN5c is the **4G Helio G200 (MT6789)** model; the **5G Dimensity 7400 Ultimate (MT6878)** model is **CN7c**. Fixed in `core/device_matrix.py` and `core/scatter_flasher.py` this session.

**Quick identification of your device:** check the box label or *Settings → About phone* for the model code `CN5c` or `CN7c`, or the build string (`CN5c-16.x…` vs `CN7c-16.x…`). "5G" in the name ⇒ CN7c/MT6878.

---

## 2. How the phone actually boots (what "managed" means)

MediaTek devices use a staged boot chain. Understanding it is *the* key to connecting a locked phone:

```
[Power + Vol keys / USB] 
        │
        ▼
  BootROM (BROM) ──► runs before Android, from the SoC itself
        │              · answers "MediaTek USB Port (VCOM)"  VID 0E8D:0003
        │              · does the handshake, SLA/DAA auth, accepts a DA
        ▼
  Preloader (BL1) ──► "MediaTek PreLoader USB VCOM" VID 0E8D:2000
        │              · if it fails/crashes you fall back to BROM
        ▼
  Download Agent (DA) ──► MTK's signed loader uploaded by the PC tool
        │                  · gives the PC read/write access to flash
        ▼
  LK / Little Kernel (BL2) → verified boot (AVB/vbmeta) → Android (HiOS 16)
```

Consequences for a **locked** phone (screen PIN unknown, USB debugging OFF):
- ADB is dead — you cannot enable USB debugging without unlocking the screen. **No ADB, no MTP, no `adb reboot bootloader`.**
- But **BROM/Preloader still answer** — they run *before* Android, so a powered-off + Vol-key + USB connect can still handshake. This is the locked-device path.
- Whether the BROM then lets you do anything depends on **security config** (next section).

---

## 3. The security model (why a locked Camon 50 Pro resists)

Reported by tools after handshake as the **Target config** byte. Bits for: `SBC` (secure boot), `SLA` (serial-link auth), `DAA` (download-agent auth), `SWJTAG`, `Root cert required`, `Mem read/write auth`, `Cmd 0xC8 blocked`.

- **MT6789 (Helio G99/G200 — CN5c 4G):** mature, widely-bypassed SoC. mtkclient's Kamakiri payload path works; usually no auth file needed.
- **MT6878 (Dimensity 7300/7400 — CN7c 5G):**
  - On an *unprotected* device (e.g. the Unihertz Titan 2 in mtkclient issue #149) the log shows `Target config: 0x0`, `SBC/SLA/DAA enabled: False`, `Device is unprotected` — yet mtkclient still failed with `No valid da loader found` because it ships **no MT6878 DA**.
  - On Tecno/Transsion production builds expect `Target config: 0xE7` with `SBC/SLA/DAA enabled: True` → `Auth file is required. Use --auth option.` The auth file is **`auth_sv5.auth`**, shipped **inside the factory firmware**, generated against MediaTek's ROTPK.

**The crux:** for CN7c/MT6878 there is currently **no free/public auth file**. Commercial boxes (UnlockTool, TFT, CM2MT2, Android Utility/AMT) hold MT6878 auth **server-side** — UnlockTool added "MTK V6 MT6878 … Dimensity 7300/7300 Ultimate" and "Tecno/Infinix MTK up to Android 15 (factory reset / erase FRP / readback / flash)" in release **2026.02.20.0**. The official, no-hassle route remains the **Transsion SWD ("Tecno Flash Tool") + factory-signed firmware**, which carries the DA + auth file and needs no manual configuration.

---

## 4. Every connection path (in order of usefulness for a locked phone)

### 4.1 Normal ADB (USB debugging) — ❌ impossible on a locked phone
`adb devices` → needs the screen unlocked to toggle "USB debugging". Skip on a locked device.

### 4.2 Fastboot — ⚠️ only *after* OEM unlock (which needs a Tecno ID)
- Enter: `adb reboot bootloader` (needs ADB), or **power off → hold Vol Down + Power** (or Vol Up + Power).
- `fastboot devices` should list it. Transsion devices *do* have fastboot.
- **Unlock requirement:** you must be signed into a **Tecno ID account on the phone** (new accounts are locked out for ~14 days), then the **"OEM unlocking" toggle** becomes available in Developer options, then `fastboot flashing unlock` works.
- ⚠️ On Tecno, running `fastboot oem unlock` without the OEM toggle returns `OKAY` but `fastboot getvar unlocked` still says `no` (confirmed on XDA, Tecno Spark/other models). It silently does nothing.
- So for a **locked phone, fastboot cannot unlock it** — you go to BROM (§4.3) or the official tool (§4.5).

### 4.3 MTK BROM / Preloader — ✅ the locked-device path
1. Power the phone **fully off**.
2. Hold **Volume Up + Volume Down** (Transsion standard; some models just Vol Down).
3. Plug the USB cable while holding → the phone shows nothing, but the PC sees:
   - `MediaTek USB Port (VCOM)` = BROM (VID 0E8D:0003), or
   - `MediaTek PreLoader USB VCOM` = preloader (VID 0E8D:2000).
4. Needs the **MTK VCOM driver** (Windows), or udev rules (Linux). USB 2.0 ports are more reliable.
5. From there the tool uploads a DA (and auth file if protected) and then can format FRP, wipe userdata, read/write partitions, flash.

Notes from the field:
- On newer MTK (Android 12+) the *button* BROM is sometimes disabled — you land in **preloader** only. Workarounds: crash-preloader tricks (`mtk crash` in mtkclient, Android Utility "crash preloader", or the SP Flash Tool "fail on purpose" trick) to force BROM.
- One Infinix thread warns that on some Transsion models "holding both volume buttons puts the device in factory mode" — if so, use a single Vol key or the crash method.
- Test-point/ISP pinouts for MT6878V exist (see §7).

### 4.4 Recovery ADB sideload — ✅ works on a locked phone (limited)
Recovery's own adbd is authorized by the **"Apply update from ADB"** menu, so USB debugging is *not* needed. `adb devices` shows the device in `sideload` state and `adb sideload update.zip` installs an OTA. Useful for applying an official OTA to a soft-bricked phone; it will **not** unlock the bootloader or remove FRP. (Already implemented in the tool.)

### 4.5 Official Transsion SWD ("Tecno Flash Tool") — ✅ the sanctioned flash path
- Transsion Software Download Tool (a.k.a. Tecno Flash Tool, `SWD_AfterSales.exe`), MTK builds v4.1801–v4.1901 (v5.x is SPD/Qualcomm; v4.1901 needs a dongle only for "format all").
- Loads the **factory firmware** (scatter/XML + `MTK_AllInOne_DA.bin` + `auth_sv5.auth`), then: power off → Vol Up+Down → connect → Green PASS.
- Hovatek's note is the key advantage: *"you won't need to manually search for, input custom DA or Auth files in order to flash these models using software download tool"* — because the factory firmware carries them.
- Service functions include Read Info, Format, **Reset FRP**, **Unlock/Relock Bootloader**, DM-Verity fix, RPMB backup.

### 4.6 SP Flash Tool (manual)
- Use the **Download-XML** tab (new XML format) or classic scatter tab.
- Select: Download-Agent = `MTK_AllInOne_DA.bin` (or the MT6878 DA below), Scatter = `…Android_scatter.xml` / `MT6878_Android_scatter.txt`, Authentication = `auth_sv5.auth`.
- Power off → connect with Vol key pressed.

### 4.7 mtkclient (free/open-source)
```bash
git clone https://github.com/bkerler/mtkclient
# CN5c 4G (MT6789): works out of the box
python mtk e metadata,userdata,md_udc        # wipe
python mtk da seccfg unlock                  # unlock BL (after OEM toggle)
# CN7c 5G (MT6878): WIP — supply a DA manually
python mtk printgpt --loader MTK_AllInOne_DA_mt6878.bin        # or bin/da/MT6878_NOTHING.bin
python mtk da seccfg unlock --loader MTK_AllInOne_DA_mt6878.bin --auth auth_sv5.auth   # if protected
```
- MT6878 support in mainline mtkclient: `brom_config.py` has the chip (`hw code 0x1375`, `damode=XML`, `dacode 0x1375`) but **no bundled DA loader** — issue #149 "no valid da loader found MT6878" was closed *not planned*; the maintainer's support is WIP.
- The modded fork `sallecta/mtkclient_mod` (Codeberg) covers the V6-protocol chips and states plainly: *"For all devices with DAA, SLA and Remote-Auth activated no public solution currently exists."*

### 4.8 Paid boxes (server-side auth)
UnlockTool, TFT UnlockTool, CM2MT2/Infinity, Android Utility PRO (AUP), NCK, Chimera. These hold the MT6878 auth files on their servers and are currently the only way to do BROM operations on a **locked** CN7c/5G beyond the official Transsion tool. (XDA: *"The AMT ppl and CM2MT2 only have the auth file in their respective servers."*)

---

## 5. Chip identification table (from mtkclient source + issue #149)

| Item | MT6789 (Helio G99/G100/G200) | MT6878 (Dimensity 7300/7400 Ultimate) |
|---|---|---|
| HW code | (G99: 0x707 family — verify per build) | **0x1375** |
| DA code reported | — | **4981** (no bundled loader for it) |
| DA mode | LEGACY/xflash | **XML** (`DAmodes.XML`) |
| DA payload addr | — | 0x2010000 |
| BROM payload addr | — | 0x100a00 |
| WDT addr | — | 0x1c00a000 |
| UART addr | — | 0x11002000 |
| Description in mtkclient | "MTK Helio G99" (MT6789/MT8781V) | "Dimensity 7300" |
| Bundled DA in mtkclient | ✅ (generic v5/v6 + AllInOne) | ❌ none |

---

## 6. Dev files FOUND (and verified)

### 6.1 Downloaded into this repo → `bin/da/`
Real **MTK DA v6 (XML mode) for MT6878** — the loaders mtkclient lacks and this tool's `send_da()` can accept. Sourced from the Diablosat archive linked in mtkclient issue #149 (uploaded by @El-HOOT as "same chip").

| File | Size | Build string inside | SHA-256 |
|---|---|---|---|
| `bin/da/MT6878_NOTHING.bin` | 1,248,068 B | `MTK_DA_v6_2024-03-06 14:18:05` | `415a2ce14faa4d1303b41a44a498acb18055d166e89fcd10f53fff63cd26ed50` |
| `bin/da/MT6878_NOTHING_1.bin` | 1,255,284 B | `MTK_DA_v6_2024-12-11 20:09:40` | `661ba3a4c610735656ab5480b6842cf4a78c64cd86bebe970539cd1d35baa8e8` |

Verification: both begin with the ASCII header `MTK_DOWNLOAD_AGENT` and contain `MTK_DA`, `mt6878`, `SLA`, `DAA`, `EMI`, `USB` markers — i.e. genuine MTK download agents for MT6878, **not** random data.

> ⚠️ These are third-party/leaked MediaTek binaries (dumped from a Nothing Phone of the same SoC). They are unsigned-for-your-device: they still cannot defeat **DAA/SLA on a protected Tecno** without the matching `auth_sv5.auth`. Use them only where they are accepted (e.g. `--loader` on an unprotected device, or as the upload payload for this tool's DA path).

### 6.2 DA archive (source)
- `https://archive.diablosat.cc/firmwares/amt-dumps/NothingDA/` — contains `MT6878_NOTHING.bin`, `MT6878_NOTHING_1.bin`, `MT6886_NOTHING_0.bin`.

### 6.3 Firmware (contains the real scatter/preloader/DA/auth)
- Hovatek "Tecno Camon 50 Pro Stock ROM" (thread 49681):
  - CN5c-16.1.0.110SP23_OP001PF001AZ **[Factory / Signed]** (MEGA link)
  - CN7c-16.2.0.140SP06_OP005PF001AZ **[Factory / Signed]** (MEGA link)
- NeedRom:
  - "Tecno Camon 50 Pro CN5c" (many CN5c-16.x builds, `full_cn5c_h8924-user`, tagged MT6789)
  - "Tecno Camon 50 Pro 5G CN7c" (many CN7c-16.x builds, `full_cn7c_h788-user`, tagged MT6878) — firmware is **XML scatter** (`…Android_scatter.xml`) and may include an **Authentication File**.
- firmwarebd.com: CN5c root/unroot file `CN5c-16.1.0.150SP14(OPPJ003PF001PJ)` + "Tecno/Infinix Flash Tool" root guide.

### 6.4 Hardware (test point / ISP)
- frtech.com: **"MT6878V MTK Dimensity 7300 ISP PINOUT"** (4 MB) — eMMC/UFS ISP pinout for direct hardware work on MT6878V.
- Standard MTK USB IDs: BROM `0E8D:0003`, Preloader `0E8D:2000`, DA `0E8D:2001`.

---

## 7. Concrete recommendation for a **locked** Camon 50 Pro

1. **Identify the variant** (CN5c vs CN7c) from the box / about screen / build string.
2. **Drivers first:** MediaTek USB VCOM + Preloader VCOM (Windows: disable driver-signature enforcement if needed; Linux: udev rules; use a USB 2.0 port).
3. **Connect in BROM/preloader:** power off → hold Vol Up+Vol Down → plug USB → confirm `MediaTek USB Port` / `MediaTek PreLoader USB VCOM` in Device Manager.
4. **Choose the tool by variant:**
   - **CN5c (4G, MT6789):** free path — `mtkclient` (`mtk e metadata,userdata,md_udc` for FRP/locks; `mtk da seccfg unlock` after OEM toggle) **or** Transsion SWD + factory firmware.
   - **CN7c (5G, MT6878):** official Transsion SWD + factory-signed firmware (DA+auth inside) **or** a paid box with server auth (UnlockTool ≥ 2026.02.20.0, CM2MT2, TFT). Free mtkclient is WIP and will stop at `Auth file is required` on a protected unit — the DA files in `bin/da/` help only if the unit is unprotected or you obtain `auth_sv5.auth`.
5. **To unlock the bootloader properly (both variants):** sign into a ≥14-day-old **Tecno ID** on the phone, enable **OEM unlocking** in Developer options, then `fastboot flashing unlock`.
6. **Recovery sideload** remains the safe way to apply an official OTA to a phone that boots to recovery (no USB debugging needed).

---

## 8. Source links

**Primary / authoritative**
- mtkclient chip config (MT6878 + MT6789 entries): `mtkclient/config/brom_config.py` (bkerler/mtkclient)
- mtkclient issue #149 "no valid da loader found MT6878": https://github.com/bkerler/mtkclient/issues/149
- mtkclient issue #70 (linked from #149, custom DA discussion): https://github.com/bkerler/mtkclient/issues/70
- mtkclient bootloader-unlock discussion (auth_sv5.auth usage): https://github.com/bkerler/mtkclient/discussions/61
- sallecta/mtkclient_mod (V6 protocol chips; "no public solution for DAA/SLA/Remote-Auth"): https://codeberg.org/sallecta/mtkclient_mod

**Firmware / files**
- Hovatek Camon 50 Pro Stock ROM: https://www.hovatek.com/forum/thread-49681.html
- NeedRom Camon 50 Pro CN5c (MT6789): https://www.needrom.com/download/tecno-camon-50-pro-cn5c/
- NeedRom Camon 50 Pro 5G CN7c (MT6878): https://www.needrom.com/download/tecno-camon-50-pro-5g-cn7c/
- DA archive (MT6878 DA files): https://archive.diablosat.cc/firmwares/amt-dumps/NothingDA/
- MT6878V ISP pinout: https://support.frtech.com/index.php?a=downloads&b=folder&id=1088

**Tools**
- Transsion SWD / Tecno Flash Tool (versions + usage): https://androidmtk.com/download-transsion-software-download-tool ; https://www.hovatek.com/forum/thread-23708.html
- SP Flash Tool auth-file procedure: https://droidwin.com/download-agent-scatter-authentication-files-in-sp-flash-tool/
- How to force BROM (SP Flash Tool crash trick): https://www.hovatek.com/blog/how-to-force-a-mediatek-device-into-brom-mode/
- UnlockTool changelog (MT6878 support, Feb 2026): https://unlocktool.net/download/

**Community / procedures**
- XDA: mtkclient setup guide: https://xdaforums.com/t/guide-mtk-how-to-use-mtkclient-and-set-it-up.4509245/
- XDA: Tecno unlock bootloader (Tecno ID + 14 days): https://xdaforums.com/t/tecno-unlock-bootloader.4580657/
- Reddit r/TECNOphone unlock (Tecno account ≥2 weeks): https://www.reddit.com/r/TECNOphone/comments/1l6sqq2/how_do_you_unlock_the_bootloader_of_tecno_camon/
- XDA: BROM entry discussion: https://xdaforums.com/t/how-to-enter-into-brom-mode.4462757/
- XDA: MTK auth bypass (SLA/DAA) utility: https://xdaforums.com/t/mod-dev-mediatek-mtk-auth-bypass-sla-daa-utility.4232377/
- Specs: https://www.gsmarena.com/tecno_camon_50_pro_5g-14538.php (5G) · https://www.gsmarena.com/tecno_camon_50_pro-14500.php (4G) · https://www.91mobiles.com/tecno-camon-50-pro-5g-price-in-india (MT6878)
