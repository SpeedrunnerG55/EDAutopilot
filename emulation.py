# ## Control ED with direct input

# ### Get latest keybinds file

from sys import platform
from os import environ, listdir
from os.path import join, isfile, getmtime
from xml.etree.ElementTree import parse
from pynput.keyboard import Key, Controller as KeyController
from pynput.mouse import Button, Controller as ButtonController
from time import sleep,time

from consoleOut import consoleHeadder

if platform == "linux" or platform == "linux2":
    path_logs = "/home/" + environ['USER'] + "/.steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous"
    path_bindings = "/home/" + environ['USER'] + "/.steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Local Settings/Application Data/Frontier Developments/Elite Dangerous/Options/Bindings"
elif platform == "darwin":
    path_logs = "mac path i dunno"
    path_bindings = "mac path i dunno"
elif platform == "win32":
    path_logs = environ['USERPROFILE'] + "\Saved Games\Frontier Developments\Elite Dangerous"
    path_bindings = environ['LOCALAPPDATA'] + "\Frontier Developments\Elite Dangerous\Options\Bindings"

def get_latest_keybinds(path_bindings):
    list_of_bindings = [join(path_bindings, f) for f in listdir(path_bindings) if isfile(join(path_bindings, f))]
    if not list_of_bindings:
        return None
    latest_bindings = max(list_of_bindings, key=getmtime)
    return latest_bindings

PATH_KEYBINDINGS = path_bindings
KEY_REPEAT_DELAY = 0.200
KEY_DEFAULT_DELAY = 0.070


# ### Extract necessary keys

keys_to_obtain = [
        'YawLeftButton',
        'YawRightButton',
        'RollLeftButton',
        'RollRightButton',
        'PitchUpButton',
        'PitchDownButton',
        'SetSpeedZero',
        'SetSpeed50',
        'SetSpeed100',
        'HyperSuperCombination',
        'UIFocus',
        'UI_Up',
        'UI_Down',
        'UI_Left',
        'UI_Right',
        'UI_Select',
        'UI_Back',
        'CycleNextPanel',
        'HeadLookReset',
        'PrimaryFire',
        'SecondaryFire',
        'ExplorationFSSEnter',
        'ExplorationFSSQuit',
        'ExplorationFSSDiscoveryScan',
        'ExplorationFSSRadioTuningX_Decrease',
        'ExplorationFSSRadioTuningX_Increase'
    ]

def get_bindings(keys_to_obtain=keys_to_obtain):
    """Returns a dict struct with the direct input equivalent of the necessary elite keybindings"""
    direct_input_keys = {}

    latest_bindings = get_latest_keybinds(PATH_KEYBINDINGS)

    print("get_latest_keybinds="+str(latest_bindings))

    bindings_tree = parse(latest_bindings)
    bindings_root = bindings_tree.getroot()

    for item in bindings_root:
        if item.tag in keys_to_obtain:
            key = None
            mod = None
            # Check primary
            if item[0].attrib['Device'].strip() == "Keyboard":
                key = item[0].attrib['Key']
            # Check secondary (and prefer secondary)
            if item[1].attrib['Device'].strip() == "Keyboard":
                key = item[1].attrib['Key']

            if key is not None:
                key = key[4:]
            # Prepare final binding
            if key is not None:
                direct_input_keys[item.tag] = key

    if len(list(direct_input_keys.keys())) < 1:
        return None
    else:
        return direct_input_keys



keys = get_bindings()
for key in keys_to_obtain:
    try:
        print('get_bindings_<'+str(key)+'>='+str(keys[key]))
    except Exception as e:
        print(str("get_bindings_<"+key+">= does not have a valid keyboard keybind.").upper())

# ## Direct input function

# ### Send input

convert_to_direct_keys = {
    'LeftShift':Key.shift_l,
    'RightShift':Key.shift_r,
    'LeftAlt':Key.alt_l,
    'RightAlt':Key.alt_r,
    'LeftControl':Key.ctrl_l,
    'RightControl':Key.ctrl_r,
    'Enter':Key.enter,
    'Backspace':Key.backspace,
    'UpArrow':Key.up,
    'DownArrow':Key.down,
    'LeftArrow':Key.left,
    'RightArrow':Key.right,
    'End':Key.end,
    'Equals':'=',
    'Comma':',',
    'RightBracket':']',
    'Period':'.',
    'Apostrophe':'\'',
    'SemiColon':';',
    'Slash':'/',
    'Space':' ',
    'F1':'f1',
    'F2':'f2',
    'F3':'f3',
    'F4':'f4',
    'F5':'f5',
    'F6':'f6',
    'F7':'f7',
    'F8':'f8',
    'F9':'f9'
}


keyboard = KeyController()

# Actuals Functions

def PressKey(Key):
    if Key in convert_to_direct_keys:
        keyboard.press(convert_to_direct_keys[Key])
    else:
        keyboard.press(str(Key))

def ReleaseKey(Key):
    if Key in convert_to_direct_keys:
        keyboard.release(convert_to_direct_keys[Key])
    else:
        keyboard.release(str(Key))

def send(key, hold=None, repeat=1, repeat_delay=None, state=None):

    global KEY_DEFAULT_DELAY, KEY_REPEAT_DELAY

    if key is None:
        print('SEND=NONE !!!!!!!!')
        return

    for value in keys:
        if keys[value] == key:
            out = value
            break

    print('send=key:'+str(out)+',hold:'+str(hold)+',repeat:'+str(repeat)+',repeat_delay:'+str(repeat_delay)+',state:'+str(state))
    for i in range(repeat):

        if state == 1 or state == None:
            PressKey(key)
        if state is None:
            if hold:
                sleep(hold)
            else:
                sleep(KEY_DEFAULT_DELAY)
        if state is None or state == 0:
            ReleaseKey(key)
        if repeat_delay:
            sleep(repeat_delay)
        else:
            sleep(KEY_REPEAT_DELAY)


# ### Clear input

def clear_input(to_clear=None):
    consoleHeadder("CLEAR INPUT")
    for key in to_clear.keys():
        if key in keys:
            send(keys[key], state=0)
    print('clear_input')

mouse = ButtonController()

def SelectGame():
    # Read pointer position
    print('The current pointer position is {0}'.format(mouse.position))

    # Set pointer position
    mouse.position = (200, 200)
    print('Now we have moved it to {0}'.format(mouse.position))

    # Press and release
    mouse.press(Button.left)
    sleep(.3)
    mouse.release(Button.left)
    sleep(.3)
