
import sys
from sys import platform
from os import environ, listdir
from os.path import join, isfile, getmtime, abspath
from json import loads
from math import degrees, atan
from random import random
from time import sleep
from numpy import array, sum, where
import pyscreenshot as ImageGrab
from datetime import datetime
from xml.etree.ElementTree import parse
import cv2 # see reference 2
from pyautogui import size# see reference 6
import logging
import colorlog
import subprocess


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = abspath(".")

    return join(base_path, relative_path)


# ## Logging

logging.basicConfig(filename='autopilot.log', level=logging.DEBUG)
logger = colorlog.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(
    colorlog.ColoredFormatter('%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s',
        log_colors={
            'DEBUG':    'fg_bold_cyan',
            'INFO':     'fg_bold_green',
            'WARNING':  'bg_bold_yellow,fg_bold_blue',
            'ERROR':    'bg_bold_red,fg_bold_white',
            'CRITICAL': 'bg_bold_red,fg_bold_yellow',
	},secondary_log_colors={}

    ))
logger.addHandler(handler)

logger.debug('This is a DEBUG message. These information is usually used for troubleshooting')
logger.info('This is an INFO message. These information is usually used for conveying information')
logger.warning('some warning message. These information is usually used for warning')
logger.error('some error message. These information is usually used for errors and should not happen')
logger.critical('some critical message. These information is usually used for critical error, and will usually result in an exception.')


logging.info('\n'+200*'-'+'\n'+'---- AUTOPILOT DATA '+180*'-'+'\n'+200*'-')


# ## Constants

if platform == "linux" or platform == "linux2":
    path_logs = "/home/speed/.steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous"
    path_bindings = "/home/speed/.steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Local Settings/Application Data/Frontier Developments/Elite Dangerous/Options/Bindings"
elif platform == "darwin":
    path_logs = "mac path i dunno"
    path_bindings = "mac path i dunno"
elif platform == "win32":
    path_logs = environ['USERPROFILE'] + "\Saved Games\Frontier Developments\Elite Dangerous"
    path_bindings = environ['LOCALAPPDATA'] + "\Frontier Developments\Elite Dangerous\Options\Bindings"

RELEASE = 'v19.05.15-alpha-18'
PATH_LOG_FILES = path_logs
PATH_KEYBINDINGS = path_bindings
KEY_MOD_DELAY = 0.010
KEY_DEFAULT_DELAY = 0.200
KEY_REPEAT_DELAY = 0.100
FUNCTION_DEFAULT_DELAY = 0.500
SCREEN_WIDTH, SCREEN_HEIGHT = size()

logging.info('RELEASE='+str(RELEASE))
logging.info('PATH_LOG_FILES='+str(PATH_LOG_FILES))
logging.info('PATH_KEYBINDINGS='+str(PATH_KEYBINDINGS))
logging.info('KEY_MOD_DELAY='+str(KEY_MOD_DELAY))
logging.info('KEY_DEFAULT_DELAY='+str(KEY_DEFAULT_DELAY))
logging.info('KEY_REPEAT_DELAY='+str(KEY_REPEAT_DELAY))
logging.info('FUNCTION_DEFAULT_DELAY='+str(FUNCTION_DEFAULT_DELAY))
logging.info('SCREEN_WIDTH='+str(SCREEN_WIDTH))
logging.info('SCREEN_HEIGHT='+str(SCREEN_HEIGHT))


# ## Read ED logs

# ### Get latest log file


def get_latest_log(path_logs):
    """Returns the full path of the latest (most recent) elite log file (journal) from specified path"""
    list_of_logs = [join(path_logs, f) for f in listdir(path_logs) if isfile(join(path_logs, f)) and f.startswith('Journal.')]
    if not list_of_logs:
        return None
    latest_log = max(list_of_logs, key=getmtime)
    return latest_log



logging.info('get_latest_log='+str(get_latest_log(PATH_LOG_FILES)))


# ### Extract ship info from log


