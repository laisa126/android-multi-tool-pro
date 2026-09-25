"""
Android Multi-Tool Pro - Sequential Workflow & Process Tutorial Engine
Guides technicians through the exact next steps after any operation completes
(USB Connection, Admin Security Plugin Removal, Factory Reset, FRP Reset, Bootloader Unlock, Rooting).
"""


# GUIDED STEP-BY-STEP WIZARD FOR USB PLUG-IN & ADMIN PLUGIN REMOVAL
USB_PLUGGED_WIZARD = {
    "workflow_id": "TECNO_ADMIN_PLUGIN_REMOVAL",
    "title": "Guided Step-by-Step: Tecno Camon 50 Pro Admin App Security Plugin Removal",
    "total_steps": 6,
    "steps": [
        {
            "step": 1,
            "title": "USB Connected & Debugging Authorization",
            "phone_action": "Check phone display. If 'Allow USB debugging?' appears, tap 'Always allow from this computer' then tap 'Allow'. Keep screen unlocked.",
            "tool_action": "Click 'Identify Device' to verify the ADB handshake with the MediaTek Dimensity 7400 chipset.",
            "button_text": "Step 1: Identify Device",
            "api_action": "read_info",
            "tab_target": "tab-info"
        },
        {
            "step": 2,
            "title": "Detect Active Admin Security Plugins",
            "phone_action": "Do NOT tap or disconnect anything on the phone screen. Leave USB connected.",
            "tool_action": "Click 'Scan Active Admins' to query the Device Policy Manager for active packages (e.g. Carlcare, PalmPay, PayJoy, com.android.security.plugin).",
            "button_text": "Step 2: Scan Admins",
            "api_action": "list_admins",
            "tab_target": "tab-camon50"
        },
        {
            "step": 3,
            "title": "Strip Overlay & Hijack AppOps (Kill Lockscreen Banner)",
            "phone_action": "Notice the screen: Any persistent lockscreen overlay or greyed-out banner will immediately disappear.",
            "tool_action": "Click 'Neutralize Overlay' to revoke SYSTEM_ALERT_WINDOW, RUN_IN_BACKGROUND, and START_FOREGROUND via AppOps.",
            "button_text": "Step 3: Neutralize Overlay",
            "api_action": "neutralize_security_plugin",
            "tab_target": "tab-camon50"
        },
        {
            "step": 4,
            "title": "Deactivate Device Admin & Wipe Local Credentials",
            "phone_action": "Phone remains on home screen. Settings -> Device admin apps will show the plugin is no longer managing the device.",
            "tool_action": "Click 'Deactivate Admin' to run 'dpm remove-active-admin' and 'pm clear' to wipe all cached MDM tokens.",
            "button_text": "Step 4: Deactivate Admin",
            "api_action": "neutralize_security_plugin",
            "tab_target": "tab-camon50"
        },
        {
            "step": 5,
            "title": "Freeze HiOS MDM & Provisioning Daemons",
            "phone_action": "Phone stays on. HiOS zero-touch setup wizard and cloud enrollment daemons are frozen permanently.",
            "tool_action": "Click 'Freeze MDM & Daemons' to set 'device_provisioned=1' and disable background enrollment agents.",
            "button_text": "Step 5: Freeze MDM",
            "api_action": "transsion_mdm",
            "tab_target": "tab-camon50"
        },
        {
            "step": 6,
            "title": "Reboot & Verify Final Operation State",
            "phone_action": "Phone will reboot into Android OS. Once on desktop, you can safely connect Wi-Fi and insert your SIM card. The plugin will never return.",
            "tool_action": "Click 'Reboot System' to finalize. Servicing is 100% complete!",
            "button_text": "Step 6: Reboot System (Finish)",
            "api_action": "reboot",
            "tab_target": "tab-reboot"
        }
    ]
}

WORKFLOW_TUTORIALS = {
    "TECNO_ADMIN_PLUGIN_REMOVAL": {
        "title": "Step-by-Step: Removing Admin App Security Plugin (Tecno Camon 50 Pro)",
        "current_status": "USB Cable Plugged In -> Interactive Step-by-Step Guided Wizard Active.",
        "next_steps": [
            {
                "step": 1,
                "title": "Authorize USB Debugging",
                "action": "On phone: Tap 'Always allow from this computer' on the USB debugging popup. In tool: Click 'Identify Device'."
            },
            {
                "step": 2,
                "title": "Scan Active Device Admins",
                "action": "Click 'Scan Admins' in Camon 50 Suite to detect the exact component package name controlling the device."
            },
            {
                "step": 3,
                "title": "Neutralize AppOps Overlay Rights",
                "action": "Click 'Neutralize Plugin' to revoke SYSTEM_ALERT_WINDOW. This kills the overlay lockscreen immediately."
            },
            {
                "step": 4,
                "title": "Unregister Admin & Clear Data",
                "action": "Tool issues 'dpm remove-active-admin' and 'pm clear' to wipe tokens."
            },
            {
                "step": 5,
                "title": "Freeze HiOS MDM Enrollment",
                "action": "Click 'Freeze HiOS MDM & PayJoy' to lock global device_provisioned = 1 and user_setup_complete = 1."
            },
            {
                "step": 6,
                "title": "Reboot & Connect Network",
                "action": "Reboot device. Connect Wi-Fi and insert SIM. Device is permanently clean and unlocked."
            }
        ]
    },

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
