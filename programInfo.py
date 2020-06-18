from emulation import PATH_KEYBINDINGS, KEY_REPEAT_DELAY,KEY_DEFAULT_DELAY
from readLogs import PATH_LOG_FILES
from consoleOut import consoleHeadder

RELEASE = 'v19.05.15-alpha-18'
KEY_MOD_DELAY = 0.001
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

def showInfo():

    consoleHeadder("AUTOPILOT DATA")

    print('RELEASE='+str(RELEASE))
    print('PATH_LOG_FILES='+str(PATH_LOG_FILES))
    print('PATH_KEYBINDINGS='+str(PATH_KEYBINDINGS))
    print('KEY_MOD_DELAY='+str(KEY_MOD_DELAY))
    print('KEY_DEFAULT_DELAY='+str(KEY_DEFAULT_DELAY))
    print('KEY_REPEAT_DELAY='+str(KEY_REPEAT_DELAY))
    print('SCREEN_WIDTH='+str(SCREEN_WIDTH))
    print('SCREEN_HEIGHT='+str(SCREEN_HEIGHT))