def ship():
    """Returns a 'status' dict containing relevant game status information (state, fuel, ...)"""
    latest_log = get_latest_log(PATH_LOG_FILES)
    ship = {
        'time': (datetime.now() - datetime.fromtimestamp(getmtime(latest_log))).seconds,
        'status': None,
        'type': None,
        'location': None,
        'star_class': None,
        'target': None,
        'fuel_capacity': None,
        'fuel_level': None,
        'fuel_percent': None,
        'is_scooping': False,
    }
    # Read log line by line and parse data
    with open(latest_log, encoding="utf-8") as f:
        for line in f:
            log = loads(line)

            # parse data
            try:
                # parse ship status
                log_event = log['event']

                if log_event == 'StartJump':
                    ship['status'] = str('starting_'+log['JumpType']).lower()

                elif log_event == 'SupercruiseEntry' or log_event == 'FSDJump':
                    ship['status'] = 'in_supercruise'

                elif log_event == 'SupercruiseExit' or log_event == 'DockingCancelled'                  or (log_event == 'Music' and ship['status'] == 'in_undocking')                  or (log_event == 'Location' and log['Docked'] == False):
                    ship['status'] = 'in_space'

                elif log_event == 'Undocked':
#                     ship['status'] = 'starting_undocking'
                    ship['status'] = 'in_space'

                elif log_event == 'DockingRequested':
                    ship['status'] = 'starting_docking'

                elif log_event == "Music" and log['MusicTrack'] == "DockingComputer":
                    if ship['status'] == 'starting_undocking':
                        ship['status'] = 'in_undocking'
                    elif ship['status'] == 'starting_docking':
                        ship['status'] = 'in_docking'

                elif log_event == 'Docked':
                    ship['status'] = 'in_station'

                # parse ship type
                if log_event == 'LoadGame' or log_event == 'Loadout':
                    ship['type'] = log['Ship']

                # parse fuel
                if 'FuelLevel' in log and ship['type'] != 'TestBuggy':
                    ship['fuel_level'] = log['FuelLevel']
                if 'FuelCapacity' in log and ship['type'] != 'TestBuggy':
                        try:
                            ship['fuel_capacity'] = log['FuelCapacity']['Main']
                        except:
                            ship['fuel_capacity'] = log['FuelCapacity']
                if log_event == 'FuelScoop' and 'Total' in log:
                    ship['fuel_level'] = log['Total']
                if ship['fuel_level'] and ship['fuel_capacity']:
                    ship['fuel_percent'] = round((ship['fuel_level'] / ship['fuel_capacity'])*100)
                else:
                    ship['fuel_percent'] = 10

                # parse scoop
                if log_event == 'FuelScoop' and ship['time'] < 10 and ship['fuel_percent'] < 100:
                    ship['is_scooping'] = True
                else:
                    ship['is_scooping'] = False

                # parse location
                if (log_event == 'Location' or log_event == 'FSDJump') and 'StarSystem' in log:
                    ship['location'] = log['StarSystem']
                if 'StarClass' in log:
                    ship['star_class'] = log['StarClass']

                # parse target
                if log_event == 'FSDTarget':
                    if log['Name'] == ship['location']:
                        ship['target'] = None
                    else:
                        ship['target'] = log['Name']
                elif log_event == 'FSDJump':
                    if ship['location'] == ship['target']:
                        ship['target'] = None


            # exceptions
            except Exception as e:
                logging.exception("Exception occurred")
                print(e)
#     logging.debug('ship='+str(ship))
    return ship



logging.debug('ship='+str(ship()))


# ## Control ED with direct input

# ### Get latest keybinds file


def get_latest_keybinds(path_bindings):
    list_of_bindings = [join(path_bindings, f) for f in listdir(path_bindings) if isfile(join(path_bindings, f))]
    if not list_of_bindings:
        return None
    latest_bindings = max(list_of_bindings, key=getmtime)
    return latest_bindings


logging.info("get_latest_keybinds="+str(get_latest_keybinds(PATH_KEYBINDINGS)))


# ### Extract necessary keys



keys_to_obtain = [
        'YawLeftButton',
        'YawRightButton',
        'RollLeftButton',
        'RollRightButton',
        'PitchUpButton',
        'PitchDownButton',
        'SetSpeedZero',
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
        'SecondaryFire'
    ]

