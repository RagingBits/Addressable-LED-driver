Simple Python example to demonstrate effects running from a PC.

Usage
Open a command line at the python folder location.
Run the python example indicating the respective serial COM port and effects file to be run.
The python will initialize the board every time it is invoked, so the LED Driver must always be reset.

Command Prompt example to run 50LED_RAINBOW_ROTATE.leds in the subfolder Effects, using COM PORT 3: 
:>python AddressableLEDsController.py -p COM3 -f Effects/50LED_RAINBOW_ROTATE.leds


