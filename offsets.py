import cv2
from numpy import array, zeros, uint8

from random import random
from calculations import x_angle

from fileMananager import resource_path
from immageProcessing import get_screen, show_immage, scaleImage, filter_orange, filter_orange2, filter_blue, equalize
from numpy import where

#things that i dont have to do every frame
compass_template = cv2.imread(resource_path("templates/compass.png"), cv2.IMREAD_GRAYSCALE)
compass_width, compass_height = compass_template.shape[::-1]
navpoint_template = cv2.imread(resource_path("templates/navpoint.png"), cv2.IMREAD_GRAYSCALE)
navpoint_width, navpoint_height = navpoint_template.shape[::-1]
destination_template = cv2.imread(resource_path("templates/destination.png"), cv2.IMREAD_GRAYSCALE)
destination_width, destination_height = destination_template.shape[::-1]

# ### getHorizon
def getEntryOffset(img=None):

    mask_horizon = filterHorizon(img)
    x,y,r = findCircle(mask_horizon)

    finalR = r - (r/10)

    finalX,fianlY = pointOnCircle(x,y,r - (r/10),pi/2)

    angle1 = (pi/2) - (pi/100)
    angle2 = (pi/2) + (pi/100)

    height = (int(cos(angle2) * r) - int(cos(angle1) * r)) / 2

    cv2.circle(img,(x,y),r,(0,128,0),2)

    cv2.circle(img,(finalX,fianlY),2,(0,0,255),3)

    cv2.line(img, pointOnCircle(x,y,finalR-height,angle1),pointOnCircle(x,y,finalR+height,angle1), (255, 128, 0), 3)
    cv2.line(img, pointOnCircle(x,y,finalR-height,angle2),pointOnCircle(x,y,finalR+height,angle2), (255, 128, 0), 3)

    cv2.line(img, pointOnCircle(x,y,finalR-height,angle1),pointOnCircle(x,y,finalR-height,angle2), (255, 128, 0), 3)
    cv2.line(img, pointOnCircle(x,y,finalR+height,angle1),pointOnCircle(x,y,finalR+height,angle2), (255, 128, 0), 3)

	# show the output image

    show_immage("output",scaleImage(img,50))
    show_immage("mask_horizon",scaleImage(mask_horizon,50))


# # ### get FSS spectrum offset
#
def getSpectrumOffset(testing=False):

    left = 458
    top = 598
    right = 961
    bottom = 628

    screen = get_screen(left,top,right,bottom)
    height = right - top
    width = right - left

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

    # if testing:
    cv2.line(screen,(pt,0),(pt,height), (0,0,255), 1)
    show_immage('Spectrum', screen)
    show_immage('Spectrum spots', spots)
    show_immage('Spectrum curser', curser)

    return offset
# ### tuneRadio


# ### Get compass image

def get_compass_image(testing=False):

    doubt = 7

    left = 530
    top = 610
    right = 720
    bottom = 800

    screenWidth = right - left

    screen = get_screen(left,top,right,bottom)
    mask_orange = filter_orange(screen,testing=testing)
    # mask_orange = equalize(screen,testing=testing)
    # justCompass = cv2.bitwise_and(screen, screen, mask=mask_orange)

    match = cv2.matchTemplate(mask_orange, compass_template, cv2.TM_CCOEFF_NORMED)
    show_immage('Compass match',match)

    threshold = 0.2
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
    pt = (0, 0)
    if max_val >= threshold:
        pt = max_loc
        compass_image = screen[pt[1]-doubt : pt[1]+compass_height+doubt, pt[0]-doubt : pt[0]+compass_width+doubt].copy()
        if compass_image.size == 0:
            compass_image = cv2.cvtColor(compass_template.copy(),cv2.COLOR_GRAY2BGR)
    else:
        compass_image = cv2.cvtColor(compass_template.copy(),cv2.COLOR_GRAY2BGR)

    # if testing:
    cv2.rectangle(screen, pt, (pt[0] + compass_width, pt[1] + compass_height), (0,0,255), 2)
    # showHSV('justCompass', justCompass)
    show_immage('Compass Found', screen)
    show_immage('Compass Mask', mask_orange)


    return compass_image, compass_width+(2*doubt), compass_height+(2*doubt)

# ### Get navpoint offset

same_last_count = 0
last_last = {'x': 1, 'y': 100}
def get_navpoint_offset(testing=False, close=None, last=None):

    global same_last_count, last_last

    pt = (0, 0)

    compass_image, compass_width, compass_height = get_compass_image(testing=testing)

    centerx = int((1/2)*compass_width)
    centery = int((1/2)*compass_height)

    cv2.circle(compass_image,(centerx,centery),35,(0,0,0),20)

    mask_blue = filter_blue(compass_image,testing=testing)
    # justNavpoint = cv2.bitwise_and(compass_image, compass_image, mask=mask_blue)

    match = cv2.matchTemplate(mask_blue, navpoint_template, cv2.TM_CCOEFF_NORMED)
    show_immage('Navpoint match',match)

    threshold = 0.3
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
    pt = (0, 0)
    if max_val >= threshold:
        pt = max_loc

    final_x = (pt[0] + ((1/2)*navpoint_width)) - ((1/2)*compass_width)
    final_y = ((1/2)*compass_height) - (pt[1] + ((1/2)*navpoint_height))

    endx = int((pt[0] + ((1/2)*navpoint_width)))
    endy = int((pt[1] + ((1/2)*navpoint_height)))

    # if testing:
    cv2.rectangle(compass_image, pt, (pt[0] + navpoint_width, pt[1] + navpoint_height), (0,0,255), 2)
    if(not close == None):
        cv2.rectangle(compass_image, (centerx - close['x'],centery - close['y']),(centerx + close['x'],centery + close['y']), (255,0,0), 2)
    cv2.line(compass_image,(centerx,centery),(endx,endy),(0, 255, 0),2)
    # showHSV('justNavpoint', justNavpoint)
    show_immage('Navpoint Found', compass_image)


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
    return result

# ### Get destination offset

def get_destination_offset(testing=True, close=None):

    pt = (0, 0)

    left = 300
    top = 200
    right = 1300
    bottom = 700

    width = right - left
    height = bottom - top

    centerx = int((1/2)*width)
    centery = int((1/2)*height)

    screen = get_screen(left,top,right,bottom)
    mask_orange = filter_orange2(screen)

    match = cv2.matchTemplate(mask_orange, destination_template, cv2.TM_CCOEFF_NORMED)
    show_immage('Destination match',scaleImage(match,50))

    threshold = 0.2
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
    pt = (0, 0)
    if max_val >= threshold:
        pt = max_loc

    final_x = int((pt[0] + ((1/2)*destination_width)) - ((1/2)*width))
    final_y = int(((1/2)*height) - (pt[1] + ((1/2)*destination_height)))

    endx = int((pt[0] + ((1/2)* destination_width)))
    endy = int((pt[1] + ((1/2)*destination_height)))
    result = {'x':final_x, 'y':final_y}
    # if testing:
    cv2.rectangle(screen, pt, (pt[0] + destination_width, pt[1] + destination_height), (0,0,255), 2)
    if(not close == None):
        cv2.rectangle(screen, (centerx - close['x'],centery - close['y']),(centerx + close['x'],centery + close['y']), (255,0,0), 2)
    cv2.line(screen,(centerx,centery),(endx,endy),(0, 255, 0),2)
    show_immage('Destination Found', scaleImage(screen,50))
    show_immage('Destination Mask', scaleImage(mask_orange,50))
    return result
