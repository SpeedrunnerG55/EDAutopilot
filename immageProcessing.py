import cv2 # see reference 2
import mss

from time import sleep
from numpy import array

from jsonreader import readFromFile, writeToFile
from fileMananager import resource_path
from emulation import SelectGame
from readLogs import STAR_CLASS

# ### Get screen

def get_screen(x_left, y_top, x_right, y_bot):
    im = array(mss.mss().grab((x_left, y_top, x_right, y_bot)))  # type: ignore
    im = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
    return im


def spawnWindow(name,x,y):
    logo = cv2.imread(resource_path("src/logo.png"))
    logo = scaleImage(logo,6)
    print("spawning {}".format(name))
    show_immage(name,logo)
    sleep(.07)
    cv2.moveWindow(name,x,y)
    cv2.waitKey(1)


def scaleImage(image=None,scale_percent=None):
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    # resize image
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    return resized


def createWindows(select=False):

    spawnWindow("Compass Found",1800,0)
    spawnWindow("Compass Mask",2000,0)
    spawnWindow("Compass match",2000,230)
    spawnWindow("Navpoint Found",1600,0)
    spawnWindow("Navpoint Mask",1730,0)
    spawnWindow("Navpoint match",1660,90)
    spawnWindow("Destination Found",2200,0)
    spawnWindow("Destination Mask",2750,0)
    spawnWindow("Destination match",2750,280)

    LoadHSVs()

    createSliderWindow('orange',1700,500)
    createSliderWindow('blue',2100,500)

    if(select):
        SelectGame()


def show_immage(name,image,pt=None):
    cv2.imshow(name,image)
    if(not pt == None):
        x = pt[0]
        y = pt[1]
        cv2.moveWindow(name,x,y)
    cv2.waitKey(1)

# ### showHSV
def showHSV(name=None,image=None):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # hsv = cv2.blur(hsv,(2,50))
    hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
    show_immage(name + '-hist',hist)

# ### HSV slider tool

def callback(x):
    pass

HSV_List = {}

def LoadHSVs():
    global HSV_List
    HSV_List = readFromFile('HSV.json')

def SaveHSVs():
    global HSV_List
    writeToFile(HSV_List,'HSV.json')

def getHSVs(collor,frame=None,hsv=None):

    if collor in HSV_List:
        if STAR_CLASS in HSV_List[collor]:
            lower_hsv,higher_hsv = HSV_List[collor][STAR_CLASS]
            lower_hsv,higher_hsv = array(lower_hsv),array(higher_hsv)
        else:
            lower_hsv,higher_hsv = readTrackbars(frame,hsv,collor,200)

    return lower_hsv,higher_hsv

def createSliderWindow(collor,x,y):

    spawnWindow(collor,x,y)

    print(STAR_CLASS)

    if collor in HSV_List:
        if STAR_CLASS in HSV_List[collor]:
            defaults = getHSVs(collor)
        else:
            defaults = (0, 0, 0),(179, 255, 255)
    elif(collor == 'sun'):
        defaults = (0, 0, 200), (179, 240, 255)
    else:
        print("collor {} not found".format(collor))

    cv2.createTrackbar('lowH',collor,defaults[0][0],179,callback)
    cv2.createTrackbar('highH',collor,defaults[1][0],179,callback)

    cv2.createTrackbar('lowS',collor,defaults[0][1],255,callback)
    cv2.createTrackbar('highS',collor,defaults[1][1],255,callback)

    cv2.createTrackbar('lowV',collor,defaults[0][2],255,callback)
    cv2.createTrackbar('highV',collor,defaults[1][2],255,callback)


def readTrackbars(frame,hsv,name,scale):

    # get trackbar positions
    lowH = cv2.getTrackbarPos('lowH',name)
    highH = cv2.getTrackbarPos('highH',name)
    lowS = cv2.getTrackbarPos('lowS',name)
    highS = cv2.getTrackbarPos('highS',name)
    lowV = cv2.getTrackbarPos('lowV',name)
    highV = cv2.getTrackbarPos('highV',name)

    lower_hsv = array([lowH, lowS, lowV])
    higher_hsv = array([highH, highS, highV])

    mask = cv2.inRange(hsv, lower_hsv, higher_hsv)
    frame = cv2.bitwise_and(frame, frame, mask=mask)
    show_immage(name,scaleImage(frame,scale))


    return lower_hsv,higher_hsv

# Equalization
def equalize(image, testing=False):
    img = image.copy()
    # Load the image in greyscale
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # create a CLAHE object (Arguments are optional).
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_out = clahe.apply(img_gray)
    return img_out

def filter_Signals(image):
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
    filtered = cv2.blur(filtered,(2,50))
    ret,filtered = cv2.threshold(filtered,25,255,cv2.THRESH_BINARY)
    return filtered


def filter_Curser(image):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # hsv = cv2.blur(hsv,(2,50))
    filtered = cv2.inRange(hsv, array([0,0,65]), array([255,25, 130]))
    return filtered

# ### filterAltitude
def filterAltidude(image):
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

# ### Filter sun

def filter_sun(image,testing=False):
    frame = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # filter Elite UI orange
    if(testing):
        lower_hsv,higher_hsv = readTrackbars(frame,hsv,'sun',200)
    else:
        lower_hsv,higher_hsv = array([0, 0, 200]), array([179, 240, 255])
    filtered = cv2.inRange(hsv,lower_hsv,higher_hsv)
    return filtered



# ### Filter orange

def filter_orange(image,testing=False):
    frame = image.copy()

    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if(testing):
        lower_hsv,higher_hsv = readTrackbars(frame,hsv,'orange',150)
    else:
        lower_hsv,higher_hsv = getHSVs('orange',frame=frame,hsv=hsv)

    filtered = cv2.inRange(hsv, lower_hsv,higher_hsv)

    return filtered


# ### Filter orange2

def filter_orange2(image):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # filter Elite UI orange
    filtered = cv2.inRange(hsv, array([15, 220, 220]), array([30, 255, 255]))
    return filtered


# ### Filter blue

def filter_blue(image,testing=False):
    frame = image.copy()

    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if(testing):
        lower_hsv,higher_hsv = readTrackbars(frame,hsv,'blue',500)
    else:
        lower_hsv,higher_hsv = getHSVs('blue',frame=frame,hsv=hsv)

    filtered = cv2.inRange(hsv, lower_hsv,higher_hsv)

    show_immage('Navpoint Mask', filtered)

    return filtered



# ### filterHorizon
def filterHorizon(image):
    hsv = image.copy()
    # converting from BGR to HSV color space
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    # hsv = cv2.blur(hsv,(2,50))
    filtered = cv2.inRange(hsv, array([115,223,100]), array([123, 255, 200]))
    return filtered
