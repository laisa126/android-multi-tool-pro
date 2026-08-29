"""
Android Multi-Tool Pro - Comprehensive Device Compatibility Matrix
Full catalog of supported devices, OEM models, chipsets, and servicing methods.
Includes dedicated support for Tecno Camon 50 Pro / Camon 50 Pro 5G.
"""

from typing import Dict, List, Optional

SUPPORTED_DEVICE_CATALOG = [
    # --- TRANSSION: TECNO (FLAGSHIP & CAMON SERIES) ---
    {
        "brand": "Tecno",
        "series": "Camon Pro Series (Flagship Camera Line)",
        "models": [
            "Tecno Camon 50 Pro 5G (CN7c) — MT6878 Dimensity 7400 Ultimate",
            "Tecno Camon 50 Pro 4G (CN5c) — MT6789 Helio G200 Ultimate",
            "Tecno Camon 50 / Camon 50 Premier",
            "Tecno Camon 30 / 30 Pro 5G / 30 Premier",
            "Tecno Camon 20 / 20 Pro / 20 Premier 5G",
            "Tecno Camon 19 / 19 Pro / 19 Neo",
            "Tecno Camon 18 / 18 Premier / 18P"
        ],
        "chipset": "MediaTek Dimensity 7400 Ultimate (MT6878) / Dimensity 8300-8200 (MT6897/MT6896) / Helio G200-G99 (MT6789)",
        "supported_ops": [
            "1-Click MTK BROM / Preloader FRP Wipe",
            "Userdata Hard Format (Screen PIN/Pattern Removal)",
            "HiOS 14/15/16 Bloatware Auto-Cleaner",
            "Fastbootd Dynamic 'super' Partition Flasher",
            "Android 14/15/16 init_boot KernelSU & Magisk Root",
            "VBMeta AVB Disabler (--disable-verity)",
            "NVRAM & NVDATA Baseband / Radio Calibration Backup",
            "OEM Bootloader Unlock (fastboot flashing unlock)"
        ]
    },
    {
        "brand": "Tecno",
        "series": "Spark & Pova Series",
        "models": ["Spark 20 / 20 Pro / 20 Pro+", "Spark 10 / 10 Pro / 10C", "Spark 9 / 8 / 7", "Pova 6 / 6 Pro 5G", "Pova 5 / 5 Pro / Neo 3"],
        "chipset": "MediaTek Helio G85 / G88 / G99 & Dimensity 6080 / 7020",
        "supported_ops": ["MTK BROM FRP Reset", "Userdata Wipe", "Preloader VCOM Connect", "Fastboot Flasher", "HiOS Telemetry Removal"]
    },
    {
        "brand": "Infinix",
        "series": "Hot, Note & Zero Series",
        "models": ["Hot 40 / 40 Pro", "Hot 30 / 20 / 12", "Note 40 / 40 Pro 5G", "Note 30 / 30 Pro", "Zero 30 5G / Zero Ultra"],
        "chipset": "MediaTek Helio G99 / Dimensity 7020 / Dimensity 8020",
        "supported_ops": ["MTK Preloader Format", "XOS Bloatware Cleaner", "FRP Reset", "Fastbootd Flasher", "Magisk Root"]
    },

    # --- SAMSUNG GALAXY ---
    {
        "brand": "Samsung",
        "series": "Galaxy S Series",
        "models": ["Galaxy S24 / S24+ / S24 Ultra", "Galaxy S23 / S23+ / S23 Ultra", "Galaxy S22 / S22+ / S22 Ultra", "Galaxy S21 / S21 FE", "Galaxy S20 / S20 FE"],
        "chipset": "Snapdragon 8 Gen 1/2/3 & Exynos 2100/2200/2400",
        "supported_ops": ["ADB Diagnostics", "AT *#0*# Test Mode FRP", "Odin Download Mode", "CSC Switch", "Knox Telemetry", "OneUI Debloat"]
    },
    {
        "brand": "Samsung",
        "series": "Galaxy A & M Series (MediaTek)",
        "models": ["Galaxy A02 / A03s / A04 / A04e", "Galaxy A12 (SM-A125F)", "Galaxy A13 (SM-A137F)", "Galaxy A14 5G", "Galaxy A22 / A22 5G", "Galaxy A32 / A34 5G", "Galaxy M12 / M22"],
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
        "models": ["Redmi Note 13 / 13 Pro 5G", "Redmi Note 12 / 12 Pro / 12 Turbo", "Redmi Note 11 / 11S / 11 Pro", "Redmi Note 10 / 10 Pro / 10S", "Redmi Note 9 / 9S / 9 Pro", "Redmi Note 8 / 8 Pro / 8T"],
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
    },

    # --- TECNO PHANTOM & CAMON 40 (FOLDABLES / 2025 FLAGSHIPS) ---
    {
        "brand": "Tecno",
        "series": "Phantom & Camon 40 Series (Foldables & 2025 Flagships)",
        "models": ["Phantom V Fold 2 / V Flip 2", "Phantom V2 Flip", "Camon 40 / 40 Pro / 40 Premier 5G", "Camon 30s / 30 Pro+"],
        "chipset": "MediaTek Dimensity 9000+ / 8200 Ultimate / 7300 / Helio G100",
        "supported_ops": ["MTK BROM FRP Wipe", "HiOS Bloatware Cleaner", "Fastbootd Super Flasher", "Magisk init_boot Root", "Userdata Format"]
    },
    {
        "brand": "Tecno",
        "series": "Pova & Spark 2025 Series",
        "models": ["Pova 7 / 7 Pro 5G", "Spark 30 / 30 Pro / 30C", "Spark 20 Pro+"],
        "chipset": "MediaTek Dimensity 7025 / Helio G100 / G85",
        "supported_ops": ["MTK Preloader Format", "FRP Reset", "Fastboot Flasher", "HiOS Telemetry Removal"]
    },

    # --- INFINIX & ITEL ---
    {
        "brand": "Infinix",
        "series": "Note, Zero & GT Series",
        "models": ["Note 50 / 50 Pro 5G", "Zero 40 / 40 5G", "GT 20 Pro / GT 10 Pro", "Hot 50 / 50i"],
        "chipset": "MediaTek Dimensity 8020 / 7200 / 7020 & Helio G100 / G99",
        "supported_ops": ["MTK SLA Auth Skip", "XOS Bloatware Cleaner", "FRP Reset", "Fastbootd Flasher", "Magisk Root"]
    },
    {
        "brand": "itel",
        "series": "S & P Series (Transsion)",
        "models": ["itel S24 / S24 Ultra", "itel P55 / P55+", "itel A70 / A80"],
        "chipset": "Unisoc T606 / T612 & MediaTek Helio G85",
        "supported_ops": ["SPD Diag Port Reader", "Fastboot FRP Erase", "PAC Firmware Flasher", "Userdata Wipe"]
    },

    # --- SAMSUNG 2024/2025 FLAGSHIPS & MIDRANGE ---
    {
        "brand": "Samsung",
        "series": "Galaxy S24 / S25 & Foldables",
        "models": ["Galaxy S25 / S25+ / S25 Ultra", "Galaxy S24 FE", "Galaxy Z Fold 6 / Z Flip 6"],
        "chipset": "Snapdragon 8 Gen 3 / 8 Elite & Exynos 2400",
        "supported_ops": ["ADB Diagnostics", "Odin Download Mode", "CSC Switch", "Knox Telemetry", "OneUI Debloat"]
    },
    {
        "brand": "Samsung",
        "series": "Galaxy A & M 2024-2025 Series",
        "models": ["Galaxy A55 / A35 5G", "Galaxy A25 / A15", "Galaxy M55 / M35 5G"],
        "chipset": "Exynos 1480 / 1380 / 1330",
        "supported_ops": ["ADB Diagnostics", "Samsung Test Mode FRP", "EDL 9008 (QC models)", "Odin Flashing", "EFS Backup"]
    },

    # --- XIAOMI / REDMI / POCO 2024-2025 ---
    {
        "brand": "Xiaomi",
        "series": "Redmi Note & K 2024-2025 Series",
        "models": ["Redmi Note 14 / 14 Pro 5G", "Redmi Note 13 Pro+", "Redmi K80 / K80 Pro"],
        "chipset": "Qualcomm Snapdragon 7s Gen 2 / 8 Gen 3 & MediaTek Dimensity 7300",
        "supported_ops": ["Fastboot Flasher", "EDL 9008 Firehose", "MTK BROM Bypass", "HyperOS Debloat", "OEM Unlock"]
    },
    {
        "brand": "Xiaomi",
        "series": "POCO & Xiaomi Number Series",
        "models": ["POCO X7 / X7 Pro", "POCO F7 / F7 Pro", "Xiaomi 15 / 15 Ultra", "Redmi 14C / 13C"],
        "chipset": "Snapdragon 7+ Gen 3 / 8 Elite & MediaTek Dimensity 8400",
        "supported_ops": ["Fastboot Partition Flash", "EDL 9008 Partition Erase", "Anti-Rollback Check", "SafetyNet Pass Helper"]
    },

    # --- MOTOROLA & GOOGLE 2024-2025 ---
    {
        "brand": "Motorola",
        "series": "Moto G, Edge & Razr 2024-2025",
        "models": ["Moto G75 / G85 / G100 5G", "Moto Edge 60 / Edge 60 Fusion", "Moto Razr 50 / 50 Ultra"],
        "chipset": "Snapdragon 7 Gen 3 / 8 Gen 3 & MediaTek Dimensity 7300",
        "supported_ops": ["Fastboot Sparse Flasher", "Fastboot FRP Erase", "OEM Unlock", "Blankflash EDL Unbrick"]
    },
    {
        "brand": "Google",
        "series": "Pixel 9 & Pixel 8 Series",
        "models": ["Pixel 9 / 9 Pro / 9 Pro XL / 9 Pro Fold", "Pixel 8a"],
        "chipset": "Google Tensor G4",
        "supported_ops": ["Standard Fastboot Flasher", "OEM Bootloader Unlock", "Factory Image Sideload", "Magisk / KernelSU Root"]
    },

    # --- ONEPLUS & NOKIA / HMD ---
    {
        "brand": "OnePlus",
        "series": "OnePlus 13 & Nord 2024-2025",
        "models": ["OnePlus 13 / 13R", "OnePlus Nord 5 / Nord CE 5", "OnePlus Ace 5"],
        "chipset": "Snapdragon 8 Elite / 8 Gen 3 & Dimensity 8350",
        "supported_ops": ["Fastboot Flashing Unlock", "MSMDownloadTool EDL Helper", "Fastbootd Super Flasher", "Magisk Boot Root"]
    },
    {
        "brand": "Nokia / HMD",
        "series": "HMD Pulse & Nokia G / C Series",
        "models": ["HMD Pulse / Pulse Pro", "Nokia G42 / G60", "Nokia C32 / C22"],
        "chipset": "Unisoc T606 / T610 & Snapdragon 480+",
        "supported_ops": ["SPD Diag Port Reader", "Fastboot FRP Erase", "PAC Firmware Flasher", "Userdata Wipe"]
    }
]

def find_device_matches(model_str: str) -> List[Dict[str, any]]:
    matches = []
    query = model_str.lower()
    for cat in SUPPORTED_DEVICE_CATALOG:
        if query in cat["brand"].lower() or query in cat["series"].lower() or any(query in m.lower() for m in cat["models"]):
            matches.append(cat)
    return matches
