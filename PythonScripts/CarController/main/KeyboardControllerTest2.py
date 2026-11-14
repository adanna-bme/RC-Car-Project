
import tkinter as tk
import serial
import time

# =====================================
# KEYBOARD ROBOT CAR CONTROLLER
# Arduino + HC-05 Bluetooth
# =====================================

CAR_PORT = "COM7"
CAR_BAUD = 9600

# Arduino stops after 700 ms without
# receiving another movement command.
HEARTBEAT_MS = 200

KEY_COMMANDS = {
    "w": ("F", "FORWARD"),
    "a": ("L", "LEFT"),
    "s": ("B", "BACKWARD"),
    "d": ("R", "RIGHT"),
    "f": ("S", "STOP"),
}

car = None
active_command = "S"
closing = False


def send_command(command):
    global car

    if car is not None:
        try:
            car.write(command.encode("ascii"))
        except serial.SerialException as error:
            print("Bluetooth error:", error)
            emergency_stop()


def emergency_stop():
    global active_command
    active_command = "S"
    status_label.config(
        text="STOPPED",
        fg="red"
    )


def key_pressed(event):
    global active_command

    key = event.keysym.lower()

    if key == "q":
        close_program()
        return

    if key in KEY_COMMANDS:
        command, label = KEY_COMMANDS[key]

        active_command = command

        status_label.config(
            text=label,
            fg="red" if command == "S" else "green"
        )

        send_command(command)
        print("COMMAND:", command, label)


def heartbeat():
    if closing:
        return

    if active_command != "S":
        send_command(active_command)

    root.after(HEARTBEAT_MS, heartbeat)


def close_program():
    global closing, active_command

    if closing:
        return

    closing = True
    active_command = "S"

    if car is not None:
        try:
            for _ in range(3):
                car.write(b"S")
                time.sleep(0.05)
            car.close()
        except serial.SerialException:
            pass

    root.destroy()


# =====================================
# CONNECT TO CAR
# =====================================

try:
    car = serial.Serial(
        CAR_PORT,
        CAR_BAUD,
        timeout=0,
        write_timeout=0.3
    )

    print("Connected to robot on", CAR_PORT)

except serial.SerialException as error:
    print("Could not connect:", error)
    raise SystemExit


# =====================================
# BUILD CONTROL WINDOW
# =====================================

root = tk.Tk()
root.title("EEG Robot Car - Keyboard Control")
root.geometry("420x330")
root.resizable(False, False)

tk.Label(
    root,
    text="ROBOT CAR CONTROLLER",
    font=("Arial", 17, "bold")
).pack(pady=15)

status_label = tk.Label(
    root,
    text="STOPPED",
    font=("Arial", 22, "bold"),
    fg="red"
)
status_label.pack(pady=12)

tk.Label(
    root,
    text="W = Forward\n"
         "A = Left     D = Right\n"
         "S = Backward\n"
         "F = STOP\n"
         "Q = Quit",
    font=("Arial", 13),
    justify="center"
).pack(pady=10)

tk.Label(
    root,
    text="Click this window, then press a key.\n"
         "Movement continues until STOP.",
    font=("Arial", 10),
    fg="gray"
).pack(pady=10)

root.bind("<KeyPress>", key_pressed)
root.protocol("WM_DELETE_WINDOW", close_program)

# Start safely stopped
send_command("S")

root.after(HEARTBEAT_MS, heartbeat)

root.mainloop()

print("Controller closed.")
