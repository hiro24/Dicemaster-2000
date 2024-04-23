import os
import busio
import pwmio
import time
import random
import board
import digitalio
import storage
import adafruit_sdcard
from audiomp3 import MP3Decoder
from audiocore import WaveFile
import audiopwmio

# Uses CircuitPython

# audio = AudioOut(board.GP9)
audio = audiopwmio.PWMAudioOut(board.GP9)
path = "/sd/dice/"
filename = "nice.wav"

# Keep track of time for percentage toggling
d4_press_time = 0
d6_press_time = 0
d8_press_time = 0
d10_press_time = 0
mode_1_to_100 = False
silent_mode = False

# Define buttons
button_pins = {
    'd4': board.GP16,
    'd6': board.GP18,
    'd8': board.GP21,
    'd10': board.GP26,
    'd12': board.GP27,
    'd20': board.GP28,
    'roll': board.GP0,
    'reset': board.GP6
}
buttons = {}
for button, pin in button_pins.items():
    buttons[button] = digitalio.DigitalInOut(pin)
    buttons[button].switch_to_input(pull=digitalio.Pull.DOWN)

# Setting up sd card reader, use SPI1: SCK=GP10, MOSI=GP11, MISO=GP12
spi = busio.SPI(board.GP10, board.GP11, board.GP12)  # SCK, MOSI, MISO
cs = digitalio.DigitalInOut(board.GP13)  # CS pin

# Connect to the card and mount the filesystem.
sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# Set up MP3 files for playing
mp3_file = open(path + filename, "rb")
decoder = MP3Decoder(mp3_file)

# Process for playing MP3 files
def play_mp3(filename):
    path = "/sd/dice/"
    decoder.file = open(path + filename, "rb")
    audio.play(decoder)
    while audio.playing:
        pass

def process_roll_result(roll_result):
    # Initialize the variables
    numberOne, numberTwo = None, None
    # Handle cases for 1 - 15
    if 1 <= roll_result <= 100:
        numberOne = f"{roll_result}.mp3"
    # Handle cases for 100 - 199
    elif 100 <= roll_result <= 199:
        if roll_result == 100:
            numberOne = "100.mp3"
        else:
            # Process the number as if it were 0 - 99, then adjust the variables
            tempResult = roll_result - 100
            numberOne, numberTwo = process_roll_result(tempResult)
            numberOne, numberTwo = "100.mp3", numberOne
    # Handle case for 200
    elif roll_result == 200:
        numberOne = "200.mp3"
    return numberOne, numberTwo

# Set up variables for use later in dice rolling
# Initialize dice counts in a dictionary
dice_counts = {'d4': 0, 'd6': 0, 'd8': 0, 'd10': 0, 'd12': 0, 'd20': 0}

# Saved dice counts
# save_dice_counts = {'d4save': 0, 'd6save': 0, 'd8save': 0, 'd10save': 0, 'd12save': 0, 'd20save': 0}

# Initialize other variables
total_dice = 0
# saved_total_dice = 0
roll_result = 0
dice_rolled = False  # Using a boolean for better clarity
my_and = False  # Using a boolean for better clarity

def resetDice():
    global dice_counts, total_dice, dice_rolled, roll_result
    # Reset all dice counts to 0
    for key in dice_counts:
        dice_counts[key] = 0
    # Reset other variables
    total_dice = 0
    dice_rolled = False
    roll_result = 0

def save_to_file():
    global dice_counts, total_dice
    with open("/sd/saved.pool", "w") as file:
        for key, value in dice_counts.items():
            file.write(f"{key}={value}\n")
        file.write(f"total_dice={total_dice}\n")

def load_from_file():
    global dice_counts, total_dice, dice_rolled, roll_result
    with open("/sd/saved.pool", "r") as file:
        for line in file:
            key, value = line.strip().split('=')
            if key in dice_counts:
                dice_counts[key] = int(value)
            elif key == 'total_dice':
                total_dice = int(value)
    dice_rolled = False
    roll_result = 0

#def save_pool():
#    global dice_counts, save_dice_counts, total_dice, saved_total_dice
#    for save_key in save_dice_counts:
#        key = save_key.replace('save', '')  # Remove 'save' from the key
#        if key in dice_counts:
#            save_dice_counts[save_key] = dice_counts[key]
#    saved_total_dice = total_dice