def get_bindings(keys_to_obtain=keys_to_obtain):
    """Returns a dict struct with the direct input equivalent of the necessary elite keybindings"""
    direct_input_keys = {}
    convert_to_direct_keys = {
        'Key_LeftShift':'LShift',
        'Key_RightShift':'RShift',
        'Key_LeftAlt':'LAlt',
        'Key_RightAlt':'RAlt',
        'Key_LeftControl':'LControl',
        'Key_RightControl':'RControl',
        'Key_Enter':'Return',
        'Key_Backspace':'0xff08',
        'Key_UpArrow':'0x08fc',
        'Key_DownArrow':'0x08fe',
        'Key_LeftArrow':'0x08fb',
        'Key_RightArrow':'0x08fd'
    }

    latest_bindings = get_latest_keybinds(PATH_KEYBINDINGS)
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
            # Adequate key to SCANCODE dict standard
            if key in convert_to_direct_keys:
                key = convert_to_direct_keys[key]
            elif key is not None:
                key = key[4:]
            # Prepare final binding
            if key is not None:
                direct_input_keys[item.tag] = key
#             else:
#                 logging.warning("get_bindings_<"+item.tag+">= does not have a valid keyboard keybind.")

    if len(list(direct_input_keys.keys())) < 1:
        return None
    else:
        return direct_input_keys



keys = get_bindings()
for key in keys_to_obtain:
    try:
        logging.info('get_bindings_<'+str(key)+'>='+str(keys[key]))
    except Exception as e:
        logging.warning(str("get_bindings_<"+key+">= does not have a valid keyboard keybind.").upper())

# ## Direct input function

# ### Send input


# Actuals Functions

def PressKey(Key):
    print("keydown key: " + str(Key))
    subprocess.call(["xdotool", "keydown", str(Key)])

def ReleaseKey(Key):
    print("keyup key: " + str(Key))
    subprocess.call(["xdotool", "keyup", str(Key)])

def send(key, hold=None, repeat=1, repeat_delay=None, state=None):

    global KEY_MOD_DELAY, KEY_DEFAULT_DELAY, KEY_REPEAT_DELAY

    if key is None:
        logging.warning('SEND=NONE !!!!!!!!')
        return

    logging.debug('send=key:'+str(key)+',hold:'+str(hold)+',repeat:'+str(repeat)+',repeat_delay:'+str(repeat_delay)+',state:'+str(state))
    for i in range(repeat):

        if state is None or state == 1:
            if 'mod' in key:
                PressKey(key)
                sleep(KEY_MOD_DELAY)

            PressKey(key)

        if state is None:
            if hold:
                sleep(hold)
            else:
                sleep(KEY_DEFAULT_DELAY)

        if state is None or state == 0:
            ReleaseKey(key)

            if 'mod' in key:
                sleep(KEY_MOD_DELAY)
                ReleaseKey(key)

        if repeat_delay:
            sleep(repeat_delay)
        else:
            sleep(KEY_REPEAT_DELAY)



# ### Clear input

def clear_input(to_clear=None):
    logging.info('\n'+200*'-'+'\n'+'---- CLEAR INPUT '+183*'-'+'\n'+200*'-')
    for key in to_clear.keys():
        if key in keys:
            send(to_clear[key], state=0)
    logging.debug('clear_input')


# ### Get screen

def get_screen(x_left, y_top, x_right, y_bot):
    x_left = int(x_left)
    y_top = int(y_top)
    x_right = int(x_right)
    y_bot = int(y_bot)
    # print("grabbing screen" + str((x_left, y_top, x_right, y_bot)))
    screen = array(ImageGrab.grab(bbox=(x_left, y_top, x_right, y_bot)))
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    test = cv2.imread(resource_path("Cold Osha.PNG"))
    test = cv2.resize(test,(500,500))
    print(test)
    cv2.imshow('Screen',test)

    return screen


# ### HSV slider tool

def callback(x):
    pass

