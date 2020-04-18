import sys
from sys import platform
from os import environ, listdir
from os.path import join, isfile, getmtime, abspath
from json import loads
from math import degrees, atan, cos, sin, pi, sqrt
from random import random
from time import sleep,time
from numpy import sum, array, where
from datetime import datetime
from xml.etree.ElementTree import parse
import cv2 # see reference 2
import logging
import colorlog
import mss
from statistics import mode

from pynput.keyboard import Key, Controller

keyboard = Controller()

# from pynput.keyboard import Key, Controller

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

def consoleHeadder(text=None):
    width = 100
    logging.info('\n'+width*'-'+'\n'+ "---- " +text+ " " +(width - len(text) - 6)*'-'+'\n'+width*'-')

logger.debug('This is a DEBUG message. These information is usually used for troubleshooting')
logger.info('This is an INFO message. These information is usually used for conveying information')
logger.warning('some warning message. These information is usually used for warning')
logger.error('some error message. These information is usually used for errors and should not happen')
logger.critical('some critical message. These information is usually used for critical error, and will usually result in an exception.')

consoleHeadder("AUTOPILOT DATA")

# ## Constants

if platform == "linux" or platform == "linux2":
    path_logs = "/home/" + environ['USER'] + "/.steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous"
    path_bindings = "/home/" + environ['USER'] + "/.steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Local Settings/Application Data/Frontier Developments/Elite Dangerous/Options/Bindings"
elif platform == "darwin":
    path_logs = "mac path i dunno"
    path_bindings = "mac path i dunno"
elif platform == "win32":
    path_logs = environ['USERPROFILE'] + "\Saved Games\Frontier Developments\Elite Dangerous"
    path_bindings = environ['LOCALAPPDATA'] + "\Frontier Developments\Elite Dangerous\Options\Bindings"

RELEASE = 'v19.05.15-alpha-18'
PATH_LOG_FILES = path_logs
PATH_KEYBINDINGS = path_bindings
KEY_MOD_DELAY = 0.001
KEY_DEFAULT_DELAY = 0.200
KEY_REPEAT_DELAY = 0.100
FUNCTION_DEFAULT_DELAY = 0.500
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

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

                if log_event == 'ApproachBody':
                    ship['status'] = 'in_orbitalcruise'

                if log_event == 'StartJump':
                    ship['status'] = str('starting_'+log['JumpType']).lower()

                elif log_event == 'SupercruiseEntry' or log_event == 'FSDJump' or log_event == 'LeaveBody':
                    ship['status'] = 'in_supercruise'

                elif log_event == 'SupercruiseExit' or log_event == 'DockingCancelled' or (log_event == 'Music' and ship['status'] == 'in_undocking') or (log_event == 'Location' and log['Docked'] == False):
                    if ship['status'] == 'in_orbitalcruise':
                        ship['status'] = 'in_glide'
                    else:
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
        logging.info('get_bindings_<'+str(key)+'>='+str(keys[key]))
    except Exception as e:
        logging.warning(str("get_bindings_<"+key+">= does not have a valid keyboard keybind.").upper())

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
        'Comma':',',
        'Period':'.',
        'Numpad_9':'9',
        'Numpad_7':'7',
        'Apostrophe':'\'',
        'SemiColon':';',
        'Slash':'/',
        'Space':' '
    }


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
        logging.warning('SEND=NONE !!!!!!!!')
        return

    logging.info('send=key:'+str(key)+',hold:'+str(hold)+',repeat:'+str(repeat)+',repeat_delay:'+str(repeat_delay)+',state:'+str(state))
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
            send(to_clear[key], state=0)
    logging.debug('clear_input')


# ### Get screen

def PrintImmage(fileName,immage):
    cv2.imwrite(resource_path("Captures/" + fileName + ".png"),immage)
    # whattoshow["img"] = immage

def get_screen(x_left, y_top, x_right, y_bot):
    im = array(mss.mss().grab((x_left, y_top, x_right, y_bot)))  # type: ignore
    im = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
    return im

