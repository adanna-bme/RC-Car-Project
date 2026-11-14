
import time
import serial

# ==========================================
# EEG ROBOT CAR CONTROLLER - V3
# MindWave Mobile + HC-05 + Arduino Uno
# ==========================================

# BLUETOOTH CONNECTIONS
EEG_PORT = None
EEG_BAUD = 57600

CAR_PORT = None
CAR_BAUD = 9600

# True = control physical car
# False = dry-run simulation
SEND_BLUETOOTH = True

# BLINK DETECTION
BLINK_THRESHOLD = 900
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


def parse_payload(payload):
    """Decode raw EEG and signal quality."""

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
                value, "big", signed=True
            )
            samples.append(raw)

        elif code == 0x02 and size == 1:
            quality = value[0]

    return samples, quality


def pop_packets(buffer):
    """Extract valid MindWave packets."""

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

        payload = bytes(buffer[3:3 + length])
        checksum = buffer[3 + length]

        expected = (~sum(payload)) & 0xFF

        if expected == checksum:
            packets.append(payload)
            del buffer[:packet_end]
        else:
            del buffer[0]

    return packets


def main():

    car = None
    moving = False
    blink_active = False

    last_blink = float("-inf")
    last_stop = float("-inf")
    last_heartbeat = 0.0

    forward_started = None

    def send(command):

        if car is not None:
            car.write(command.encode("ascii"))
            car.flush()

        print("COMMAND:", command)

    def stop(reason):

        nonlocal moving
        nonlocal forward_started
        nonlocal last_stop

        if moving:

            moving = False
            forward_started = None
            last_stop = time.monotonic()

            print("STOP:", reason)
            send("S")

    try:

        if SEND_BLUETOOTH:

            print("Connecting to HC-05...")

            car = serial.Serial(
                CAR_PORT,
                CAR_BAUD,
                timeout=0,
                write_timeout=0.3
            )

            send("S")

        else:
            print(
                "DRY RUN: Bluetooth disabled; "
                "motors will not receive commands"
            )

        print(
            "Connecting to MindWave on",
            EEG_PORT
        )

        with serial.Serial(
            EEG_PORT,
            EEG_BAUD,
            timeout=0
        ) as eeg:

            print("MindWave connected!")
            print("Waiting for good EEG signal...")
            print("One eye squeeze = FORWARD/STOP")
            print("Press Ctrl+C to end test.\n")

            start = time.monotonic()
            window_start = start
            last_data = start

            last_quality = None
            signal_quality = None

            buffer = bytearray()
            window = []

            was_healthy = False

            while True:

                now = time.monotonic()

                if eeg.in_waiting:

                    incoming = eeg.read(
                        min(eeg.in_waiting, 1024)
                    )

                    buffer.extend(incoming)

                    for payload in pop_packets(buffer):

                        samples, quality = (
                            parse_payload(payload)
                        )

                        if samples:
                            window.extend(samples)
                            last_data = time.monotonic()

                        if quality is not None:
                            signal_quality = quality
                            last_quality = time.monotonic()

                now = time.monotonic()

                warmed_up = (
                    now - start >= WARMUP_SECONDS
                )

                eeg_fresh = (
                    now - last_data
                    < EEG_TIMEOUT_SECONDS
                )

                contact_good = (
                    signal_quality == 0
                    and last_quality is not None
                    and now - last_quality
                    < QUALITY_TIMEOUT_SECONDS
                )

                healthy = (
                    warmed_up
                    and eeg_fresh
                    and contact_good
                )

                if not healthy:

                    if was_healthy:
                        print(
                            "EEG signal/contact invalid"
                        )

                    stop("EEG signal/contact lost")

                    blink_active = False
                    window.clear()
                    window_start = now

                was_healthy = healthy

                if (
                    moving
                    and forward_started is not None
                    and now - forward_started
                    >= MAX_FORWARD_SECONDS
                ):
                    stop(
                        "maximum forward duration reached"
                    )

                if (
                    moving
                    and healthy
                    and now - last_heartbeat
                    >= HEARTBEAT_SECONDS
                ):

                    send("F")
                    last_heartbeat = now

                if now - window_start >= WINDOW_SECONDS:

                    if healthy and len(window) >= 20:

                        signal_range = (
                            max(window) - min(window)
                        )

                        print(
                            "Signal range:",
                            signal_range
                        )

                        if signal_range < RESET_THRESHOLD:
                            blink_active = False

                        elif (
                            signal_range >= BLINK_THRESHOLD
                            and not blink_active
                        ):

                            blink_active = True

                            if moving:
                                required_cooldown = (
                                    STOP_COOLDOWN_SECONDS
                                )
                            else:
                                required_cooldown = (
                                    START_COOLDOWN_SECONDS
                                )

                            allowed = (
                                now - last_blink
                                >= required_cooldown
                            )

                            if not moving:

                                allowed = (
                                    allowed
                                    and now - last_stop
                                    >= START_COOLDOWN_SECONDS
                                )

                            if allowed:

                                last_blink = now

                                print("BLINK DETECTED!")

                                if moving:

                                    stop("intentional blink")

                                else:

                                    moving = True
                                    forward_started = now

                                    print(
                                        "FORWARD requested"
                                    )

                                    send("F")
                                    last_heartbeat = now

                    window.clear()
                    window_start = now

                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nStopped by user.")

    except (serial.SerialException, OSError) as error:
        print("Serial error:", error)

    finally:

        if car is not None:

            for _ in range(3):

                try:
                    car.write(b"S")
                    car.flush()
                    time.sleep(0.05)

                except (serial.SerialException, OSError):
                    print(
                        "Could not send STOP. "
                        "Check Arduino watchdog."
                    )
                    break

            car.close()

        print("Controller closed.")
        print("Turn off motor battery before handling.")


if __name__ == "__main__":
    main()
