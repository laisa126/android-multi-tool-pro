"""
Android Multi-Tool Pro - Sequential Workflow & Process Tutorial Engine
Guides technicians through the exact next steps after any operation completes
(Factory Reset, FRP Reset, Bootloader Unlock, Rooting, or Debloat).
"""

from typing import Dict, List

WORKFLOW_TUTORIALS = {
    "FACTORY_RESET_COMPLETE": {
        "title": "Operation Finished: Factory Reset / Userdata Wipe",
        "current_status": "All personal data, pattern/PIN screen locks, and app cache have been wiped.",
        "next_steps": [
            {
                "step": 1,
                "title": "First Boot Time Warning",
                "action": "Allow the phone 2 to 4 minutes to rebuild the Dalvik cache and encrypt userdata on first boot. Do not unplug battery or force shutdown."
            },
            {
                "step": 2,
                "title": "Setup Wizard Walkthrough",
                "action": "Select your language and region. Connect to Wi-Fi. If prompted for an old Google Account, use the 'FRP & Screen Lock' tab to bypass."
            },
            {
                "step": 3,
                "title": "Re-Enable Technician Access",
                "action": "Once on the home screen: Go to Settings -> About Phone -> Tap 'Build Number' 7 times -> Go to Developer Options -> Turn ON 'USB Debugging'."
            },
            {
                "step": 4,
                "title": "Recommended Next Action in Tool",
                "action": "Switch to the 'Debloat HiOS / Apps' tab to clean out pre-installed bloatware (PalmPay, AHA games) while the phone is fresh."
            }
        ]
    },

    "FRP_BYPASS_COMPLETE": {
        "title": "Operation Finished: FRP (Google Account) Bypass",
        "current_status": "Persistent Google Account Lock has been cleared from config/frp blocks.",
        "next_steps": [
            {
                "step": 1,
                "title": "Device Clean Reboot",
                "action": "Click 'Reboot System' in the Reboot tab (or hold Power on phone for 5 seconds)."
            },
            {
                "step": 2,
                "title": "Skip Account Screen",
                "action": "On the initial Welcome setup screen, tap 'Skip' when asked to sign in with Google or connect to Wi-Fi."
            },
            {
                "step": 3,
                "title": "Bind Your Own Account",
                "action": "Once on the Home launcher, go to Settings -> Accounts -> Add your personal Google Account to register new cloud backup tokens."
            },
            {
                "step": 4,
                "title": "Set New Screen Security",
                "action": "Go to Settings -> Security -> Set a new PIN or Fingerprint to re-initialize Android Keystore."
            }
        ]
    },

    "BOOTLOADER_UNLOCK_COMPLETE": {
        "title": "Operation Finished: Bootloader Unlocked (flashing unlock)",
        "current_status": "Bootloader security verification is disengaged. Custom kernels & recoveries can now be flashed.",
        "next_steps": [
            {
                "step": 1,
                "title": "Data Wipe Automatic Trigger",
                "action": "The phone screen will display an orange warning: 'Your device software cannot be checked for corruption'. Press Power to proceed. Android will automatically wipe userdata for security."
            },
            {
                "step": 2,
                "title": "Initial Setup & Developer Re-activation",
                "action": "Walk through setup wizard quickly. Go to Settings -> About Phone -> Tap Build Number 7 times -> Re-enable USB Debugging."
            },
            {
                "step": 3,
                "title": "Next Technician Action: Rooting or Custom ROM",
                "action": "Switch to the 'Root & Magisk' tab to flash Magisk/KernelSU patched init_boot.img, OR switch to 'Fastboot Flasher' to flash TWRP/OrangeFox."
            }
        ]
    },

    "ROOT_FLASH_COMPLETE": {
        "title": "Operation Finished: Magisk / KernelSU Root Image Flashed",
        "current_status": "Patched init_boot kernel and disabled vbmeta verification written to storage.",
        "next_steps": [
            {
                "step": 1,
                "title": "Boot System Normally",
                "action": "Execute 'fastboot reboot' or click 'Reboot System' in tool. Phone will boot into Android OS."
            },
            {
                "step": 2,
                "title": "Open or Install Magisk App",
                "action": "If Magisk app is not visible on homescreen: Click 'Install Magisk Manager APK' in the Root tab. Open the Magisk app on phone."
            },
            {
                "step": 3,
                "title": "Perform Magisk 'Additional Setup'",
                "action": "Magisk will prompt: 'Requires Additional Setup. Do you want to proceed?'. Tap 'OK'. The phone will reboot in 5 seconds."
            },
            {
                "step": 4,
                "title": "Verify Superuser in Multi-Tool",
                "action": "Once rebooted, click 'Check Root Status' in the Root tab. Tool should confirm: 'Device is Rooted (uid=0)'."
            },
            {
                "step": 5,
                "title": "SafetyNet / Play Integrity Fix",
                "action": "In Magisk settings, enable 'Zygisk' and configure 'Enforce DenyList' for banking apps."
            }
        ]
    },

    "DEBLOAT_COMPLETE": {
        "title": "Operation Finished: OEM Bloatware Cleaned",
        "current_status": "Unwanted preloaded background telemetry apps disabled/uninstalled for user 0.",
        "next_steps": [
            {
                "step": 1,
                "title": "Quick Reboot to Clear Memory",
                "action": "Restart the device once so the Android system clears stale background services from RAM."
            },
            {
                "step": 2,
                "title": "Check Core Functions",
                "action": "Test that the Camera, Phone Dialer, and Default SMS app function normally."
            },
            {
                "step": 3,
                "title": "Enjoy Optimized Performance",
                "action": "RAM usage drops by 1.2 GB to 2 GB, and background battery drain is reduced."
            }
        ]
    }
}