def show_immage(name,image):
    cv2.imshow(name,image)
    cv2.waitKey(10)

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
        show_immage('image', frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break


# ### Equalization

def equalize(image=None):
    img = image.copy()
    # Load the image in greyscale
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # create a CLAHE object (Arguments are optional).
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    img_out = clahe.apply(img_gray)
    return img_out



# ### Filter bright

def filter_bright(image=None):
    img = image.copy()
    equalized = equalize(img)
    equalized = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
    equalized = cv2.cvtColor(equalized, cv2.COLOR_BGR2HSV)
    filtered = cv2.inRange(equalized, array([0, 0, 215]), array([0, 0, 255]))
    return filtered



# ### Filter sun

def filter_sun(image=None):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # filter Elite UI orange
    filtered = cv2.inRange(hsv, array([0, 0, 200]), array([255, 130, 255]))
    return filtered



# ### Filter orange

def filter_orange(image=None):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # filter Elite UI orange
    if(ship()['star_class'] == 'A'):
        filtered = cv2.inRange(hsv, array([0, 25, 200]), array([19, 255, 255]))
    elif(ship()['star_class'] == 'F'):
        filtered = cv2.inRange(hsv, array([0, 60, 200]), array([25, 255, 255]))
    elif(ship()['star_class'] == 'G'):
        filtered = cv2.inRange(hsv, array([4, 130, 210]), array([45, 255, 255]))
    elif(ship()['star_class'] == None):
        filtered = cv2.inRange(hsv, array([0, 25, 180]), array([80, 255, 255]))
    else:
        filtered = cv2.inRange(hsv, array([0, 110, 210]), array([15, 255, 255]))
    return filtered


# ### Filter orange2

def filter_orange2(image=None):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # filter Elite UI orange
    filtered = cv2.inRange(hsv, array([15, 220, 220]), array([30, 255, 255]))
    return filtered


# ### Filter blue

def filter_blue(image=None):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # filter Elite UI orange
    if(ship()['star_class'] == 'A'):
        filtered = cv2.inRange(hsv, array([80, 10, 240]), array([110, 60, 255]))
    elif(ship()['star_class'] == 'G'):
        filtered = cv2.inRange(hsv, array([90, 15, 190]), array([190, 70, 255]))
    if(ship()['star_class'] == None):
        filtered = cv2.inRange(hsv, array([80, 100, 150]), array([120, 255, 255]))
    else:
        filtered = cv2.inRange(hsv, array([80, 0, 200]), array([180, 100, 255]))
    return filtered

# ### Get sun

def sun_percent():
    left = 0
    top = 0
    right = 1600
    bottom = 700
    screen = get_screen(left,top,right,bottom)
    filtered = filter_sun(screen)
    white = sum(filtered == 255)
    black = sum(filtered != 255)
    result = white / black
    return result * 100


# ### Get compass image

def get_compass_image(testing=True):
    compass_template = cv2.imread(resource_path("templates/compass.png"), cv2.IMREAD_GRAYSCALE)
    compass_width, compass_height = compass_template.shape[::-1]
    compass_image = compass_template.copy()
    doubt = 7

    screen = get_screen(530,610,720,790)
    mask_orange = filter_orange(screen)
    # justCompass = cv2.bitwise_and(screen, screen, mask=mask_orange)

    match = cv2.matchTemplate(mask_orange, compass_template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.280
    loc = where( match >= threshold)

    pt = (doubt, doubt)
    for point in zip(*loc[::-1]):
            pt = point
    compass_image = screen[pt[1]-doubt : pt[1]+compass_height+doubt, pt[0]-doubt : pt[0]+compass_width+doubt].copy()
    if testing:
        cv2.rectangle(screen, pt, (pt[0] + compass_width, pt[1] + compass_height), (0,0,255), 2)
        # PrintImmage('Compass Found', screen)
        # PrintImmage('Compass Mask', mask_orange)
        # showHSV('justCompass', justCompass)
        show_immage('Compass Found', screen)
        show_immage('Compass Mask', mask_orange)
    return compass_image, compass_width+(2*doubt), compass_height+(2*doubt)


# ### Get navpoint offset

same_last_count = 0
last_last = {'x': 1, 'y': 100}
def get_navpoint_offset(testing=True, last=None):

    global same_last_count, last_last
    navpoint_template = cv2.imread(resource_path("templates/navpoint.png"), cv2.IMREAD_GRAYSCALE)
    navpoint_width, navpoint_height = navpoint_template.shape[::-1]
    pt = (0, 0)

    compass_image, compass_width, compass_height = get_compass_image()

    centerx = int((1/2)*compass_width)
    centery = int((1/2)*compass_height)

    cv2.circle(compass_image,(centerx,centery),35,(0,0,0),20)

    mask_blue = filter_blue(compass_image)
    # justNavpoint = cv2.bitwise_and(compass_image, compass_image, mask=mask_blue)

    match = cv2.matchTemplate(mask_blue, navpoint_template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.3
    loc = where( match >= threshold)
    for point in zip(*loc[::-1]):
            pt = point
    final_x = (pt[0] + ((1/2)*navpoint_width)) - ((1/2)*compass_width)
    final_y = ((1/2)*compass_height) - (pt[1] + ((1/2)*navpoint_height))

    endx = int((pt[0] + ((1/2)*navpoint_width)))
    endy = int((pt[1] + ((1/2)*navpoint_height)))

    if testing:
        cv2.rectangle(compass_image, pt, (pt[0] + navpoint_width, pt[1] + navpoint_height), (0,0,255), 2)
        cv2.line(compass_image,(centerx,centery),(endx,endy),(0, 255, 0),2)
        # PrintImmage('Navpoint Found', compass_image)
        # PrintImmage('Navpoint Mask', mask_blue)
        # showHSV('justNavpoint', justNavpoint)
        show_immage('Navpoint Found', compass_image)
        show_immage('Navpoint Mask', mask_blue)

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

def get_destination_offset(testing=True):
    destination_template = cv2.imread(resource_path("templates/destination.png"), cv2.IMREAD_GRAYSCALE)
    destination_width, destination_height = destination_template.shape[::-1]
    pt = (0, 0)

    left = 500
    top = 300
    right = 1100
    bottom = 600

    width = right - left
    height = bottom - top

    centerx = int((1/2)*width)
    centery = int((1/2)*height)

    screen = get_screen(left,top,right,bottom)
    mask_orange = filter_orange2(screen)

    match = cv2.matchTemplate(mask_orange, destination_template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.3
    loc = where( match >= threshold)
    for point in zip(*loc[::-1]):
            pt = point
    final_x = int((pt[0] + ((1/2)*destination_width)) - ((1/2)*width))
    final_y = int(((1/2)*height) - (pt[1] + ((1/2)*destination_height)))

    endx = int((pt[0] + ((1/2)* destination_width)))
    endy = int((pt[1] + ((1/2)*destination_height)))
    result = {'x':final_x, 'y':final_y}
    if testing:
        cv2.rectangle(screen, pt, (pt[0] + destination_width, pt[1] + destination_height), (0,0,255), 2)
        cv2.line(screen,(centerx,centery),(endx,endy),(0, 255, 0),2)
        # PrintImmage('Destination Found', screen)
        # PrintImmage('Destination Mask', mask_orange)
        show_immage('Destination Found', screen)
        show_immage('Destination Mask', mask_orange)
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
    logging.info('align')
    if not (ship()['status'] == 'in_supercruise' or ship()['status'] == 'in_space'):
        logging.error('align=err1')
        raise Exception('align error 1')

    logging.info('align= speed 100')
    send(keys['SetSpeed100'])

    logging.info('align= avoid sun')
    while sun_percent() > 5:
        send(keys['PitchUpButton'], state=1)
    send(keys['PitchUpButton'], state=0)

    logging.info('align= find navpoint')
    off = get_navpoint_offset()

    while not off:
        send(keys['PitchUpButton'], state=1)
        off = get_navpoint_offset()
    send(keys['PitchUpButton'], state=0)

    logging.info('align= crude align')
    close = 1
    action = None
    while (abs(off['x']) > close) or (abs(off['y']) > close):
        while (abs(off['x']) > close):
            if off['x'] > close and action is not 'right':
                action = 'right'
                send(keys['RollRightButton'], state=1)
                send(keys['RollLeftButton'], state=0)
            elif off['x'] < -close and action is not 'left':
                action = 'left'
                send(keys['RollRightButton'], state=0)
                send(keys['RollLeftButton'], state=1)
            if ship()['status'] == 'starting_hyperspace':
                return
            off = get_navpoint_offset(last=off)
        if(action == 'right'):
            send(keys['RollRightButton'], state=0)
        elif(action == 'left'):
            send(keys['RollLeftButton'], state=0)
        action = None
        while (abs(off['y']) > close):
            if off['y'] > close and action is not 'up':
                action = 'up'
                send(keys['PitchDownButton'], state=0)
                send(keys['PitchUpButton'], state=1)
            elif off['y'] < -close and action is not 'down':
                action = 'down'
                send(keys['PitchDownButton'], state=1)
                send(keys['PitchUpButton'], state=0)
            if ship()['status'] == 'starting_hyperspace':
                return
            off = get_navpoint_offset(last=off)
        if(action == 'up'):
            send(keys['PitchUpButton'], state=0)
        elif(action == 'down'):
            send(keys['PitchDownButton'], state=0)
        off = get_navpoint_offset(last=off)
    logging.info('align= fine align')
    sleep(0.5)
    close = 24
    off = get_destination_offset()
    if not off:
        return
    while (abs(off['x']) > close) or (abs(off['y']) > close):
        while (abs(off['x']) > close):
            if off['x'] > close:
                action = 'right'
                send(keys['YawRightButton'], state=1)
                send(keys['YawLeftButton'], state=0)
            elif off['x'] < -close:
                action = 'left'
                send(keys['YawLeftButton'], state=1)
                send(keys['YawRightButton'], state=0)
            off = get_destination_offset()
        if(action == 'right'):
            send(keys['YawRightButton'], state=0)
        elif(action == 'left'):
            send(keys['YawLeftButton'], state=0)
        action = None
        while (abs(off['y']) > close):
            if off['y'] > close:
                action = 'up'
                send(keys['PitchUpButton'], state=1)
                send(keys['PitchDownButton'], state=0)
            elif off['y'] < -close:
                action = 'down'
                send(keys['PitchDownButton'], state=1)
                send(keys['PitchUpButton'], state=0)
            if ship()['status'] == 'starting_hyperspace':
                return
            off = get_destination_offset()
        if(action == 'up'):
            send(keys['PitchUpButton'], state=0)
        elif(action == 'down'):
            send(keys['PitchDownButton'], state=0)
        action = None
    logging.info('align=complete')


# ### Jump

def jump():
    logging.info('jump')
    tries = 3
    for i in range(tries):
        logging.info('jump= try:'+str(i))
        if not (ship()['status'] == 'in_supercruise' or ship()['status'] == 'in_space'):
            logging.error('jump=err1')
            raise Exception('not ready to jump')
        sleep(0.5)
        logging.info('jump= start fsd')
        send(keys['HyperSuperCombination'], hold=1)
        send(keys['SetSpeed100'])
        sleep(16)
        if ship()['status'] != 'starting_hyperspace':
            logging.info('jump= misalign stop fsd')
            send(keys['HyperSuperCombination'], hold=1)
            sleep(2)
            align()
        else:
            logging.info('jump= in jump')
            while ship()['status'] != 'in_supercruise':
                sleep(1)
            logging.info('jump= speed 0')
            send(keys['SetSpeedZero'])
            logging.info('jump=complete')
            return True
    logging.error('jump=err2')
    raise Exception("jump failure")


def filter_Signals(image=None):
    height = 628 - 598
    width = 961 - 458
    pt = [(0,int(height / 2)),(width,int(height / 2))]
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # filter Elite UI orange
    filtered = cv2.inRange(hsv, array([95,150,90]), array([160, 255, 200]))
    filtered = cv2.line(filtered,pt[0],pt[1],(0,255,0),1)
    show_immage('Spectrum filtered', filtered)
    # PrintImmage('Spectrum filtered', filtered)
    filtered = cv2.blur(filtered,(2,50))
    ret,filtered = cv2.threshold(filtered,25,255,cv2.THRESH_BINARY)
    return filtered


def filter_Curser(image=None):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # hsv = cv2.blur(hsv,(2,50))
    filtered = cv2.inRange(hsv, array([0,0,65]), array([255,25, 130]))
    return filtered

# # ### get FSS spectrum offset
#
def getSpectrumOffset(testing=True):
    screen = get_screen(458,598,961,628)
    height = 628 - 598
    width = 961 - 458

    spectrum_template = cv2.imread(resource_path("templates/spectrum spot.png"), cv2.IMREAD_GRAYSCALE)
    ceuser_template = cv2.imread(resource_path("templates/spectrum spot.png"), cv2.IMREAD_GRAYSCALE)

    spots = filter_Signals(screen)
    curser = filter_Curser(screen)

    scanLine = 7

    x1 = 0;
    curserPos = 0
    spotPos = 0

    for i in range(1,width):
        if(curser[scanLine][i] == 255):
            screen = cv2.line(screen,(i,0),(i,height),(0,255,0,1))
            curserPos = i
            break
    for i in range(1,width):
        if(spots[scanLine][i] == 255 and spots[scanLine][i-1] == 0):
            x1 = i;
        if(spots[scanLine][i] == 0 and spots[scanLine][i-1] != 0):
            x2 = i;
            CenterX = int((x2 - x1)/2) + x1
            spotPos = CenterX
            screen = cv2.line(screen,(CenterX,0),(CenterX,height),(0,0,255),1)
            break

    screen = cv2.line(screen,(curserPos,int(height/2)),(spotPos,int(height/2)),(255,0,0),1)
    offset = curserPos - spotPos

    # print(curser)

    if testing:
        cv2.line(screen,(pt,0),(pt,height), (0,0,255), 1)
        # PrintImmage('Spectrum', screen)
        # PrintImmage('Spectrum spots', spots)
        # PrintImmage('Spectrum curser', curser)
        show_immage('Spectrum', screen)
        show_immage('Spectrum spots', spots)
        show_immage('Spectrum curser', curser)

    return offset
# ### tuneRadio

def tuneRadio():
    off = getSpectrumOffset()
    close = 3
    while (off > close or off < -close):
        print(off)
        amt = abs(off/330)
        if(off > close):
            send(keys['ExplorationFSSRadioTuningX_Decrease'],hold=amt)
        elif(off < close):
            send(keys['ExplorationFSSRadioTuningX_Increase'],hold=amt)
        sleep(1.5);
        off = getSpectrumOffset()

# ### showHSV
def showHSV(name=None,image=None):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # hsv = cv2.blur(hsv,(2,50))
    hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
    show_immage(name + '-hist',hist)


# ### filterHorizon
def filterHorizon(image=None):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # hsv = cv2.blur(hsv,(2,50))
    filtered = cv2.inRange(hsv, array([115,223,100]), array([123, 255, 200]))
    return filtered

def scaleImage(image=None,scale_percent=None):
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    # resize image
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    return resized

def findCircle(image=None):

    width, height = image.shape[::-1]

    x1,x2,x3,y1,y2,y3 = 0,0,0,0,0,0
    for j in range(1,width,120):
        for i in range(1,height):
            if(image[i][j] == 255 and x1 == 0):
                x1 = j
                y1 = i
                origin1 = (x1,0)
                break
            if(image[i][j] == 255):
                x3 = j
                y3 = i
                origin3 = (x3,0)
                break
    if(x3 != 0):
        x2 = int((x3 - x1) / 2) + x1
        for i in range(1,height):
            if(image[i][x2] == 255):
                y2 = i
                origin2 = (x2,0)
                break

    if(y2 == 0):
        x1,x2,x3,y1,y2,y3 = 0,0,0,0,0,0
        for i in range(1,height,60):
            for j in range(1,width):
                if(image[i][j] == 255 and y1 == 0):
                    x1 = j
                    y1 = i
                    origin1 = (0,y1)
                    break
                if(image[i][j] == 255):
                    x3 = j
                    y3 = i
                    origin3 = (0,y3)
                    break
        if(y3 != 0):
            y2 = int((y3 - y1) / 2) + y1
            for j in range(1,width):
                if(image[y2][j] == 255):
                    x2 = j
                    origin2 = (0,y2)
                    break


    if(y2 == 0 or x2 == 0):
        return 0,0,0
    # else:
        # print('point 1 ({},{})\npoint 2 ({},{})\npoint 3 ({},{})\n'.format(x1,y1,x2,y2,x3,y3))


    x12 = x1 - x2
    x13 = x1 - x3

    y12 = y1 - y2
    y13 = y1 - y3

    y31 = y3 - y1
    y21 = y2 - y1

    x31 = x3 - x1
    x21 = x2 - x1

    # x1^2 - x3^2
    sx13 = pow(x1, 2) - pow(x3, 2)

    # y1^2 - y3^2
    sy13 = pow(y1, 2) - pow(y3, 2)

    sx21 = pow(x2, 2) - pow(x1, 2)
    sy21 = pow(y2, 2) - pow(y1, 2);

    f = (((sx13) * (x12) + (sy13) *
          (x12) + (sx21) * (x13) +
          (sy21) * (x13)) // (2 *
          ((y31) * (x12) - (y21) * (x13))));

    g = (((sx13) * (y12) + (sy13) * (y12) +
          (sx21) * (y13) + (sy21) * (y13)) //
          (2 * ((x31) * (y12) - (x21) * (y13))));

    c = (-pow(x1, 2) - pow(y1, 2) -
         2 * g * x1 - 2 * f * y1);

    # eqn of circle be x^2 + y^2 + 2*g*x + 2*f*y + c = 0
    # where centre is (h = -g, k = -f) and
    # radius r as r^2 = h^2 + k^2 - c
    h = -g;
    k = -f;
    sqr_of_r = h * h + k * k - c;

    # r is the radius
    r = int(sqrt(sqr_of_r));

    cv2.line(image,origin1,(x1,y1),(255, 128, 0),2)
    cv2.line(image,origin2,(x2,y2),(255, 128, 0),2)
    cv2.line(image,origin3,(x3,y3),(255, 128, 0),2)

    cv2.line(image,(x1,y1),(h,k),(255, 128, 0),2)
    cv2.line(image,(x2,y2),(h,k),(255, 128, 0),2)
    cv2.line(image,(x3,y3),(h,k),(255, 128, 0),2)

    cv2.circle(image, (h,k), r, (255, 0, 0), 2)

    return h,k,r


def pointonCircle(x,y,r,angle):
    return(x + int(cos(angle) * r),y - int(sin(angle) * r))

# ### getHorizon
def getEntryOffset(img=None):

    mask_horizon = filterHorizon(img)
    x,y,r = findCircle(mask_horizon)

    finalR = r - (r/10)

    finalX,fianlY = pointonCircle(x,y,r - (r/10),pi/2)

    angle1 = (pi/2) - (pi/100)
    angle2 = (pi/2) + (pi/100)

    height = (int(cos(angle2) * r) - int(cos(angle1) * r)) / 2

    cv2.circle(img,(x,y),r,(0,128,0),2)

    cv2.circle(img,(finalX,fianlY),2,(0,0,255),3)

    cv2.line(img, pointonCircle(x,y,finalR-height,angle1),pointonCircle(x,y,finalR+height,angle1), (255, 128, 0), 3)
    cv2.line(img, pointonCircle(x,y,finalR-height,angle2),pointonCircle(x,y,finalR+height,angle2), (255, 128, 0), 3)

    cv2.line(img, pointonCircle(x,y,finalR-height,angle1),pointonCircle(x,y,finalR-height,angle2), (255, 128, 0), 3)
    cv2.line(img, pointonCircle(x,y,finalR+height,angle1),pointonCircle(x,y,finalR+height,angle2), (255, 128, 0), 3)

	# show the output image

    cv2.imshow("output",scaleImage(img,50))
    cv2.imshow("mask_horizon",scaleImage(mask_horizon,50))


    # if testing:
        # PrintImmage('Horizon Found', screen)
        # PrintImmage('Horizon Mask', mask_horizon)
        # show_immage('Horizon Found', screen)
        # show_immage('justHorizon', justHorizon)
        # show_immage('Horizon Mask', mask_horizon)


# ### filterAltitude
def filterAltidude(image=None):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # hsv = cv2.blur(hsv,(2,50))

    low  =  9,180,130
    high = 12,255,240

    filtered = cv2.inRange(hsv, array([low[0],low[1],low[2]]), array([high[0],high[1],high[2]]))
    justfiltered = cv2.bitwise_and(image, image, mask=filtered)
    showHSV('justfiltered', justfiltered)

    return filtered


def getPoints(image=None):

    width, height = image.shape[::-1]

    points = []

    first = None;

    for i in range(1,height,10):
        for j in range(1,width):
            if(image[i][width - j] == 255):
                if first == None:
                    first = i
                if(i < first + 180):
                    y = i
                    x = width - j
                    points.append((x,y))
                break

    return points



def getDistance(point1,point2):
    return sqrt(pow(point2[0] - point1[0],2) + pow(point2[1] - point1[1],2))

def getDistances(points):

    distances = []

    for i in range(len(points) - 1):
        distance = round(getDistance(points[i],points[i+1]),1)
        distances.append(distance)
    return distances

def cleanPoints(points,source=None):

    distances = getDistances(points)

    m = mode(distances)

    tollerance = abs(m * .2)
    upperlim = m + tollerance
    lowerlim = m - tollerance

    cleaned = []

    for i in range(len(distances) - 1):

        distance1 = distances[i]
        distance2 = distances[i+1]

        spec = distance1 > lowerlim and distance1 < upperlim and distance2 > lowerlim and distance2 < upperlim

        if(not spec):
            source = cv2.circle(source,points[i],2,(0,0,128),2)
        else:
            source = cv2.circle(source,points[i],2,(0,128,0),2)
            cleaned.append(points[i + 1])

    return cleaned

def getaltLine(image=None,source=None):

    points = getPoints(image)

    points = cleanPoints(points,source)

    return points


### getAltitude
def getAltitude(testing=True):

    left = 935
    top = 320
    right = 1150
    bottom = 620

    screen = get_screen(left,top,right,bottom)
    # screen = cv2.imread(resource_path("examples/altitude.png"))
    # screen = screen[300:600, 900:1100]

    mask_Altidude = filterAltidude(screen)


    # if ship()['status'] == 'in_orbitalcruise' or ship()['status'] == 'in_glide':
    #
    #     points = getaltLine(mask_Altidude,screen)
    #
    #     screen = cv2.circle(screen,points[0],2,(128,0,0),2)
    #     screen = cv2.circle(screen,points[-1],2,(128,0,0),2)
    #     screen = cv2.line(screen,points[0],points[-1],(128,0,0),2)

    show_immage('screen', screen)
    show_immage('mask_Altidude', mask_Altidude)


# ### System information

def printSytemInformation():
    logging.info("Star Type: " + str(ship()['star_class']))

# ### Discovery Scan

def discoveryScan():
    send(keys['PrimaryFire'],hold=5.3)


# ### Refuel

def refuel(refuel_threshold=100):
    logging.debug('refuel')
    scoopable_stars = ['F', 'O', 'G', 'K', 'B', 'A', 'M']
    if ship()['status'] != 'in_supercruise':
        logging.error('refuel=err1')
        return False
        raise Exception('not ready to refuel')

    if ship()['fuel_percent'] < refuel_threshold and ship()['star_class'] in scoopable_stars:
        logging.info('refuel= start refuel')
        send(keys['SetSpeed100'])
    #     while not ship()['is_scooping']:
    #         sleep(1)
        sleep(4.2)
        logging.info('refuel= wait for refuel')
        send(keys['SetSpeedZero'], repeat=3)
        while not ship()['fuel_percent'] == 100:
            sleep(1)
        logging.info('refuel=complete')
        return True
    elif ship()['fuel_percent'] >= refuel_threshold:
        logging.info('refuel= not needed')
        return False
    elif ship()['star_class'] not in scoopable_stars:
        logging.info('refuel= needed, unsuitable star')
        return False
    else:
        return False



# ### Discovery scanner


# ### Position

def position(refuled):
    logging.debug('position')
    send(keys['PitchUpButton'], state=1)
    sleep(5)
    send(keys['PitchUpButton'], state=0)
    send(keys['SetSpeed50'])
    send(keys['PitchUpButton'], state=1)
    while sun_percent() > 3:
        sleep(1)
    send(keys['SetSpeed100'])
    sleep(5)
    send(keys['PitchUpButton'], state=0)
    if(refuled):
        sleep(7)
    else:
        sleep(3)
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
# 'in-docking',,,


def autopilot():

    consoleHeadder("AUTOPILOT START")
    logging.info('get_latest_log='+str(get_latest_log(PATH_LOG_FILES)))
    logging.debug('ship='+str(ship()))
#     if ship()['target']:
#         undock()
    printSytemInformation();
    while ship()['target']:
        if ship()['status'] == 'in_space' or ship()['status'] == 'in_supercruise':
            consoleHeadder("AUTOPILOT ALIGN");  align();
            consoleHeadder("AUTOPILOT JUMP");   jump();  printSytemInformation();
            consoleHeadder("AUTOPILOT SCAN");   discoveryScan();
            consoleHeadder("AUTOPILOT REFUEL"); refueled = refuel(); #return weather or not a reful occured
            consoleHeadder("AUTOPILOT POSIT");  position(refueled); #pitch up more because you are closer to the star
    send(keys['SetSpeedZero'])
    consoleHeadder("AUTOPILOT END")
