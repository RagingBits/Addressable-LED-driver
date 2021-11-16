Simple Python example to demonstrate effects running from a PC.

This app uses Python 3 scripts to run.


1) Install python 3 for windows.
2) Add python 3 exe forlder to windows eviromental variables PATH if needed.
3) Install "pyserial" module using "pip"
	3a) Run a cmd prompt and navigate to <python instalation forder>\Scripts and execute "pip.exe install pyserial" 
	3b) OR "python -m pip install pyserial".
4) Create a LEDs effects file using LED Matrix Studio V0.8.13 (Other versions may need a modified python script to absorb the generated files.)
This must have LEDs  effect file must be created with the exact length of leds used in the Magic Lights string, supporting a maximum of 300 LEDs.

Usage
Open a command line at the python folder location.
Run the python example indicating the respective serial COM port and effects file to be run.
The python will initialize the board every time it is invoked, so the LED Driver must always be reset.

Command Prompt example to run 50LED_RAINBOW_ROTATE.leds in the subfolder Effects, using COM PORT 3: 
:>python AddressableLEDsController.py -p COM3 -f Effects/50LED_RAINBOW_ROTATE.leds


