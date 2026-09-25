# Tecno Camon 50 Pro — Verified Working Files (Flash / Firmware / Root)

> Compiled 2026-08-29. All links below were checked live. Focus is on the
> **CN5c (4G · MT6789 · Helio G200 Ultimate)** — your confirmed device — plus
> the CN7c (5G · MT6878) variant for completeness.

---

## 1. Stock ROM / Firmware (flash files) — VERIFIED LIVE

These are full **scatter-format** stock ROMs. Flash with **SP Flash Tool**
(or any paid box / mtkclient). They unbrick, downgrade, and **contain the DA +
auth files the tool needs** (see §4).

### ✅ CN5c — Factory / Signed (your device)
| Build | Size | Link | Status |
|---|---|---|---|
| `CN5c-16.1.0.110SP23_OP001PF001AZ` | ~11.4 GB | https://mega.nz/file/N1JDmSDa#d5OVgxX93GSrHJu75ycUQgVIDf8dMjqA2DbP8PkoBfU | ✅ **verified live (Mega API)** |
| `CN5c-16.1.0.110SP23_OP001PF001AZ` | 11.72 GB | https://drive.google.com/file/d/1inSHgnEfiW4QkL5-K8v0icK3kbpsvdvM/view?usp=sharing | ✅ **HTTP 200** (Google Drive mirror) |

Source: [Hovatek thread 49681](https://www.hovatek.com/forum/thread-49681.html) (Mega),
[NaijaRom CN5C page](https://naijarom.com/tecno-camon-50-pro-cn5c) (Drive mirror).

### ✅ CN7c — Factory / Signed (5G variant)
| Build | Size | Link | Status |
|---|---|---|---|
| `CN7c-16.2.0.140SP06_OP005PF001AZ` | ~11.8 GB | https://mega.nz/file/Yx5BWA4T#FkbzwScf9S1pwNvh5E8WjD-1vsNtrOSNAyyeKq8sBwA | ✅ **verified live (Mega API)** |

### More CN5c builds (multi-host)
- **NaijaRom** (free + paid mirrors) — 4 builds: 16.1.0.110SP23, 16.1.0.150SP09,
  16.2.0.150SP07 (OP004PF001AZ & OPPJ004PF001PJ):
  https://naijarom.com/tecno-camon-50-pro-cn5c
- **FirmwareDrive** folder (paid host) — same 4 zips:
  https://firmwaredrive.com/index.php?a=downloads&b=folder&id=52034
  (file ids: 122750, 125839, 130796, 131516)
- **NeedRom** (free registration required) — 10+ CN5c builds with changelogs:
  https://www.needrom.com/download/tecno-camon-50-pro-cn5c/
- **FirmwareBD** — CN5c-16.1.0.110SP23:
  https://www.firmwarebd.com/2026/02/tecno-camon-50-pro-cn5c-firmware-flash.html

---

## 2. Root file (Magisk boot.img) — CN5c

- **File:** `CN5c Root UnRoot File [CN5c-16.1.0.150SP14(OPPJ003PF001PJ)]`
- **Requirement:** bootloader **must be unlocked** first (OEM unlock + `fastboot
  flashing unlock`; Tecno needs an account ≥ 2 weeks old).
- **How:** flash the Magisk-patched boot.img with **Tecno/Infinix Flash Tool**.
- https://www.firmwarebd.com/2026/05/how-to-root-tecno-camon-50-pro-cn5c.html

---

## 3. DA (Download Agent) + Auth file — for mtkclient / SP Flash Tool

**This is the key piece for making the tool work on the Camon 50 Pro.**

The MT6789 (Helio G99 family) has **DAA (Download Agent Authentication) enabled**.
mtkclient's bundled generic `MTK_DA_V6.bin` is **rejected** with
`DAA_SIG_VERIFY_FAILED`. The fix is to feed it the **signed DA that ships inside
the device's own stock ROM**.

Inside an extracted CN5c stock ROM (or an MXML flash package) you will find
(the names may vary slightly):

```
MT6789_Android_scatter.txt        # scatter (also .xml)
images/download_agent/DA_BR.bin   # signed Download Agent  ← use as --loader
auth_sv5.auth                     # authentication file   ← use as --auth
preloader_*.bin                   # preloader              ← use as --preloader
```

### mtkclient command (once files are extracted)
```bash
mtk e metadata,userdata,md_udc \
    --loader   images/download_agent/DA_BR.bin \
    --preloader preloader_cn5c.bin \
    --auth      auth_sv5.auth
```

### SP Flash Tool
- Load `MT6789_Android_scatter.txt`, point the **Authentication File** slot at
  `auth_sv5.auth` (SP Flash Tool v6+), DA auto-selected from the ROM.
- Newer CN5c builds are MXML (Tecno's proprietary package) — use the official
  **Tecno Flash Tool** or extract with transsion MXML extractors; NaijaRom
  provides SP-Flash-Tool-ready zips.

**Important caveat:** `auth_sv5.auth` is per-unit/per-model signed. A DA/auth
from a *different* MT6789 phone (e.g. Poco M5 `rock.zip`) will **not** work on
the Camon 50 Pro — you must pull the DA/auth from the **CN5c stock ROM above**.

---

## 4. What the commercial tools do (for reference)

- **UnlockTool** already supports CN5c FRP + factory reset + erase via
  **META mode** (chip `mt6789`, e.g. build `CN5c-16.1.0.160SP10`). Confirmed in
  [Martview thread](https://www.martview-forum.com/threads/tecno-camon-50-pro-4g-cn5c-frp-factory-reset-meta-mode-unlock-don.190704/).
- That means: for a **locked/bricked** CN5c, the free path is
  **stock-ROM DA + auth + mtkclient**; the paid path is UnlockTool / CM2 / WWR MTK.

---

## 5. Quick decision guide

| Goal | Use |
|---|---|
| Unbrick / reflash / downgrade | Stock ROM (§1) + SP Flash Tool |
| Extract DA + auth for mtkclient | Stock ROM (§1) → §3 |
| Wipe FRP / factory reset (locked) | mtkclient + ROM DA/auth (§3), or UnlockTool (paid) |
| Root | Bootloader unlock → Magisk boot.img (§2) |
| Free one-shot FRP/reset | mtkclient works **only** with ROM DA/auth for MT6789 DAA devices |

> The single most useful download for you: **the CN5c Mega link** — it is the
> factory/signed full firmware and contains everything (scatter, DA, auth,
> preloader) needed for both SP Flash Tool and mtkclient.
