
import serial
import time
import csv
import statistics

# EEG FACIAL EXPRESSION EXPERIMENT

EEG_PORT = "COM10"
EEG_BAUD = 57600

WINDOW_SECONDS = 0.5
TRIAL_SECONDS = 4

GESTURES = [
    "neutral",
    "eye_squeeze",
    "eyebrow_raise",
    "eyebrow_furrow",
    "smile"
]

TRIALS_PER_GESTURE = 3

results = []


def extract_packets(buffer):
    packets = []

    while True:
        start = buffer.find(b"\xaa\xaa")

        if start == -1:
            if buffer[-1:] == b"\xaa":
                buffer[:] = b"\xaa"
            else:
                buffer.clear()
            break

        del buffer[:start]

        if len(buffer) < 3:
            break

        length = buffer[2]

        if length > 169:
            del buffer[0]
            continue

        end = 3 + length + 1

        if len(buffer) < end:
            break

        payload = bytes(buffer[3:3 + length])
        checksum = buffer[3 + length]

        if ((~sum(payload)) & 255) == checksum:
            packets.append(payload)
            del buffer[:end]
        else:
            del buffer[0]

    return packets


def decode(payload):
    samples = []
    quality = None
    i = 0

    while i < len(payload):
        while i < len(payload) and payload[i] == 0x55:
            i += 1

        if i >= len(payload):
            break

        code = payload[i]
        i += 1

        if code >= 0x80:
            if i >= len(payload):
                break
            size = payload[i]
            i += 1
        else:
            size = 1

        if i + size > len(payload):
            break

        data = payload[i:i + size]
        i += size

        if code == 0x80 and size == 2:
            samples.append(
                int.from_bytes(data, "big", signed=True)
            )

        elif code == 0x02 and size == 1:
            quality = data[0]

    return samples, quality


def record_trial(eeg, gesture, trial):
    print("\nRecording:", gesture, "Trial:", trial)
    print("Perform the expression when prompted.")
    print("Recording for", TRIAL_SECONDS, "seconds")

    eeg.reset_input_buffer()
    buffer = bytearray()
    samples = []

    quality = None
    quality_time = None
    window_start = time.monotonic()
    end_time = window_start + TRIAL_SECONDS

    while time.monotonic() < end_time:

        if eeg.in_waiting:
            buffer.extend(
                eeg.read(min(eeg.in_waiting, 1024))
            )

            for packet in extract_packets(buffer):
                raw, q = decode(packet)
                samples.extend(raw)

                if q is not None:
                    quality = q
                    quality_time = time.monotonic()

        now = time.monotonic()

        if now - window_start >= WINDOW_SECONDS:

            if len(samples) >= 20:
                signal_range = max(samples) - min(samples)
                rms = (
                    sum(x * x for x in samples)
                    / len(samples)
                ) ** 0.5

                contact_ok = (
                    quality == 0
                    and quality_time is not None
                    and now - quality_time < 3.0
                )

                print(
                    "Range:", signal_range,
                    "| RMS:", round(rms, 1),
                    "| Contact:", contact_ok
                )

                results.append({
                    "gesture": gesture,
                    "trial": trial,
                    "range": signal_range,
                    "rms": round(rms, 2),
                    "contact_ok": contact_ok
                })

            samples.clear()
            window_start = now

        time.sleep(0.01)

    print("Trial complete!")


def main():
    print("EEG FACIAL EXPRESSION TEST")
    print("No motor commands will be sent.")
    print("Connecting to MindWave:", EEG_PORT)

    with serial.Serial(
        EEG_PORT, EEG_BAUD, timeout=0
    ) as eeg:

        print("Connected!")
        print("Adjust headset for good contact.")
        input("Press Enter when ready...")

        for gesture in GESTURES:

            print("\n========================")
            print("GESTURE:", gesture.upper())
            print("========================")

            for trial in range(1, TRIALS_PER_GESTURE + 1):

                input(
                    "Press Enter to prepare trial "
                    + str(trial) + "..."
                )

                print("Get ready...")
                time.sleep(2)

                record_trial(eeg, gesture, trial)

                print("Relax your face.")
                time.sleep(2)

    filename = "facial_expression_results.csv"

    with open(
        filename, "w", newline="", encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "gesture", "trial", "range",
                "rms", "contact_ok"
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n===== RESULTS SUMMARY =====")

    for gesture in GESTURES:

        values = [
            row["range"]
            for row in results
            if row["gesture"] == gesture
            and row["contact_ok"]
        ]

        if values:
            print(
                gesture,
                "| Median:", statistics.median(values),
                "| Min:", min(values),
                "| Max:", max(values)
            )
        else:
            print(gesture, "| No valid readings")

    print("\nResults saved to:", filename)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExperiment interrupted.")
    except serial.SerialException as error:
        print("Connection error:", error)
