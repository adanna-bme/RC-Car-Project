
"""Control the car from a terminal: W/A/S/D to move, F to stop, Q to quit."""

import os
import sys
import time
from contextlib import contextmanager

import serial


CAR_BAUD = 9600
HEARTBEAT_SECONDS = 0.2  # Must remain below the Arduino's 700 ms timeout.

# Keyboard keys and Bluetooth commands are different: keyboard F means STOP.
KEY_COMMANDS = {
    "w": (b"F", "FORWARD"),
    "a": (b"L", "LEFT"),
    "s": (b"B", "BACKWARD"),
    "d": (b"R", "RIGHT"),
    "f": (b"S", "STOP"),
}


@contextmanager
def keyboard_input():
    """Yield a nonblocking key reader and restore terminal settings on exit."""
    if not sys.stdin.isatty():
        raise RuntimeError("Run this controller in an interactive terminal.")

    if os.name == "nt":
        import msvcrt

        def read_key():
            if not msvcrt.kbhit():
                return None
            key = msvcrt.getwch()
            if key in ("\x00", "\xe0"):
                msvcrt.getwch()  # Ignore Windows special keys.
                return None
            return key

        yield read_key
    else:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        original_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)

            def read_key():
                if select.select([fd], [], [], 0)[0]:
                    return os.read(fd, 1).decode("ascii", errors="ignore")
                return None

            yield read_key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, original_settings)


def control_car(connection, read_key):
    """Latch the selected direction and repeat it until STOP or shutdown."""
    active_command = b"S"
    last_sent = time.monotonic()
    connection.write(active_command)

    while True:
        key = read_key()
        if key is not None:
            key = key.lower()
            if key in ("q", "\x03"):
                return

            if key in KEY_COMMANDS:
                active_command, label = KEY_COMMANDS[key]
                connection.write(active_command)
                last_sent = time.monotonic()
                print(label, flush=True)

        now = time.monotonic()
        if active_command != b"S" and now - last_sent >= HEARTBEAT_SECONDS:
            connection.write(active_command)
            last_sent = now

        time.sleep(0.01)


def main():
    connection = None
    try:
        port = input("Enter robot serial port (COM5 or /dev/rfcomm0): ").strip()
        if not port:
            print("A robot serial port is required.")
            return

        with keyboard_input() as read_key:
            connection = serial.Serial(
                port, CAR_BAUD, timeout=0, write_timeout=0.3
            )
            print("Car connected. W: forward | A: left | S: backward | D: right")
            print("F: stop | Q or Ctrl+C: quit. Movement continues after key release.")
            control_car(connection, read_key)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except (serial.SerialException, OSError, RuntimeError) as error:
        print("Controller error:", error)
    finally:
        if connection is not None:
            try:
                # Repeat STOP to improve delivery before closing Bluetooth.
                for _ in range(3):
                    connection.write(b"S")
                    time.sleep(0.05)
            except (serial.SerialException, OSError) as error:
                print("Could not send STOP:", error)
            finally:
                connection.close()
        print("Controller closed.")


if __name__ == "__main__":
    main()
