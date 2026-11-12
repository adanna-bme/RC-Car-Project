
import time
import serial


# ==========================================
# CONFIGURATION
# ==========================================

EEG_BAUD = 57600

CAR_BAUD = 9600

SEND_BLUETOOTH = True

# BLINK DETECTION
FORWARD_THRESHOLD = 900  # Activated by blinking
# Zero disables a direction until its threshold is configured.
BACKWARD_THRESHOLD = 0
LEFT_THRESHOLD = 0
RIGHT_THRESHOLD = 0
RESET_THRESHOLD = 300

# MOVEMENT TIMING
START_COOLDOWN_SECONDS = 1.0
STOP_COOLDOWN_SECONDS = 0.75
MAX_FORWARD_SECONDS = 5.0

# SIGNAL PROCESSING
WINDOW_SECONDS = 0.5
WARMUP_SECONDS = 4.0

# SAFETY AND COMMUNICATION
HEARTBEAT_SECONDS = 0.2
EEG_TIMEOUT_SECONDS = 1.5
QUALITY_TIMEOUT_SECONDS = 3.0


# ==========================================
# ROBOT CAR CLASS
# ==========================================

class RobotCar:

    def __init__(self, port, baud_rate):

        self.port = port
        self.baud_rate = baud_rate

        self.connection = None
        self.moving = False

    def connect(self):

        print("Connecting to HC-05...")

        self.connection = serial.Serial(
            self.port,
            self.baud_rate,
            timeout=0,
            write_timeout=0.3
        )

        print("Car Bluetooth connected!")

        self.stop()

    def send_command(self, command):

        if self.connection is not None:

            self.connection.write(
                command.encode("ascii")
            )

            self.connection.flush()

        print("COMMAND:", command)

    def forward(self):

        self.send_command("F")
        self.moving = True

    def backward(self):

        self.send_command("B")
        self.moving = True

    def left(self):

        self.send_command("L")
        self.moving = True

    def right(self):

        self.send_command("R")
        self.moving = True

    def stop(self):

        self.send_command("S")
        self.moving = False

    def close(self):

        if self.connection is not None:

            for _ in range(3):

                try:

                    self.connection.write(b"S")
                    self.connection.flush()

                    time.sleep(0.05)

                except (serial.SerialException, OSError):

                    print(
                        "Could not send STOP. "
                        "Check Arduino watchdog."
                    )

                    break

            self.connection.close()
            self.connection = None

        print("Car connection closed.")


# ==========================================
# EEG ROBOT CONTROLLER CLASS
# ==========================================

