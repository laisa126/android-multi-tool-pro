"""
Android Multi-Tool Pro - Comprehensive Device Compatibility Matrix
Full catalog of supported devices, OEM models, chipsets, and servicing methods.
"""

from typing import Dict, List, Optional

SUPPORTED_DEVICE_CATALOG = [
    # --- SAMSUNG GALAXY ---
    {
        "brand": "Samsung",
        "series": "Galaxy S Series",
        "models": ["Galaxy S24 / S24+ / S24 Ultra", "Galaxy S23 / S23+ / S23 Ultra", "Galaxy S22 / S22+ / S22 Ultra", "Galaxy S21 / S21 FE", "Galaxy S20 / S20 FE", "Galaxy S10 / S10+ / S10e"],
        "chipset": "Snapdragon 8 Gen 1/2/3 & Exynos 2100/2200/2400",
        "supported_ops": ["ADB Diagnostics", "AT *#0*# Test Mode FRP", "Odin Download Mode", "CSC Switch", "Knox Telemetry", "OneUI Debloat"]
    },
    {
        "brand": "Samsung",
        "series": "Galaxy A & M Series (MediaTek)",
        "models": ["Galaxy A02 / A03s / A04 / A04e", "Galaxy A12 (SM-A125F)", "Galaxy A13 (SM-A137F)", "Galaxy A14 5G", "Galaxy A22 / A22 5G", "Galaxy A31 / A32", "Galaxy A34 5G", "Galaxy M02 / M12 / M22"],
        "chipset": "MediaTek Helio P35 / G80 / Dimensity 700 / 1080",
        "supported_ops": ["MTK BootROM 1-Click FRP", "Direct Userdata Wipe", "Samsung Test Mode", "Odin Download Mode", "Fastboot Flash"]
    },
    {
        "brand": "Samsung",
        "series": "Galaxy A & M Series (Qualcomm & Exynos)",
        "models": ["Galaxy A52 / A52s / A53 5G", "Galaxy A54 5G", "Galaxy A71 / A72 / A73 5G", "Galaxy M51 / M52 5G"],
        "chipset": "Snapdragon 720G / 750G / 778G & Exynos 1280 / 1380",
        "supported_ops": ["ADB Diagnostics", "Samsung Test Mode FRP", "EDL 9008 Test Point", "Odin Flashing", "EFS Backup"]
    },

    # --- XIAOMI / REDMI / POCO ---
    {
        "brand": "Xiaomi",
        "series": "Redmi Note Series",
        "models": ["Redmi Note 13 / 13 Pro 5G", "Redmi Note 12 / 12 Pro / 12 Turbo", "Redmi Note 11 / 11S / 11 Pro", "Redmi Note 10 / 10 Pro / 10S", "Redmi Note 9 / 9S / 9 Pro", "Redmi Note 8 / 8 Pro / 8T", "Redmi Note 7 / 7 Pro"],
        "chipset": "Qualcomm Snapdragon & MediaTek Helio / Dimensity",
        "supported_ops": ["Fastboot Flasher", "Fastbootd Super Dynamic Parts", "EDL 9008 Firehose", "MTK BROM Bypass", "Mi Cloud Persist Format", "MIUI/HyperOS Debloat", "OEM Unlock"]
    },
    {
        "brand": "Xiaomi",
        "series": "Redmi Number & POCO Series",
        "models": ["Redmi 9 / 9A / 9C", "Redmi 10 / 10A / 10C", "Redmi 12 / 12C / 13C", "POCO X3 NFC / X3 Pro", "POCO X4 / X5 / X6 Pro", "POCO F3 / F4 / F5", "POCO M3 / M4 / M5"],
        "chipset": "Snapdragon 860/778G/870 & MediaTek Helio G25/G35/G85/G99",
        "supported_ops": ["Fastboot Partition Flash", "EDL 9008 Partition Erase", "MTK SLA/DAA Auth Skip", "Anti-Rollback Check", "SafetyNet Pass Helper"]
    },

    # --- TRANSSION (TECNO / INFINIX / ITEL) ---
    {
        "brand": "Transsion",
        "series": "Tecno Spark & Camon Series",
        "models": ["Spark 7 / 8 / 9 / 10 / 20", "Camon 17 / 18 / 19 / 20 / 30 Pro", "Pova 2 / 3 / 4 / 5 / Neo"],
        "chipset": "MediaTek Helio G35 / G70 / G85 / G96 / G99 & Dimensity 8050",
        "supported_ops": ["MTK BROM 1-Click FRP", "Userdata Wipe (Lock Removal)", "Preloader VCOM Connect", "Fastboot OEM Unlock", "HiOS Telemetry Cleaner"]
    },
    {
        "brand": "Transsion",
        "series": "Infinix Hot, Note & Zero Series",
        "models": ["Hot 9 / 10 / 11 / 12 / 20 / 30 / 40", "Note 10 / 11 / 12 / 30 / 40 Pro", "Zero 5G / Zero Ultra / Zero 30"],
        "chipset": "MediaTek Helio G88 / G95 / G99 & Dimensity 920 / 8020",
        "supported_ops": ["MTK BROM Fast Wipe", "XOS Bloatware Cleaner", "Fastboot Flasher", "FRP Reset", "Bootloader Unlock"]
    },

    # --- BBK GROUP (OPPO / REALME / VIVO / ONEPLUS) ---
    {
        "brand": "BBK",
        "series": "Realme Number & C Series",
        "models": ["Realme C11 / C12 / C15 / C21 / C33 / C55", "Realme 5 / 6 / 7 / 8 / 9 / 10 / 11 / 12 Pro"],
        "chipset": "MediaTek Helio G-Series, Snapdragon 665 / 720G & Unisoc T612/T616",
        "supported_ops": ["MTK SLA Auth Skip", "Fastboot flashing unlock", "EDL 9008 Service", "ColorOS/RealmeUI Debloat", "Deep-Testing APK Push"]
    },
    {
        "brand": "BBK",
        "series": "Oppo A, Reno & Find Series",
        "models": ["Oppo A15 / A16 / A17 / A53 / A54 / A74 / A96", "Reno 4 / 5 / 6 / 7 / 8 / 10 / 11"],
        "chipset": "Snapdragon 662/680/765G & MediaTek Dimensity 7050/8100",
        "supported_ops": ["EDL 9008 Test Point", "MTK Preloader Format", "ColorOS Safe Debloat", "Full ADB Diagnostic Dump"]
    },
    {
        "brand": "BBK",
        "series": "Vivo Y, V & iQOO Series",
        "models": ["Vivo Y11 / Y12 / Y15 / Y20 / Y21 / Y33s / Y50 / Y53s", "Vivo V20 / V21 / V23 / V27 / V29", "iQOO Z6 / Z7 / Neo 6 / Neo 7"],
        "chipset": "Snapdragon 460/665/720G & MediaTek Helio P35/G80",
        "supported_ops": ["EDL 9008 Test Point", "MTK BROM Wipe", "Fastboot Flasher", "FuntouchOS Bloatware Removal"]
    },
    {
        "brand": "OnePlus",
        "series": "OnePlus Flagship & Nord Series",
        "models": ["OnePlus 7 / 8 / 9 / 10 / 11 / 12", "OnePlus Nord / Nord CE / Nord 2 / Nord 3"],
        "chipset": "Qualcomm Snapdragon 855 / 865 / 888 / 8 Gen 1/2/3 & Dimensity 9000",
        "supported_ops": ["Fastboot Flashing Unlock (Instant)", "MSMDownloadTool EDL Helper", "Fastbootd Super Dynamic Flasher", "Magisk Boot Root"]
    },

    # --- MOTOROLA & GOOGLE PIXEL ---
    {
        "brand": "Motorola",
        "series": "Moto G, E & Edge Series",
        "models": ["Moto G9 / G10 / G30 / G50 / G60 / G82 / G84", "Moto Edge 20 / 30 / 40 / 50 Pro", "Moto E7 / E20 / E32 / E40"],
        "chipset": "Snapdragon 480/695/778G & Unisoc T606/T700",
        "supported_ops": ["Fastboot Sparse Chunk Flasher", "Fastboot Universal FRP Erase", "Motorola OEM Unlock", "Blankflash EDL Unbrick"]
    },
    {
        "brand": "Google",
        "series": "Google Pixel Series",
        "models": ["Pixel 4 / 4a / 5 / 5a", "Pixel 6 / 6a / 6 Pro", "Pixel 7 / 7a / 7 Pro", "Pixel 8 / 8a / 8 Pro"],
        "chipset": "Google Tensor G1 / G2 / G3 & Snapdragon 765G",
        "supported_ops": ["Standard Android Fastboot Flasher", "OEM Bootloader Unlock", "Direct Factory Image Sideload", "Systemless Magisk / KernelSU Root"]
    },

    # --- UNISOC / SPREADTRUM (SPD) ---
    {
        "brand": "Unisoc (SPD)",
        "series": "Entry-level smartphones & tablets",
        "models": ["Realme C30 / C33", "Infinix Smart 7 / 8", "Tecno Pop 5 / 6 / 7", "Nokia C20 / C30 / G11 / G21", "itel A58 / A60 / S18"],
        "chipset": "Unisoc SC9863A / T606 / T610 / T612 / T616 / T700",
        "supported_ops": ["SPD Diag Port Reader", "Universal Fastboot Erase FRP", "PAC Firmware Flasher", "Userdata Wipe"]
    }
]

def find_device_matches(model_str: str) -> List[Dict[str, any]]:
    """Searches catalog for model matches based on ADB getprop or Fastboot product query."""
    matches = []
    query = model_str.lower()
    for cat in SUPPORTED_DEVICE_CATALOG:
        if query in cat["brand"].lower() or any(query in m.lower() for m in cat["models"]):
            matches.append(cat)
    return matches
