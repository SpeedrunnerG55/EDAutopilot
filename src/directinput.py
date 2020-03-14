# direct inputs
# source to this solution and code:
# http://stackoverflow.com/questions/14489013/simulate-python-keypresses-for-controlling-a-game
# http://www.gamespp.com/directx/directInputKeyboardScanCodes.html

# import ctypes
import subprocess

# Actuals Functions

def PressKey(Key):
    subprocess.call(["xdotool", "keydown", str(Key)])

def ReleaseKey(Key):
    subprocess.call(["xdotool", "keyup", str(Key)])
