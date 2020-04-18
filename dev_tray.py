from dev_autopilot import autopilot,  get_bindings, clear_input
import threading
import kthread

STATE = 0

def start_action():
    stop_action()
    kthread.KThread(target = autopilot, name = "EDAutopilot").start()

def stop_action():
    for thread in threading.enumerate():
        if thread.getName() == 'EDAutopilot':
            thread.kill()
    clear_input(get_bindings())

from pynput import keyboard

def on_press(key):
    try:
        if key == keyboard.Key.home:
            print('start action')
            start_action()
        if key == keyboard.Key.end:
            print('stop action')
            stop_action()
    except AttributeError:
        print('special key {0} pressed'.format(
            key))

def on_release(key):
    print('{0} released'.format(key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# Collect events until released
with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()

# ...or, in a non-blocking fashion:
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()

if __name__ == '__main__':
    tray()
