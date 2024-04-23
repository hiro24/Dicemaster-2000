# Dicemaster-2000
This is the CircuitPython code for the Dicemaster 2000. It is a dice roller meant to be run on a Raspberry Pi Pico. It is connected to a MicroSD module as well as a PAM8302 audio amplifier. It also uses connections for 6 buttons (various dice), a ROLL button and a RESET button.

![IMG_4589](https://github.com/hiro24/Dicemaster-2000/assets/1022614/177d7dec-091e-47a9-9d93-547bf2dbbeae)

Feel free to modify as needed, but the original wiring was as follows:

The project was powered by 1n 18650 battery shield.
Buttons:
D4 (4 sided dice) - GP16
D6 - GP18
D8 - GP21
D10 - GP26
D12 - GP27
D20 - GP28
ROLL - GP0
RESET - GP6

SD card reader module: 
SCK - GP10
MOSI - GP11
MISO - GP12
CS - GP13

PAM8302 audio amp:
PWM audio out - GP9

![IMG_4570](https://github.com/hiro24/Dicemaster-2000/assets/1022614/6c346b0f-c500-403b-933d-0b9566066da2)


