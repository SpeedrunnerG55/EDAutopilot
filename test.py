
from immageProcessing import LoadHSVs , createWindows, createSliderWindow
from functions import dock, undock
from calculations import sun_percent
from time import sleep
from readLogs import printSytemInformation, STAR_CLASS
from programInfo import showInfo

from offsets import get_navpoint_offset, get_destination_offset

def test(functions):
    while(True):
        print(function())

def hsv_slider(functions,output=False):
    createWindows()
    while(True):
        for function in functions:
            if(output):
                print(function(testing=True))
            else:
                function(testing=True)



# for i in range(5):
#     print("starting in {}".format(5 - i))
#     sleep(1)

# dock()

printSytemInformation()

print(STAR_CLASS)
LoadHSVs()
# createSliderWindow('sun',1800,600)
# test(sun_percent)
hsv_slider([get_navpoint_offset,get_destination_offset])
