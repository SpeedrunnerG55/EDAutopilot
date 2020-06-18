import cv2
from numpy import sum
from fileMananager import resource_path
from immageProcessing import get_screen, filter_sun, show_immage, scaleImage
from math import atan,degrees

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
    #     points = getaltLinePoints(mask_Altidude,screen)
    #
    #     screen = cv2.circle(screen,points[0],2,(128,0,0),2)
    #     screen = cv2.circle(screen,points[-1],2,(128,0,0),2)
    #     screen = cv2.line(screen,points[0],points[-1],(128,0,0),2)

    show_immage('screen', screen)
    show_immage('mask_Altidude', mask_Altidude)

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

def getaltLinePoints(image=None,source=None):
    points = getPoints(image)
    points = cleanPoints(points,source)
    return points


def pointOnCircle(x,y,r,angle):
    return(x + int(cos(angle) * r),y - int(sin(angle) * r))

def x_angle(point=None):
    if not point:
        return None
    if(not point['x'] == 0):
        result = degrees(atan(point['y']/point['x']))
        if point['x'] > 0:
            return +90 - result
        else:
            return -90 - result
    else:
        return 0

# ### Get sun

def sun_percent(testing=False):
    left = 0
    top = 0
    right = 1600
    bottom = 700
    screen = get_screen(left,top,right,bottom)
    screen = scaleImage(screen,5) #reduce the resolution, not image data is needed
    filtered = filter_sun(screen,testing=testing)
    white = sum(filtered == 255)
    black = sum(filtered != 255)
    result = white / black
    return result * 100


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
