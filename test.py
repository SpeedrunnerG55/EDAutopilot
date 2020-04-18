from dev_autopilot import *
from numpy import array
from time import sleep
import mss
import cv2 # see reference 2
#

printSytemInformation()


# while(True):
#     screen = get_screen(1800,100,2600,900)
#     showHSV('hist',screen)
#     cv2.imshow('screen',screen)
#     cv2.waitKey(1)

# logging.info("CountDown")
# max = 4
# for i in range(1,max):
#     logging.info(max - i)
#     sleep(1);

# while(True):
#     tineRadio()

# while(True):
#     getSpectrumOffset()

# clear_input(get_bindings())

#

left = 0
top = 0
right = 1600
bottom = 600

# img = cv2.imread(resource_path("examples/altitude.png"))
# getEntryOffset(img)
while(True):
    get_navpoint_offset()
    cv2.waitKey(1)


#     # get_destination_offset()
#     get_navpoint_offset()


#
# consoleHeadder("THIS IS A TEST")
# sleep(1)
# consoleHeadder("THIS IS OLNY A TEST")
# sleep(1)
#
# discoveryScan()
#
# while(True):
#     getSpectrumOffset();
