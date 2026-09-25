"""
Android Multi-Tool Pro — MediaTek deep-service workflows (real mtkclient).

Higher-level operations on top of MTKEngine.run_mtkclient, shared by the
desktop GUI and the web suite:

  * firmware-folder auto-location (DA loader / auth_sv5.auth / preloader / scatter)
  * partition backup            ->  mtk r <part[,part...]> <file|dir>
  * full ROM readback           ->  mtk rl <dir>
  * single partition write      ->  mtk w <part> <file>
  * full firmware write         ->  mtk wl <dir>
  * erase partitions            ->  mtk e <part[,part...]>
  * bootloader unlock / lock    ->  mtk da seccfg unlock|lock
  * reboot from BROM            ->  mtk reset
  * IMEI-source dump + scan     ->  dump nvram/nvdata/nvcfg/proinfo, regex + Luhn

Every operation returns the real (ok, last_line) from mtkclient and streams its
stdout through log_cb. No simulated success anywhere.
"""

import os
import re
from typing import Callable, Dict, List, Optional, Tuple

from .mtk_engine import MTKEngine

# Partitions whose raw content may contain a plaintext 15-digit IMEI on MTK.
IMEI_SOURCE_PARTS = ["nvram", "nvdata", "nvcfg", "proinfo"]

# Common, safe-to-backup partitions (never preloader_emmc protected twins).
COMMON_PARTITIONS = [
    "preloader", "boot", "recovery", "lk", "logo", "dtbo", "md1img",
    "nvram", "nvdata", "nvcfg", "proinfo", "protect1", "protect2",
    "seccfg", "frp", "gpt", "efuse", "misc", "vbmeta",
]

_IMEI_RE = re.compile(rb"(?<!\d)(\d{15})(?!\d)")

# loader: anything DA-like that ends in .bin; prefer download_agent subfolder.
_LOADER_HINTS = ("da_", "_da", "download_agent", "allinone_da", "da_br")
_AUTH_HINTS = ("auth_sv5", ".auth")
_PRELOADER_HINTS = ("preloader",)
_SCATTER_HINTS = ("scatter",)


