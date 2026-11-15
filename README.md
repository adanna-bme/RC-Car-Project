# MindMotor
### An EEG-Based, Blink-Controlled Robotic Car

<img width="1080" height="2340" alt="Screenshot_20261115_003757_Gallery" src="https://github.com/user-attachments/assets/f58535d2-084b-421b-b38d-4407545c9dd6" />
<img width="4000" height="3000" alt="20261114_214824" src="https://github.com/user-attachments/assets/004ecda4-ed05-4d2e-a42a-b2f2cf7722fe" />



## Video Demonstration

[Watch Our Project Demonstration](https://canva.link/8vbn32rx8sowu44)



## Meet the Team

### Adanna Oboegbulem
**Initial Planning, EEG Signal Processing & Bluetooth Integration**

- Came up with the initial project plan and helped develop the overall concept.
- Worked on integrating the NeuroSky MindWave headset and interpreting intentional blink signals.
- Handled Bluetooth integration between the headset, laptop, and robotic car.

### Christian Napier
**Hardware Assembly & Integration**

- Assembled the physical robotic car and its components.
- Handled the wiring, electrical connections, and hardware integration.
- Worked on connecting the Arduino, motor driver, and other components.

**Together:** We both worked on programming, testing, troubleshooting, and getting the hardware and software to function as one complete system.

## Project Description

MindMotor is an EEG-headset-controlled robotic car that uses intentional eye blinks to control forward movement and stopping. By combining neuroscience, programming, Bluetooth communication, and robotics, we wanted to explore how electrical signals from the human body could be used to control technology without traditional physical inputs.

While our prototype is on a much smaller scale than advanced brain-computer interfaces, it demonstrates how similar ideas could potentially be explored to make hands-free technology more accessible.

### Features

- **Hands-Free Control:** The first intentional blink moves the car forward, while the second stops it.
- **EEG-Based Signal Detection:** Uses raw electrical signals associated with eye movements and facial muscle activity.
- **Wireless Communication:** Sends commands from Python to the robotic car through Bluetooth.
- **Arduino Motor Control:** Uses an Arduino Uno and motor driver to control movement.
- **Safety Features:** Automatically stops the car if EEG data is lost or the maximum movement time is reached.

### How It Works

While we couldn't exactly replicate the science fiction of translating thoughts into commands, we were able to recreate a smaller version using raw EEG data, particularly electrical activity associated with EOG (electrooculography), which measures electrical changes caused by eye movements.

Instead of controlling the car with our thoughts, we used intentional eye blinks to control its movement.

1. **NeuroSky MindWave:** Records raw electrical signals from the forehead, including those associated with eye blinks.
2. **Python:** Processes the signals and detects intentional blinks by measuring changes in amplitude.
3. **Bluetooth (HC-05):** Wirelessly sends forward or stop commands to the robotic car.
4. **Arduino Uno:** Receives the commands and communicates with the motor driver.
5. **Robot Car:** Moves forward after the first recognized blink and stops after the second.

**System Loop:**

Intentional Blink → MindWave detects electrical activity → Python processes the signal → Bluetooth sends a command → Arduino controls the motors → Car moves or stops

The program continues monitoring incoming signals, allowing another intentional blink to trigger the next command.

### What Users Gain From It

On a broader scale, we wanted MindMotor to demonstrate how biological signals could be used to interact with technology without having to physically control it.

For individuals with certain physical disabilities, traditional controllers may not always be accessible. Although our project isn't a fully developed assistive device, it explores an approach to hands-free control that could potentially be expanded and adapted for different needs.

Our hope is that technologies like these can eventually become more accessible and affordable, rather than being limited to expensive or highly specialized systems.

## Our Experience

### Inspiration

Our project was inspired by Hiro Hamada's nanobots from *Big Hero 6*.

In the movie, Hiro uses a neural transmitter to control an entire swarm of nanobots with his thoughts, which I thought was an incredibly interesting concept.

Obviously, we weren't going to recreate a whole swarm of nanobots, but I wanted to explore whether we could replicate a much smaller part of that idea using technology we could actually access.

That eventually led us to the idea of using an EEG headset to control a robotic car.

Beyond the movie, what made the project even more interesting was its potential connection to assistive technology. We wanted to demonstrate, even on a small scale, how electrical signals from the human body could be translated into physical movement.

### Challenges We Faced

One of our biggest challenges was the EEG headset itself.

Although our Python program could recognize intentional blinks, the headset didn't always produce consistent signals. Sometimes it would lose electrode contact, other times it would temporarily stop transmitting data, and getting the car to respond consistently became frustrating.

We also experienced issues with Bluetooth communication, hardware wiring, power connections, and making sure the Arduino and motors were responding correctly.

There were moments when the code looked completely fine, yet the car wouldn't move. Other times, something that worked perfectly a few minutes earlier would suddenly stop working.

We experimented with different blink-detection thresholds and even explored recognizing additional facial expressions using frequency and oscillation analysis. However, we eventually decided to focus on getting the forward and stop controls to work reliably.

One of the biggest things this project taught us was that something can make complete sense theoretically, but actually getting it to work in the real world is a completely different experience.

### Team Collaboration

We divided responsibilities based on the different parts of the project.

I handled the initial planning, EEG headset integration, blink detection, and Bluetooth communication, while Christian focused on the physical assembly, wiring, and hardware connections.

We both contributed to the programming, testing, and troubleshooting.

This was especially important because neither the software nor the hardware could function as a complete system on its own. We had to make sure everything was communicating correctly, from the headset and laptop to the Arduino and motors.

### Did We Have Fun?

Absolutely!

Despite how frustrating this project was at times, it was also extremely fun and fulfilling.

There was a lot of trial and error, unexpected issues, and moments where we couldn't understand why something wasn't working the way it was supposed to.

But seeing the car finally respond to an intentional blink after all that planning, programming, and troubleshooting made everything feel worthwhile.

More than anything, it was exciting to take an idea inspired by science fiction and turn it into something we could actually build and control.

## Final Presentation

[CODE PRESENTATION.pdf](https://github.com/user-attachments/files/34867612/CODE.PRESENTATION.pdf)

## Future Improvements

Although we successfully demonstrated blink-based forward and stop controls, there are several things we'd like to explore if we continue developing MindMotor:

- Improving the reliability of the EEG headset and signal detection.
- Making intentional blink recognition more consistent.
- Adding additional directional controls.
- Exploring other ways of recognizing biological signals.
- Investigating how similar systems could be adapted for more accessible assistive technology.

---

*MindMotor is an experimental proof of concept exploring the connection between neuroscience, robotics, and accessible hands-free technology.*
