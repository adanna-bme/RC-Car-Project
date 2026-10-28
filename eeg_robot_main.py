
import time

# EEG Robot Car - Automatic Blink Controller

blink_threshold = 300
cooldown = 2.0

car_moving = False
last_blink_time = float("-inf")
blink_active = False


def send_command(command):
    # Simulating wireless communication
    print("Sending to Arduino:", command)


print("EEG ROBOT CAR")
print("Enter simulated EEG readings.")
print("Type Q to quit.")

while True:
    user_input = input("EEG reading: ").strip()

    if user_input.upper() == "Q":
        send_command("S")
        break

    try:
        eeg_value = int(user_input)
    except ValueError:
        print("Please enter a valid number.")
        continue

    current_time = time.monotonic()

    if eeg_value > blink_threshold:

        if not blink_active:
            blink_active = True

            if current_time - last_blink_time >= cooldown:

                last_blink_time = current_time
                car_moving = not car_moving

                if car_moving:
                    send_command("F")
                    print("Blink detected! Moving forward.")

                else:
                    send_command("S")
                    print("Blink detected! Stopping.")

            else:
                print("Blink ignored: cooldown active.")

    else:
        blink_active = False
        print("Waiting for intentional blink...")