def luhn_ok(digits: str) -> bool:
    """Standard Luhn checksum over a 15-digit string."""
    if len(digits) != 15 or not digits.isdigit():
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def scan_imei(folder: str, max_file_mb: int = 64) -> List[str]:
    """Recursively scan a folder for 15-digit, Luhn-valid IMEI candidates.

    Heuristic only: many MTK builds store IMEI MD5-hashed (needing the device
    key), in which case nothing is found and the caller should say so.
    """
    found: List[str] = []
    seen = set()
    cap = max_file_mb * 1024 * 1024
    for root, _dirs, files in os.walk(folder):
        for fn in files:
            path = os.path.join(root, fn)
            try:
                if os.path.getsize(path) > cap:
                    continue
                with open(path, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            for m in _IMEI_RE.finditer(data):
                digits = m.group(1).decode("ascii", "ignore")
                if luhn_ok(digits) and digits not in seen:
                    seen.add(digits)
                    found.append(digits)
    return found


class MTKWorkflows:
    """MediaTek servicing workflows delegating to the real mtkclient CLI."""

    def __init__(self, engine: Optional[MTKEngine] = None):
        self.mtk = engine or MTKEngine()

    # ------------------------------------------------------------------
    # Firmware-folder auto-location
    # ------------------------------------------------------------------
    def locate_firmware_files(self, folder: str) -> Dict[str, Optional[str]]:
        """Find DA loader / auth / preloader / scatter inside an extracted ROM."""
        result: Dict[str, Optional[str]] = {
            "loader": None, "auth": None, "preloader": None, "scatter": None
        }
        if not folder or not os.path.isdir(folder):
            return result

        loader_cands, auth_cands, preloader_cands, scatter_cands = [], [], [], []
        for root, _dirs, files in os.walk(folder):
            for fn in files:
                path = os.path.join(root, fn)
                low = fn.lower()
                if not (low.endswith(".bin") or low.endswith(".auth")
                        or low.endswith(".txt") or low.endswith(".xml")):
                    continue
                if low.endswith((".auth",)) or any(h in low for h in _AUTH_HINTS):
                    auth_cands.append(path)
                if low.endswith(".bin"):
                    if any(h in low for h in _LOADER_HINTS) and "preloader" not in low:
                        loader_cands.append(path)
                    if any(h in low for h in _PRELOADER_HINTS):
                        preloader_cands.append(path)
                if any(h in low for h in _SCATTER_HINTS) and low.endswith((".txt", ".xml")):
                    scatter_cands.append(path)

        # Prefer the ones inside a download_agent / images subfolder (authentic DA).
        def _prefer_agent(paths):
            for p in paths:
                if "download_agent" in p.lower() or "images" in p.lower():
                    return p
            return paths[0] if paths else None

        result["loader"] = _prefer_agent(loader_cands)
        result["auth"] = auth_cands[0] if auth_cands else None
        result["preloader"] = preloader_cands[0] if preloader_cands else None
        result["scatter"] = scatter_cands[0] if scatter_cands else None
        return result

    # ------------------------------------------------------------------
    # Arg context building
    # ------------------------------------------------------------------
    def ctx_args(self, ctx: Optional[Dict[str, Optional[str]]] = None) -> List[str]:
        ctx = ctx or {}
        args: List[str] = []
        for flag, key in (("--loader", "loader"), ("--auth", "auth"), ("--preloader", "preloader")):
            val = (ctx.get(key) or "").strip()
            if val:
                args += [flag, val]
        return args

    # ------------------------------------------------------------------
    # Operations (each returns (ok, tail) and streams stdout via log_cb)
    # ------------------------------------------------------------------
    def backup_partitions(self, parts: List[str], out_dir: str,
                          ctx: Optional[Dict[str, Optional[str]]] = None,
                          log_cb: Optional[Callable] = None,
                          timeout: int = 1800) -> Tuple[bool, str]:
        """mtk r <parts> — single part writes to a file, several to a folder."""
        os.makedirs(out_dir, exist_ok=True)
        if len(parts) == 1:
            out = os.path.join(out_dir, parts[0] + ".bin")
            args = ["r", parts[0]] + self.ctx_args(ctx) + [out]
        else:
            args = ["r", ",".join(parts)] + self.ctx_args(ctx) + [out_dir]
        return self.mtk.run_mtkclient(args, log_cb=log_cb, timeout=timeout)

    def read_all(self, out_dir: str, ctx: Optional[Dict[str, Optional[str]]] = None,
                 log_cb: Optional[Callable] = None, timeout: int = 5400) -> Tuple[bool, str]:
        """mtk rl <dir> — dump every partition + generate a scatter."""
        os.makedirs(out_dir, exist_ok=True)
        args = ["rl"] + self.ctx_args(ctx) + [out_dir]
        return self.mtk.run_mtkclient(args, log_cb=log_cb, timeout=timeout)

    def write_partition(self, part: str, image: str,
                        ctx: Optional[Dict[str, Optional[str]]] = None,
                        log_cb: Optional[Callable] = None,
                        timeout: int = 1800) -> Tuple[bool, str]:
        """mtk w <part> <file> — flash one partition image."""
        args = ["w", part, image] + self.ctx_args(ctx)
        return self.mtk.run_mtkclient(args, log_cb=log_cb, timeout=timeout)

    def write_all(self, folder: str, ctx: Optional[Dict[str, Optional[str]]] = None,
                  log_cb: Optional[Callable] = None, timeout: int = 5400) -> Tuple[bool, str]:
        """mtk wl <dir> — flash a full extracted firmware folder (needs its scatter)."""
        args = ["wl"] + self.ctx_args(ctx) + [folder]
        return self.mtk.run_mtkclient(args, log_cb=log_cb, timeout=timeout)

    def erase_partitions(self, parts: List[str],
                         ctx: Optional[Dict[str, Optional[str]]] = None,
                         log_cb: Optional[Callable] = None,
                         timeout: int = 900) -> Tuple[bool, str]:
        """mtk e <part[,part...]> — wipe partitions (FRP / factory reset)."""
        args = ["e", ",".join(parts)] + self.ctx_args(ctx)
        return self.mtk.run_mtkclient(args, log_cb=log_cb, timeout=timeout)

    def unlock_bootloader(self, ctx: Optional[Dict[str, Optional[str]]] = None,
                          log_cb: Optional[Callable] = None,
                          timeout: int = 900) -> Tuple[bool, str]:
        """mtk da seccfg unlock — set the seccfg unlock flag via the DA."""
        args = ["da", "seccfg", "unlock"] + self.ctx_args(ctx)
        return self.mtk.run_mtkclient(args, log_cb=log_cb, timeout=timeout)

    def lock_bootloader(self, ctx: Optional[Dict[str, Optional[str]]] = None,
                        log_cb: Optional[Callable] = None,
                        timeout: int = 900) -> Tuple[bool, str]:
        """mtk da seccfg lock — re-lock the bootloader."""
        args = ["da", "seccfg", "lock"] + self.ctx_args(ctx)
        return self.mtk.run_mtkclient(args, log_cb=log_cb, timeout=timeout)

    def reboot(self, ctx: Optional[Dict[str, Optional[str]]] = None,
               log_cb: Optional[Callable] = None,
               timeout: int = 120) -> Tuple[bool, str]:
        """mtk reset — reboot the device out of BROM."""
        args = ["reset"] + self.ctx_args(ctx)
        return self.mtk.run_mtkclient(args, log_cb=log_cb, timeout=timeout)

    def dump_imei_sources(self, out_dir: str, ctx: Optional[Dict[str, Optional[str]]] = None,
                          log_cb: Optional[Callable] = None,
                          timeout: int = 1800) -> Tuple[bool, str]:
        """Dump the partitions that hold IMEI (nvram/nvdata/nvcfg/proinfo)."""
        return self.backup_partitions(IMEI_SOURCE_PARTS, out_dir, ctx, log_cb, timeout)
