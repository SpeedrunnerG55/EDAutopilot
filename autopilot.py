import cv2
from dev_autopilot import autopilot
from emulation import get_bindings, clear_input
import threading
import kthread
from pynput import keyboard
from programInfo import showInfo

STATE = 0

def start_action():
    stop_action()
    kthread.KThread(target = autopilot, name = "EDAutopilot").start()

def stop_action():
    cv2.destroyAllWindows()
    for thread in threading.enumerate():
        if thread.getName() == 'EDAutopilot':
            thread.kill()
    clear_input(get_bindings())

def on_press(key):
    try:
        if key == keyboard.Key.home:
            print('start action')
            start_action()
        if key == keyboard.Key.end:
            print('stop action')
            stop_action()
    except AttributeError:
        print('special key {0} pressed'.format(key))

def on_release(key):
    if key == keyboard.Key.esc:
        # Stop listener
        cv2.destroyAllWindows()
        stop_action()
        return False

showInfo();

# Collect events until released
with keyboard.Listener(on_press=on_press,on_release=on_release) as listener:
    listener.join()