def hsv_slider(bandw=False):
    cv2.namedWindow('image')

    ilowH = 0
    ihighH = 179

    ilowS = 0
    ihighS = 255
    ilowV = 0
    ihighV = 255

    # create trackbars for color change
    cv2.createTrackbar('lowH','image',ilowH,179,callback)
    cv2.createTrackbar('highH','image',ihighH,179,callback)

    cv2.createTrackbar('lowS','image',ilowS,255,callback)
    cv2.createTrackbar('highS','image',ihighS,255,callback)

    cv2.createTrackbar('lowV','image',ilowV,255,callback)
    cv2.createTrackbar('highV','image',ihighV,255,callback)

    while(True):
        # grab the frame
        frame = get_screen((5/16)*SCREEN_WIDTH, (5/8)*SCREEN_HEIGHT,(2/4)*SCREEN_WIDTH, (15/16)*SCREEN_HEIGHT)
        if bandw:
            frame = equalize(frame)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # get trackbar positions
        ilowH = cv2.getTrackbarPos('lowH', 'image')
        ihighH = cv2.getTrackbarPos('highH', 'image')
        ilowS = cv2.getTrackbarPos('lowS', 'image')
        ihighS = cv2.getTrackbarPos('highS', 'image')
        ilowV = cv2.getTrackbarPos('lowV', 'image')
        ihighV = cv2.getTrackbarPos('highV', 'image')

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_hsv = array([ilowH, ilowS, ilowV])
        higher_hsv = array([ihighH, ihighS, ihighV])
        mask = cv2.inRange(hsv, lower_hsv, higher_hsv)

        frame = cv2.bitwise_and(frame, frame, mask=mask)

        # show thresholded image
        cv2.imshow('image', frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break


# ### Equalization

def equalize(image=None, testing=False):
    while True:
        if testing:
            img = get_screen((5/16)*SCREEN_WIDTH, (5/8)*SCREEN_HEIGHT,(2/4)*SCREEN_WIDTH, (15/16)*SCREEN_HEIGHT)
        else:
            img = image.copy()
        # Load the image in greyscale
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # create a CLAHE object (Arguments are optional).
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        img_out = clahe.apply(img_gray)
        if testing:
            cv2.imshow('Equalized', img_out)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    return img_out



# ### Filter bright

def filter_bright(image=None, testing=False):
    while True:
        if testing:
            img = get_screen((5/16)*SCREEN_WIDTH, (5/8)*SCREEN_HEIGHT,(2/4)*SCREEN_WIDTH, (15/16)*SCREEN_HEIGHT)
        else:
            img = image.copy()
        equalized = equalize(img)
        equalized = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
        equalized = cv2.cvtColor(equalized, cv2.COLOR_BGR2HSV)
        filtered = cv2.inRange(equalized, array([0, 0, 215]), array([0, 0, 255]))
        if testing:
            cv2.imshow('Filtered', filtered)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    return filtered



# ### Filter sun

def filter_sun(image=None, testing=False):
    while True:
        if testing:
            hsv = get_screen((1/3)*SCREEN_WIDTH, (1/3)*SCREEN_HEIGHT,(2/3)*SCREEN_WIDTH, (2/3)*SCREEN_HEIGHT)
        else:
            hsv = image.copy()
        # converting from BGR to HSV color space
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
        # filter Elite UI orange
        filtered = cv2.inRange(hsv, array([0, 100, 240]), array([180, 255, 255]))
        if testing:
            cv2.imshow('Filtered', filtered)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    return filtered



# ### Filter orange

def filter_orange(image=None, testing=False):
    while True:
        if testing:
            hsv = get_screen((1/3)*SCREEN_WIDTH, (1/3)*SCREEN_HEIGHT,(2/3)*SCREEN_WIDTH, (2/3)*SCREEN_HEIGHT)
        else:
            hsv = image.copy()
        # converting from BGR to HSV color space
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
        # filter Elite UI orange
        filtered = cv2.inRange(hsv, array([0, 130, 123]), array([25, 235, 220]))
        if testing:
            cv2.imshow('Filtered', filtered)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    return filtered




# ### Filter orange2

def filter_orange2(image=None, testing=False):
    while True:
        if testing:
            hsv = get_screen((1/3)*SCREEN_WIDTH, (1/3)*SCREEN_HEIGHT,(2/3)*SCREEN_WIDTH, (2/3)*SCREEN_HEIGHT)
        else:
            hsv = image.copy()
        # converting from BGR to HSV color space
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
        # filter Elite UI orange
        filtered = cv2.inRange(hsv, array([15, 220, 220]), array([30, 255, 255]))
        if testing:
            cv2.imshow('Filtered', filtered)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    return filtered




# ### Filter blue

def filter_blue(image=None, testing=False):
    while True:
        if testing:
            hsv = get_screen((1/3)*SCREEN_WIDTH, (1/3)*SCREEN_HEIGHT,(2/3)*SCREEN_WIDTH, (2/3)*SCREEN_HEIGHT)
        else:
            hsv = image.copy()
        # converting from BGR to HSV color space
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
        # filter Elite UI orange
        filtered = cv2.inRange(hsv, array([0, 0, 200]), array([180, 100, 255]))
        if testing:
            cv2.imshow('Filtered', filtered)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    return filtered




# ### Get sun

def sun_percent():
    screen = get_screen((1/3)*SCREEN_WIDTH, (1/3)*SCREEN_HEIGHT,(2/3)*SCREEN_WIDTH, (2/3)*SCREEN_HEIGHT)
    filtered = filter_sun(screen)
    total = (1/3)*SCREEN_WIDTH*(1/3)*SCREEN_HEIGHT
    white = sum(filtered == 255)
    black = sum(filtered != 255)
    result = white / black
    return result * 100




# ### Get compass image

def get_compass_image(testing=False):
    compass_template = cv2.imread(resource_path("templates/compass.png"), cv2.IMREAD_GRAYSCALE)
    compass_width, compass_height = compass_template.shape[::-1]
    compass_image = compass_template.copy()
    doubt = 10
    while True:
        screen = get_screen((5/16)*SCREEN_WIDTH, (5/8)*SCREEN_HEIGHT,(2/4)*SCREEN_WIDTH, (15/16)*SCREEN_HEIGHT)
#         mask_orange = filter_orange(screen)
        equalized = equalize(screen)
        match = cv2.matchTemplate(equalized, compass_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.3
        loc = where( match >= threshold)
        pt = (doubt, doubt)
        for point in zip(*loc[::-1]):
                pt = point
        compass_image = screen[pt[1]-doubt : pt[1]+compass_height+doubt, pt[0]-doubt : pt[0]+compass_width+doubt].copy()
        if testing:
            cv2.rectangle(screen, pt, (pt[0] + compass_width, pt[1] + compass_height), (0,0,255), 2)
            cv2.imshow('Compass Found', screen)
            cv2.imshow('Compass Mask', equalized)
            cv2.imshow('Compass', compass_image)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    return compass_image, compass_width+(2*doubt), compass_height+(2*doubt)




# ### Get navpoint offset

same_last_count = 0
last_last = {'x': 1, 'y': 100}
def get_navpoint_offset(testing=False, last=None):
    global same_last_count, last_last
    navpoint_template = cv2.imread(resource_path("templates/navpoint.png"), cv2.IMREAD_GRAYSCALE)
    navpoint_width, navpoint_height = navpoint_template.shape[::-1]
    pt = (0, 0)
    while True:
        compass_image, compass_width, compass_height = get_compass_image()
        mask_blue = filter_blue(compass_image)
#         filtered = filter_bright(compass_image)
        match = cv2.matchTemplate(mask_blue, navpoint_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.5
        loc = where( match >= threshold)
        for point in zip(*loc[::-1]):
                pt = point
        final_x = (pt[0] + ((1/2)*navpoint_width)) - ((1/2)*compass_width)
        final_y = ((1/2)*compass_height) - (pt[1] + ((1/2)*navpoint_height))
        if testing:
            cv2.rectangle(compass_image, pt, (pt[0] + navpoint_width, pt[1] + navpoint_height), (0,0,255), 2)
            cv2.imshow('Navpoint Found', compass_image)
            cv2.imshow('Navpoint Mask', mask_blue)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    if pt[0] == 0 and pt[1] == 0:
        if last:
            if last == last_last:
                same_last_count = same_last_count + 1
            else:
                last_last = last
                same_last_count = 0
            if same_last_count > 5:
                same_last_count = 0
                if random() < .9:
                    result = {'x': 1, 'y': 100}
                else:
                    result = {'x': 100, 'y': 1}
            else:
                result = last
        else:
            result = None
    else:
        result = {'x':final_x, 'y':final_y}
    logging.debug('get_navpoint_offset='+str(result))
    return result



# ### Get destination offset

def get_destination_offset(testing=False):
    destination_template = cv2.imread(resource_path("templates/destination.png"), cv2.IMREAD_GRAYSCALE)
    destination_width, destination_height = destination_template.shape[::-1]
    pt = (0, 0)
    width = (1/3)*SCREEN_WIDTH
    height = (1/3)*SCREEN_HEIGHT
    while True:
        screen = get_screen((1/3)*SCREEN_WIDTH, (1/3)*SCREEN_HEIGHT,(2/3)*SCREEN_WIDTH, (2/3)*SCREEN_HEIGHT)
        mask_orange = filter_orange2(screen)
#         equalized = equalize(screen)
        match = cv2.matchTemplate(mask_orange, destination_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.2
        loc = where( match >= threshold)
        for point in zip(*loc[::-1]):
                pt = point
        final_x = (pt[0] + ((1/2)*destination_width)) - ((1/2)*width)
        final_y = ((1/2)*height) - (pt[1] + ((1/2)*destination_height))
        if testing:
            cv2.rectangle(screen, pt, (pt[0] + destination_width, pt[1] + destination_height), (0,0,255), 2)
            cv2.imshow('Destination Found', screen)
            cv2.imshow('Destination Mask', mask_orange)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    if pt[0] == 0 and pt[1] == 0:
        result = None
    else:
        result = {'x':final_x, 'y':final_y}
    logging.debug('get_destination_offset='+str(result))
    return result


# ## Autopilot routines

# ### Undock

def undock():
    logging.debug('undock')
    if ship()['status'] != "in_station":
        logging.error('undock=err1')
        raise Exception('undock error 1')
    send(keys['UI_Back'], repeat=10)
    send(keys['HeadLookReset'])
    send(keys['UI_Down'], hold=3)
    send(keys['UI_Select'])
    sleep(1)
    if not (ship()['status'] == "starting_undock" or ship()['status'] == "in_undock"):
        logging.error('undock=err2')
        raise Exception("undock error 2")
    send(keys['HeadLookReset'])
    send(keys['SetSpeedZero'], repeat=2)
    wait = 120
    for i in range(wait):
        sleep(1)
        if i > wait - 1:
            logging.error('undock=err3')
            raise Exception('undock error 3')
        if ship()['status'] == "in_space":
            break
    logging.debug('undock=complete')
    return True



# ### Dock

def dock():
    logging.debug('dock')
    if ship()['status'] != "in_space":
        logging.error('dock=err1')
        raise Exception('dock error 1')
    tries = 3
    for i in range(tries):
        send(keys['UI_Back'], repeat=10)
        send(keys['HeadLookReset'])
        send(keys['UIFocus'], state=1)
        send(keys['UI_Left'])
        send(keys['UIFocus'], state=0)
        send(keys['CycleNextPanel'], repeat=2)
        send(keys['UI_Up'], hold=3)
        send(keys['UI_Right'])
        send(keys['UI_Select'])
        sleep(1)
        if ship()['status'] == "starting_dock" or ship()['status'] == "in_dock":
            break
        if i > tries-1:
            logging.error('dock=err2')
            raise Exception("dock error 2")
    send(keys['UI_Back'])
    send(keys['HeadLookReset'])
    send(keys['SetSpeedZero'], repeat=2)
    wait = 120
    for i in range(wait):
        sleep(1)
        if i > wait-1:
            logging.error('dock=err3')
            raise Exception('dock error 3')
        if ship()['status'] == "in_station":
            break
    send(keys['UI_Up'], hold=3)
    send(keys['UI_Down'])
    send(keys['UI_Select'])
    logging.debug('dock=complete')
    return True



# ### Align

def x_angle(point=None):
    if not point:
        return None
    result = degrees(atan(point['y']/point['x']))
    if point['x'] > 0:
        return +90 - result
    else:
        return -90 - result


# In[227]:


def align():
    logging.debug('align')
    if not (ship()['status'] == 'in_supercruise' or ship()['status'] == 'in_space'):
        logging.error('align=err1')
        raise Exception('align error 1')

    logging.debug('align= speed 100')
    send(keys['SetSpeed100'])

    logging.debug('align= avoid sun')
    while sun_percent() > 5:
        send(keys['PitchUpButton'], state=1)
    send(keys['PitchUpButton'], state=0)

    logging.debug('align= find navpoint')
    off = get_navpoint_offset()
    while not off:
        send(keys['PitchUpButton'], state=1)
        off = get_navpoint_offset()
    send(keys['PitchUpButton'], state=0)

    logging.debug('align= crude align')
    close = 3
    close_a = 18
    hold_pitch = 0.350
    hold_roll = 0.170
    ang = x_angle(off)
    while (off['x'] > close and ang > close_a) or           (off['x'] < -close and ang < -close_a) or           (off['y'] > close) or           (off['y'] < -close):

        while (off['x'] > close and ang > close_a) or               (off['x'] < -close and ang < -close_a):

            if off['x'] > close and ang > close:
                send(keys['RollRightButton'], hold=hold_roll)
            if off['x'] < -close and ang < -close:
                send(keys['RollLeftButton'], hold=hold_roll)

            if ship()['status'] == 'starting_hyperspace':
                return
            off = get_navpoint_offset(last=off)
            ang = x_angle(off)

        ang = x_angle(off)
        while (off['y'] > close) or               (off['y'] < -close):

            if off['y'] > close:
                send(keys['PitchUpButton'], hold=hold_pitch)
            if off['y'] < -close:
                send(keys['PitchDownButton'], hold=hold_pitch)

            if ship()['status'] == 'starting_hyperspace':
                return
            off = get_navpoint_offset(last=off)
            ang = x_angle(off)

        off = get_navpoint_offset(last=off)
        ang = x_angle(off)

    logging.debug('align= fine align')
    sleep(0.5)
    close = 50
    hold_pitch = 0.200
    hold_yaw = 0.400
    for i in range(5):
        new = get_destination_offset()
        if new:
            off = new
            break
        sleep(0.25)
    if not off:
        return
    while (off['x'] > close) or           (off['x'] < -close) or           (off['y'] > close) or           (off['y'] < -close):

        if off['x'] > close:
            send(keys['YawRightButton'], hold=hold_yaw)
        if off['x'] < -close:
            send(keys['YawLeftButton'], hold=hold_yaw)
        if off['y'] > close:
            send(keys['PitchUpButton'], hold=hold_pitch)
        if off['y'] < -close:
            send(keys['PitchDownButton'], hold=hold_pitch)

        if ship()['status'] == 'starting_hyperspace':
            return

        for i in range(5):
            new = get_destination_offset()
            if new:
                off = new
                break
            sleep(0.25)
        if not off:
            return

    logging.debug('align=complete')



# ### Jump

def jump():
    logging.debug('jump')
    tries = 3
    for i in range(tries):
        logging.debug('jump= try:'+str(i))
        if not (ship()['status'] == 'in_supercruise' or ship()['status'] == 'in_space'):
            logging.error('jump=err1')
            raise Exception('not ready to jump')
        sleep(0.5)
        logging.debug('jump= start fsd')
        send(keys['HyperSuperCombination'], hold=1)
        sleep(16)
        if ship()['status'] != 'starting_hyperspace':
            logging.debug('jump= misalign stop fsd')
            send(keys['HyperSuperCombination'], hold=1)
            sleep(2)
            align()
        else:
            logging.debug('jump= in jump')
            while ship()['status'] != 'in_supercruise':
                sleep(1)
            logging.debug('jump= speed 0')
            send(keys['SetSpeedZero'])
            logging.debug('jump=complete')
            return True
    logging.error('jump=err2')
    raise Exception("jump failure")



# ### Refuel

def refuel(refuel_threshold=33):
    logging.debug('refuel')
    scoopable_stars = ['F', 'O', 'G', 'K', 'B', 'A', 'M']
    if ship()['status'] != 'in_supercruise':
        logging.error('refuel=err1')
        return False
        raise Exception('not ready to refuel')

    if ship()['fuel_percent'] < refuel_threshold and ship()['star_class'] in scoopable_stars:
        logging.debug('refuel= start refuel')
        send(keys['SetSpeed100'])
    #     while not ship()['is_scooping']:
    #         sleep(1)
        sleep(4)
        logging.debug('refuel= wait for refuel')
        send(keys['SetSpeedZero'], repeat=3)
        while not ship()['fuel_percent'] == 100:
            sleep(1)
        logging.debug('refuel=complete')
        return True
    elif ship()['fuel_percent'] >= refuel_threshold:
        logging.debug('refuel= not needed')
        return False
    elif ship()['star_class'] not in scoopable_stars:
        logging.debug('refuel= needed, unsuitable star')
        return False
    else:
        return False



# ### Discovery scanner

scanner = 0

def set_scanner(state):
    scanner = state
    logging.info('set_scanner='+str(state))

def get_scanner():
    from dev_tray import STATE
    return STATE


# ### Position

def position(refueled_multiplier=1):
    logging.debug('position')
    scan = get_scanner()
    if scan == 1:
        logging.debug('position=scanning')
        send(keys['PrimaryFire'], state=1)
    elif scan == 2:
        logging.debug('position=scanning')
        send(keys['SecondaryFire'], state=1)
    send(keys['PitchUpButton'], state=1)
    sleep(5)
    send(keys['PitchUpButton'], state=0)
    send(keys['SetSpeed100'])
    send(keys['PitchUpButton'], state=1)
    while sun_percent() > 3:
        sleep(1)
    sleep(5)
    send(keys['PitchUpButton'], state=0)
    sleep(5*refueled_multiplier)
    if scan == 1:
        logging.debug('position=scanning complete')
        send(keys['PrimaryFire'], state=0)
    elif scan == 2:
        logging.debug('position=scanning complete')
        send(keys['SecondaryFire'], state=0)
    logging.debug('position=complete')
    return True


# ## Autopilot main

# ### status reference
#
# 'in-station'
#
# 'in-supercruise'
#
# 'in-space'
#
# 'starting-undocking'
#
# 'in-undocking'
#
# 'starting-docking'
#
# 'in-docking'


def autopilot():
    logging.info('\n'+200*'-'+'\n'+'---- AUTOPILOT START '+179*'-'+'\n'+200*'-')
    logging.info('get_latest_log='+str(get_latest_log(PATH_LOG_FILES)))
    logging.debug('ship='+str(ship()))
#     if ship()['target']:
#         undock()
    while ship()['target']:
        if ship()['status'] == 'in_space' or ship()['status'] == 'in_supercruise':
            logging.info('\n'+200*'-'+'\n'+'---- AUTOPILOT ALIGN '+179*'-'+'\n'+200*'-')
            align()
            logging.info('\n'+200*'-'+'\n'+'---- AUTOPILOT JUMP '+180*'-'+'\n'+200*'-')
            jump()
            logging.info('\n'+200*'-'+'\n'+'---- AUTOPILOT REFUEL '+178*'-'+'\n'+200*'-')
            refueled = refuel()
            logging.info('\n'+200*'-'+'\n'+'---- AUTOPILOT POSIT '+179*'-'+'\n'+200*'-')
            if refueled:
                position(refueled_multiplier=4)
            else:
                position(refueled_multiplier=1)
    send(keys['SetSpeedZero'])
    logging.info('\n'+200*'-'+'\n'+'---- AUTOPILOT END '+181*'-'+'\n'+200*'-')
