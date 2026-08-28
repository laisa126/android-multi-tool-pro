"""
Android Multi-Tool Pro - OEM Bloatware Database & Diagnostics
Curated lists of OEM pre-installed bloatware packages safe to disable,
plus hardware test-point references including Tecno Camon 50 Pro.
"""

BLOATWARE_PRESETS = {
    "Samsung": [
        "com.samsung.android.bixby.agent",
        "com.samsung.android.bixby.wakeup",
        "com.samsung.android.bixbyvision.framework",
        "com.samsung.android.game.gamehome",
        "com.samsung.android.game.gametools",
        "com.sec.android.app.sbrowser",
        "com.samsung.android.kidsinstaller",
        "com.samsung.android.app.spage",
        "com.microsoft.skydrive",
        "com.facebook.katana",
        "com.facebook.system",
        "com.facebook.appmanager",
        "com.facebook.services"
    ],
    "Xiaomi / Redmi / POCO": [
        "com.miui.analytics",
        "com.miui.msa.global",
        "com.xiaomi.mipicks",
        "com.miui.bugreport",
        "com.miui.yellowpage",
        "com.miui.hybrid",
        "com.miui.hybrid.accessory",
        "com.miui.cleanmaster",
        "com.miui.videoplayer",
        "com.miui.player",
        "com.facebook.katana",
        "com.facebook.system"
    ],
    "Transsion (Tecno / Infinix / itel - HiOS 14/15/16)": [
        "com.transsion.hilauncher",
        "com.transsion.phonemaster",
        "com.transsion.aha",
        "com.transsion.magicshow",
        "com.transsion.carlcare",
        "com.transsion.palmpay",
        "com.transsion.boomplayer",
        "com.talpa.shareme",
        "com.transsion.tecnospot",
        "com.transsion.smartpanel",
        "com.transsion.vskit",
        "com.transsion.molink",
        "com.transsion.letswitch"
    ],
    "BBK (Oppo / Realme / Vivo)": [
        "com.oppo.market",
        "com.nearme.gamecenter",
        "com.coloros.gamespace",
        "com.oppo.quicksearchbox",
        "com.vivo.browser",
        "com.vivo.appstore",
        "com.bbk.theme",
        "com.vivo.game"
    ],
    "Google Safe Debloat (Generic)": [
        "com.google.android.apps.tachyon",
        "com.google.android.videos",
        "com.google.android.music",
        "com.google.android.apps.photos",
        "com.google.android.apps.docs",
        "com.google.android.apps.wellbeing"
    ]
}

TEST_POINT_DATABASE = [
    {
        "brand": "Tecno",
        "model": "Camon 50 Pro 5G (TECNO CN5c)",
        "chipset": "MediaTek Dimensity 7400 Ultimate / Helio G200",
        "mode": "MTK Preloader / BROM VCOM",
        "instructions": "NO DISASSEMBLY REQUIRED. Power off phone completely (hold Power + Vol Down for 10s if screen is locked). Press and hold Volume Up + Volume Down simultaneously. Connect high-quality Type-C cable to Windows 11 PC. The tool catches the MTK Preloader USB VCOM Port within 1.5 seconds, bypasses auth, and executes FRP wipe or userdata format."
    },
    {
        "brand": "Tecno",
        "model": "Camon 19 / 20 / 30 Pro",
        "chipset": "MediaTek Helio G96/G99 & Dimensity 8050/8200",
        "mode": "MTK Preloader",
        "instructions": "Power off phone. Hold Volume Down or Volume Up+Down. Insert Type-C cable. Multi-tool executes one-click auth bypass and formats FRP partition."
    },
    {
        "brand": "Xiaomi",
        "model": "Redmi Note 8 / 8T (Ginkgo)",
        "chipset": "Qualcomm Snapdragon 665",
        "mode": "EDL 9008",
        "instructions": "Disconnect battery. Short 2 test points located near the rear camera flex connector using tweezers. Connect USB cable while holding tweezers. Device Manager will show 'Qualcomm HS-USB QDLoader 9008'."
    },
    {
        "brand": "Xiaomi",
        "model": "Redmi 9A / 9C (Dandelion/Angelica)",
        "chipset": "MediaTek Helio G25/G35",
        "mode": "MTK BROM / Preloader",
        "instructions": "Power off device. Hold Volume Down or short KCOLO test point to ground. Insert USB cable. Tool bypasses SLA/DAA security handshake automatically."
    },
    {
        "brand": "Samsung",
        "model": "Galaxy A12 / A03s / A04e",
        "chipset": "MediaTek MT6765",
        "mode": "MTK BROM Test Point",
        "instructions": "Remove back cover. Disconnect battery cable. Locate the DAT0 / CLK test point beside eMMC shield. Short to ground and connect USB. Allows one-click FRP wipe and factory reset."
    },
    {
        "brand": "Samsung",
        "model": "Galaxy A32 / A52 / A72",
        "chipset": "Qualcomm Snapdragon 720G",
        "mode": "EDL 9008 Test Point",
        "instructions": "Locate two gold pads underneath motherboard sub-board flex. Short pins to ground and insert Type-C cable. Bypasses Knox bit check for emergency unbrick."
    }
]