class EEGRobotController:

    def __init__(self, car, eeg_port):

        self.car = car
        self.eeg_port = eeg_port

        # MOVEMENT STATE
        self.moving = False
        self.active_direction = None
        self.blink_active = False

        self.last_blink = float("-inf")
        self.last_stop = float("-inf")
        self.last_heartbeat = 0.0

        self.forward_started = None

        # EEG STATE
        self.buffer = bytearray()
        self.window = []

        self.signal_quality = None
        self.last_quality = None

        self.last_data = 0.0
        self.start_time = 0.0
        self.window_start = 0.0

        self.was_healthy = False

    # ======================================
    # EEG PACKET PARSING
    # ======================================

    @staticmethod
    def parse_payload(payload):

        samples = []
        quality = None

        index = 0

        while index < len(payload):

            while (
                index < len(payload)
                and payload[index] == 0x55
            ):
                index += 1

            if index >= len(payload):
                break

            code = payload[index]
            index += 1

            if code >= 0x80:

                if index >= len(payload):
                    break

                size = payload[index]
                index += 1

            else:
                size = 1

            if index + size > len(payload):
                break

            value = payload[index:index + size]
            index += size

            if code == 0x80 and size == 2:

                raw = int.from_bytes(
                    value,
                    "big",
                    signed=True
                )

                samples.append(raw)

            elif code == 0x02 and size == 1:

                quality = value[0]

        return samples, quality

    @staticmethod
    def pop_packets(buffer):

        packets = []

        while True:

            sync = buffer.find(b"\xaa\xaa")

            if sync < 0:

                if buffer[-1:] == b"\xaa":
                    buffer[:] = b"\xaa"

                else:
                    buffer.clear()

                break

            if sync:
                del buffer[:sync]

            if len(buffer) < 3:
                break

            length = buffer[2]

            if length > 169:

                del buffer[0]
                continue

            packet_end = 3 + length + 1

            if len(buffer) < packet_end:
                break

            payload = bytes(
                buffer[3:3 + length]
            )

            checksum = buffer[3 + length]

            expected = (~sum(payload)) & 0xFF

            if expected == checksum:

                packets.append(payload)
                del buffer[:packet_end]

            else:

                del buffer[0]

        return packets

    # ======================================
    # EEG CONNECTION
    # ======================================

    def read_eeg(self, eeg):

        if eeg.in_waiting:

            incoming = eeg.read(
                min(eeg.in_waiting, 1024)
            )

            self.buffer.extend(incoming)

            packets = self.pop_packets(
                self.buffer
            )

            for payload in packets:

                samples, quality = (
                    self.parse_payload(payload)
                )

                if samples:

                    self.window.extend(samples)

                    self.last_data = time.monotonic()

                if quality is not None:

                    self.signal_quality = quality

                    self.last_quality = (
                        time.monotonic()
                    )

    # ======================================
    # SIGNAL QUALITY MONITORING
    # ======================================

    def check_signal_health(self, now):

        warmed_up = (
            now - self.start_time
            >= WARMUP_SECONDS
        )

        eeg_fresh = (
            now - self.last_data
            < EEG_TIMEOUT_SECONDS
        )

        contact_good = (
            self.signal_quality == 0
            and self.last_quality is not None
            and now - self.last_quality
            < QUALITY_TIMEOUT_SECONDS
        )

        healthy = (
            warmed_up
            and eeg_fresh
            and contact_good
        )

        if not healthy:

            if self.was_healthy:

                print(
                    "EEG signal/contact invalid"
                )

            self.stop_movement(
                "EEG signal/contact lost"
            )

            self.blink_active = False

            self.window.clear()
            self.window_start = now

        self.was_healthy = healthy

        return healthy

    # ======================================
    # MOVEMENT CONTROL
    # ======================================

    def start_movement(self, now, direction="forward"):

        movement = {
            "forward": self.car.forward,
            "backward": self.car.backward,
            "left": self.car.left,
            "right": self.car.right,
        }[direction]

        self.moving = True
        self.active_direction = direction

        self.forward_started = now

        print(direction.upper(), "requested")

        movement()

        self.last_heartbeat = now

    def backward(self, now):

        self.start_movement(now, "backward")

    def left(self, now):

        self.start_movement(now, "left")

    def right(self, now):

        self.start_movement(now, "right")

    def stop_movement(self, reason):

        if self.moving:

            self.moving = False
            self.active_direction = None

            self.forward_started = None

            self.last_stop = time.monotonic()

            print("STOP:", reason)

            self.car.stop()

    def check_max_forward_time(self, now):

        if (
            self.moving
            and self.forward_started is not None
            and now - self.forward_started
            >= MAX_FORWARD_SECONDS
        ):

            self.stop_movement(
                "maximum movement duration reached"
            )

    def send_heartbeat(self, now, healthy):

        if (
            self.moving
            and healthy
            and now - self.last_heartbeat
            >= HEARTBEAT_SECONDS
        ):

            getattr(self.car, self.active_direction)()

            self.last_heartbeat = now

    # ======================================
    # BLINK DETECTION
    # ======================================

    def process_blink(self, now):

        if len(self.window) < 20:
            return

        signal_range = (
            max(self.window) - min(self.window)
        )

        print("Signal range:", signal_range)

        # Select the highest configured threshold reached by this signal.
        # Ties use the direction order below.
        direction = None
        matched_threshold = 0
        for candidate, threshold in (
            ("forward", FORWARD_THRESHOLD),
            ("backward", BACKWARD_THRESHOLD),
            ("left", LEFT_THRESHOLD),
            ("right", RIGHT_THRESHOLD),
        ):
            if threshold > matched_threshold and signal_range >= threshold:
                direction = candidate
                matched_threshold = threshold

        # Reset blink detection
        if signal_range < RESET_THRESHOLD:

            self.blink_active = False

        # Detect blink
        elif (
            direction is not None
            and not self.blink_active
        ):

            self.blink_active = True

            if self.moving:

                required_cooldown = (
                    STOP_COOLDOWN_SECONDS
                )

            else:

                required_cooldown = (
                    START_COOLDOWN_SECONDS
                )

            allowed = (
                now - self.last_blink
                >= required_cooldown
            )

            if not self.moving:

                allowed = (
                    allowed
                    and now - self.last_stop
                    >= START_COOLDOWN_SECONDS
                )

            if allowed:

                self.last_blink = now

                print("BLINK DETECTED!")

                if self.moving:

                    self.stop_movement(
                        "intentional blink"
                    )

                else:

                    self.start_movement(now, direction)

    # ======================================
    # EEG PROCESSING LOOP
    # ======================================

    def process_eeg(self, eeg):

        self.start_time = time.monotonic()

        self.window_start = self.start_time

        self.last_data = self.start_time

        while True:

            self.read_eeg(eeg)

            now = time.monotonic()

            # Check EEG signal
            healthy = self.check_signal_health(
                now
            )

            # Check maximum movement duration
            self.check_max_forward_time(now)

            # Send movement heartbeat
            self.send_heartbeat(
                now,
                healthy
            )

            # Process EEG signal window
            if (
                now - self.window_start
                >= WINDOW_SECONDS
            ):

                if healthy:

                    self.process_blink(now)

                self.window.clear()

                self.window_start = now

            time.sleep(0.01)

    # ======================================
    # MAIN CONTROLLER
    # ======================================

    def run(self):

        try:

            if SEND_BLUETOOTH:

                self.car.connect()

            else:

                print(
                    "DRY RUN: Bluetooth disabled; "
                    "motors will not receive commands"
                )

            print(
                "Connecting to MindWave on",
                self.eeg_port
            )

            with serial.Serial(
                self.eeg_port,
                EEG_BAUD,
                timeout=0
            ) as eeg:

                print("MindWave connected!")

                print("Waiting for good EEG signal...")

                print(
                    "One eye squeeze = FORWARD/STOP"
                )

                print("Press Ctrl+C to end test.\n")

                self.process_eeg(eeg)

        except KeyboardInterrupt:

            print("\nStopped by user.")

        except (
            serial.SerialException,
            OSError
        ) as error:

            print("Serial error:", error)

        finally:

            self.stop_movement(
                "controller shutting down"
            )

            self.car.close()

            print("Controller closed.")

            print(
                "Turn off motor battery before handling."
            )


# ==========================================
# PROGRAM ENTRY POINT
# ==========================================

def main():

    car_port = input("Enter robot COM port: ").strip()
    eeg_port = input("Enter EEG Headset COM port: ").strip()

    # Create robot car object
    car = RobotCar(
        car_port,
        CAR_BAUD
    )

    # Create EEG controller object
    controller = EEGRobotController(car, eeg_port)

    # Start controller
    controller.run()


if __name__ == "__main__":

    main()