#def load_pool():
#    global dice_counts, save_dice_counts, total_dice, saved_total_dice, dice_rolled, roll_result
#    for key in dice_counts:
#        save_key = key + 'save'
#        if save_key in save_dice_counts:
#            dice_counts[key] = save_dice_counts[save_key]
#    total_dice = saved_total_dice
#    dice_rolled = False
#    roll_result = 0

# Set up onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

print("Entering main loop")
while True:
    time.sleep(0.1)  # Short delay
    if buttons['d4'].value:  # If the d4 button is pressed
        if d4_press_time == 0:  # Button was just pressed
            d4_press_time = time.monotonic()  # Record press time
    else:
        if d4_press_time != 0:  # Button was released
            press_duration = time.monotonic() - d4_press_time
            if press_duration >= 2:  # Check if it was a long press
                silent_mode = not silent_mode  # Toggle mode
                d4_press_time = 0  # Reset press time
                if silent_mode:
                    print("Switching to silent mode")
                    play_mp3("quietmode.mp3")
                else:
                    print("Switching to normal mode")
                    play_mp3("normalmode.mp3")
            else:
                if mode_1_to_100:
                    if silent_mode:
                        play_mp3("error.mp3")
                    else:
                        play_mp3("disablepercentagemode.mp3")
                else:
                    if dice_rolled:
                        if silent_mode:
                            play_mp3("chime.mp3")
                        else:
                            play_mp3("resetting.mp3")
                        resetDice()
                    if total_dice < 10:
                        total_dice = total_dice + 1
                        dice_counts['d4'] += 1
                        # print("1 D4 added, " + str(total_dice) + " in the pool")
                        if silent_mode:
                            play_mp3("tone1.mp3")
                        else:
                            play_mp3("d4.mp3")
                        # play_music("stevie.mp3")
                    else:
                        # print("Dice pool is full")
                        if silent_mode:
                            play_mp3("error.mp3")
                        else:
                            play_mp3("full.mp3")
                    # led.value = True
                    # time.sleep(0.5)
                    # led.value = False
                    d4_press_time = 0  # Reset press time
    if buttons['d6'].value:  # If the d6 button is pressed
        if d6_press_time == 0:  # Button was just pressed
            d6_press_time = time.monotonic()  # Record press time
    else:
        if d6_press_time != 0:  # Button was released
            press_duration = time.monotonic() - d6_press_time
            if press_duration >= 2:  # Check if it was a long press
                save_to_file()
                d6_press_time = 0  # Reset press time
                time.sleep(0.5)
                if silent_mode:
                    print("Saving dice pool")
                    play_mp3("savechime.mp3")
                else:
                    print("Saving dice pool")
                    play_mp3("save.mp3")
            else:
                if mode_1_to_100:
                    if silent_mode:
                        play_mp3("error.mp3")
                    else:
                        play_mp3("disablepercentagemode.mp3")
                else:
                    if dice_rolled:
                        if silent_mode:
                            play_mp3("chime.mp3")
                        else:
                            play_mp3("resetting.mp3")
                        resetDice()
                    if total_dice < 10:
                        total_dice = total_dice + 1
                        dice_counts['d6'] += 1
                        # print("1 D6 added, " + str(total_dice) + " in the pool")
                        if silent_mode:
                            play_mp3("tone2.mp3")
                        else:
                            play_mp3("d6.mp3")
                    else:
                        # print("Dice pool is full")
                        if silent_mode:
                            play_mp3("error.mp3")
                        else:
                            play_mp3("full.mp3")
                    # led.value = True
                    # time.sleep(0.5)
                    # led.value = False
                    d6_press_time = 0  # Reset press time
    if buttons['d8'].value:  # If the d8 button is pressed
        if d8_press_time == 0:  # Button was just pressed
            d8_press_time = time.monotonic()  # Record press time
    else:
        if d8_press_time != 0:  # Button was released
            press_duration = time.monotonic() - d8_press_time
            if press_duration >= 2:  # Check if it was a long press
                load_from_file()
                time.sleep(0.5)
                d8_press_time = 0  # Reset press time
                if silent_mode:
                    print("Loading dice pool")
                    play_mp3("loadchime.mp3")
                else:
                    print("Loading dice pool")
                    play_mp3("load.mp3")
            else:
                if mode_1_to_100:
                    if silent_mode:
                        play_mp3("error.mp3")
                    else:
                        play_mp3("disablepercentagemode.mp3")
                else:
                    if dice_rolled:
                        if silent_mode:
                            play_mp3("chime.mp3")
                        else:
                            play_mp3("resetting.mp3")
                        resetDice()
                    if total_dice < 10:
                        total_dice = total_dice + 1
                        dice_counts['d8'] += 1
                        # print("1 D8 added, " + str(total_dice) + " in the pool")
                        if silent_mode:
                            play_mp3("tone3.mp3")
                        else:
                            play_mp3("d8.mp3")
                    else:
                        # print("Dice pool is full")
                        if silent_mode:
                            play_mp3("error.mp3")
                        else:
                            play_mp3("full.mp3")
                    # led.value = True
                    # time.sleep(0.5)
                    # led.value = False
                    d8_press_time = 0  # Reset press time
    if buttons['d10'].value:
        if d10_press_time == 0:  # Button was just pressed
            d10_press_time = time.monotonic()  # Record press time
    else:
        if d10_press_time != 0:  # Button was released
            press_duration = time.monotonic() - d10_press_time
            if press_duration >= 2:  # Check if it was a long press
                mode_1_to_100 = not mode_1_to_100  # Toggle mode
                d10_press_time = 0  # Reset press time
                if mode_1_to_100:
                    print("Mode switched to 1-100")
                    if silent_mode:
                        play_mp3("modechange.mp3")
                    else:
                        play_mp3("percentagemode.mp3")
                    resetDice()
                    total_dice = 1
                else:
                    print("Mode switched to normal dice pool")
                    if silent_mode:
                        play_mp3("chime.mp3")
                    else:
                        play_mp3("d10mode.mp3")
                    resetDice()
            else:
                # Original D10 functionality
                if mode_1_to_100:
                    if silent_mode:
                        play_mp3("error.mp3")
                    else:
                        play_mp3("disablepercentagemode.mp3")
                else:
                    if dice_rolled:
                        if silent_mode:
                            play_mp3("chime.mp3")
                        else:
                            play_mp3("resetting.mp3")
                        resetDice()
                    if total_dice < 10:
                        total_dice += 1
                        dice_counts['d10'] += 1
                        if silent_mode:
                            play_mp3("tone4.mp3")
                        else:
                            play_mp3("d10.mp3")
                    else:
                        if silent_mode:
                            play_mp3("error.mp3")
                        else:
                            play_mp3("full.mp3")
                    # led.value = True
                    # time.sleep(0.5)
                    # led.value = False
                    d10_press_time = 0  # Reset press time
    if buttons['d12'].value:  # If the d12 button is pressed
        if mode_1_to_100:
            if silent_mode:
                play_mp3("error.mp3")
            else:
                play_mp3("disablepercentagemode.mp3")
        else:
            if dice_rolled:
                if silent_mode:
                    play_mp3("chime.mp3")
                else:
                    play_mp3("resetting.mp3")
                resetDice()
            if total_dice < 10:
                total_dice = total_dice + 1
                dice_counts['d12'] += 1
                # print("1 D12 added, " + str(total_dice) + " in the pool")
                if silent_mode:
                    play_mp3("tone5.mp3")
                else:
                    play_mp3("d12.mp3")
            else:
                # print("Dice pool is full")
                if silent_mode:
                    play_mp3("error.mp3")
                else:
                    play_mp3("full.mp3")
            # led.value = True
            # time.sleep(0.5)
            # led.value = False
    if buttons['d20'].value:  # If the d20 button is pressed
        if mode_1_to_100:
            if silent_mode:
                play_mp3("error.mp3")
            else:
                play_mp3("disablepercentagemode.mp3")
        else:
            if dice_rolled:
                if silent_mode:
                    play_mp3("chime.mp3")
                else:
                    play_mp3("resetting.mp3")
                resetDice()
            if total_dice < 10:
                total_dice = total_dice + 1
                dice_counts['d20'] += 1
                # print("1 D20 added, " + str(total_dice) + " in the pool")
                if silent_mode:
                    play_mp3("tone6.mp3")
                else:
                    play_mp3("d20.mp3")
            else:
                # print("Dice pool is full")
                if silent_mode:
                    play_mp3("error.mp3")
                else:
                    play_mp3("full.mp3")
            # led.value = True
            # time.sleep(0.5)
            # led.value = False
    if buttons['roll'].value:  # If the roll button is pressed
        if dice_rolled:
            if not silent_mode:
                play_mp3("thelastrollwas.mp3")
            numberOne, numberTwo = process_roll_result(roll_result)
            if numberOne is not None:
                play_mp3(numberOne)
            if numberTwo is not None:
                play_mp3(numberTwo)
            if roll_result == 69:
                play_mp3("nice.mp3")
        else:
            if total_dice == 0:
                # print("No dice in pool.")
                if silent_mode:
                    play_mp3("error.mp3")
                else:
                    play_mp3("nodice.mp3")
            else:
                print("Rolling dice...")
                my_and = 0
                if mode_1_to_100:
                    if not silent_mode:
                        play_mp3("rollingpercentage.mp3")
                else:
                    if not silent_mode:
                        play_mp3("rolling.mp3")
                if dice_counts['d4'] > 0:
                    if not silent_mode:
                        play_mp3(str(dice_counts['d4']) + ".mp3")
                        play_mp3("d4.mp3")
                    my_and = 1
                if dice_counts['d6'] > 0:
                    if my_and == 1:
                        if not silent_mode:
                            play_mp3("and.mp3")
                    if not silent_mode:
                        play_mp3(str(dice_counts['d6']) + ".mp3")
                        play_mp3("d6.mp3")
                    my_and = 1
                if dice_counts['d8'] > 0:
                    if my_and == 1:
                        if not silent_mode:
                            play_mp3("and.mp3")
                    if not silent_mode:
                        play_mp3(str(dice_counts['d8']) + ".mp3")
                        play_mp3("d8.mp3")
                    my_and = 1
                if dice_counts['d10'] > 0:
                    if my_and == 1:
                        if not silent_mode:
                            play_mp3("and.mp3")
                    if not silent_mode:
                        play_mp3(str(dice_counts['d10']) + ".mp3")
                        play_mp3("d10.mp3")
                    my_and = 1
                if dice_counts['d12'] > 0:
                    if my_and == 1:
                        if not silent_mode:
                            play_mp3("and.mp3")
                    if not silent_mode:
                        play_mp3(str(dice_counts['d12']) + ".mp3")
                        play_mp3("d12.mp3")
                    my_and = 1
                if dice_counts['d20'] > 0:
                    if my_and == 1:
                        if not silent_mode:
                            play_mp3("and.mp3")
                    if not silent_mode:
                        play_mp3(str(dice_counts['d20']) + ".mp3")
                        play_mp3("d20.mp3")
                play_mp3("diceSound.mp3")
                if mode_1_to_100:
                    # Generate a random number between 1 and 100
                    roll_result = random.randint(1, 100)
                    print("Random number (1-100):", roll_result)
                    numberOne, numberTwo = process_roll_result(roll_result)
                    if numberOne is not None:
                        play_mp3(numberOne)
                else:
                    for i in range(dice_counts['d4']):
                        roll_result = roll_result + random.randint(1, 4)
                    for i in range(dice_counts['d6']):
                        roll_result = roll_result + random.randint(1, 6)
                    for i in range(dice_counts['d8']):
                        roll_result = roll_result + random.randint(1, 8)
                    for i in range(dice_counts['d10']):
                        roll_result = roll_result + random.randint(1, 10)
                    for i in range(dice_counts['d12']):
                        roll_result = roll_result + random.randint(1, 12)
                    for i in range(dice_counts['d20']):
                        roll_result = roll_result + random.randint(1, 20)
                    print("You rolled", end="")
                    if dice_counts['d4'] > 0:
                        print(" " + str(dice_counts['d4']) + " D4", end="")
                    if dice_counts['d6'] > 0:
                        print(" " + str(dice_counts['d6']) + " D6", end="")
                    if dice_counts['d8'] > 0:
                        print(" " + str(dice_counts['d8']) + " D8", end="")
                    if dice_counts['d10'] > 0:
                        print(" " + str(dice_counts['d10']) + " D10", end="")
                    if dice_counts['d12'] > 0:
                        print(" " + str(dice_counts['d12']) + " D12", end="")
                    if dice_counts['d20'] > 0:
                        print(" " + str(dice_counts['d20']) + " D20", end="")
                    print(" ")
                    print("The result is: " + str(roll_result))
                    numberOne, numberTwo = process_roll_result(roll_result)
                    dice_rolled = True
                    if numberOne is not None:
                        play_mp3(numberOne)
                    if numberTwo is not None:
                        play_mp3(numberTwo)
                    if roll_result == 69:
                        play_mp3("nice.mp3")
                led.value = True
                time.sleep(0.5)
                led.value = False
    if buttons['reset'].value:  # If the reset button is pressed
        print("Dice have been reset")
        if silent_mode:
            play_mp3("chime.mp3")
        else:
            play_mp3("resetting.mp3")
        resetDice()
        led.value = True
        time.sleep(0.5)
        led.value = False
