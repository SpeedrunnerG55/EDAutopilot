from time import sleep


from consoleOut import consoleHeadder
from readLogs import ship
from emulation import send, keys
from calculations import sun_percent, x_angle
from offsets import get_destination_offset, getEntryOffset,  get_navpoint_offset
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

# ## Autopilot routines

# ### Align

def align():
    print('align')
    if not (ship()['status'] == 'in_supercruise' or ship()['status'] == 'in_space'):
        print('align=err1')
        raise Exception('align error 1')
    print('align= speed 100')
    send(keys['SetSpeed100'])

    print('align= avoid sun')

    sunPercent = sun_percent()

    if (sunPercent > 50):
        position(False)

    if(sunPercent > 5):
        send(keys['PitchUpButton'],state=1)
        while(sunPercent > 5):
            sunPercent = sun_percent()
        send(keys['PitchUpButton'],state=0)

    print('align= find navpoint')

    off = get_navpoint_offset()

    if(not off):
        send(keys['PitchUpButton'],state=1)
        while(not off):
            off = get_navpoint_offset()
        send(keys['PitchUpButton'],state=0)

    print('align= crude align')

    status = ship()['status']

    if(status == 'in_space'):
        closeAngle = 28
        closeX = 4
        closeY = 5
    else:
        closeAngle = 13
        closeX = 3
        closeY = 4

    action = None

    angle = x_angle(off)

    while (abs(off['x']) > closeX and abs(angle) > closeAngle) or (abs(off['y']) > closeY):

        while((abs(off['x']) > closeX) and (abs(angle) > closeAngle)):

            if angle > closeAngle and action is not 'right':
                action = 'right'
                send(keys['RollLeftButton'], state=0)
                send(keys['RollRightButton'], state=1)
            elif angle < -closeAngle and action is not 'left':
                action = 'left'
                send(keys['RollRightButton'], state=0)
                send(keys['RollLeftButton'], state=1)

            off = get_navpoint_offset(last=off,close={'x':closeX, 'y':closeY})
            angle = x_angle(off)

        if(action == 'right' or action == 'left'):
            print("crude x is good")

        if(action == 'right'):
            send(keys['RollRightButton'], state=0)
        elif(action == 'left'):
            send(keys['RollLeftButton'], state=0)
        action = None

        while (abs(off['y']) > closeY):

            if off['y'] > closeY and action is not 'up':
                action = 'up'
                send(keys['PitchDownButton'], state=0)
                send(keys['PitchUpButton'], state=1)
            elif off['y'] < -closeY and action is not 'down':
                action = 'down'
                send(keys['PitchUpButton'], state=0)
                send(keys['PitchDownButton'], state=1)

            off = get_navpoint_offset(last=off,close={'x':closeX, 'y':closeY})

        if(action == 'up' or action == 'down'):
            print("crude y is good")

        if(action == 'up'):
            send(keys['PitchUpButton'], state=0)
        elif(action == 'down'):
            send(keys['PitchDownButton'], state=0)
        action = None

        off = get_navpoint_offset(last=off,close={'x':closeX, 'y':closeY})
        angle = x_angle(off)

    print('align= fine align')
    sleep(0.3)

    if(status == 'in_space'):
        closeX = 50
        closeY = 40
    else:
        closeX = 30
        closeY = 40

    off = get_destination_offset(close={'x':closeX, 'y':closeY})

    if not off:
        return

    while (abs(off['x']) > closeX) or (abs(off['y']) > closeY):
        while (abs(off['x']) > closeX):
            if off['x'] > closeX:
                action = 'right'
                send(keys['YawRightButton'], state=1)
                send(keys['YawLeftButton'], state=0)
            elif off['x'] < -closeX:
                action = 'left'
                send(keys['YawLeftButton'], state=1)
                send(keys['YawRightButton'], state=0)

            off = get_destination_offset(close={'x':closeX, 'y':closeY})

        if(action == 'right' or action == 'left'):
            print("fine x is good")

        if(action == 'right'):
            send(keys['YawRightButton'], state=0)
        elif(action == 'left'):
            send(keys['YawLeftButton'], state=0)
        action = None

        while (abs(off['y']) > closeY):
            if off['y'] > closeY:
                action = 'up'
                send(keys['PitchUpButton'], state=1)
                send(keys['PitchDownButton'], state=0)
            elif off['y'] < -closeY:
                action = 'down'
                send(keys['PitchDownButton'], state=1)
                send(keys['PitchUpButton'], state=0)

            off = get_destination_offset(close={'x':closeX, 'y':closeY})

        if(action == 'up' or action == 'down'):
            print("fine y is good")

        if(action == 'up'):
            send(keys['PitchUpButton'], state=0)
        elif(action == 'down'):
            send(keys['PitchDownButton'], state=0)
        action = None

    print('align=complete')


# ### Position

def position(refuled):
    print('position')
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
    print('position=complete')
    return True

# ### Jump

def jump():
    print('jump')
    tries = 3
    for i in range(tries):
        print('jump= try:'+str(i))
        status = ship()['status']
        if not (status == 'in_supercruise' or status == 'in_space'):
            print('jump=err1')
            raise Exception('not ready to jump')
        sleep(0.3)
        print('jump= start fsd')
        send(keys['HyperSuperCombination'], hold=1)
        send(keys['SetSpeed100'])
        sleep(16)
        if ship()['status'] != 'starting_hyperspace':
            print('jump= misalign stop fsd')
            send(keys['HyperSuperCombination'], hold=1)
            sleep(2)
            align()
        else:
            print('jump= in jump')
            while ship()['status'] != 'in_supercruise':
                sleep(1)
            print('jump= speed 0')
            send(keys['SetSpeedZero'])
            print('jump=complete')
            return True
    print('jump=err2')
    raise Exception("jump failure")

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

# ### Dock

def dock():
    print('dock')
    if ship()['status'] != "in_space":
        print('dock=err1')
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
            print('dock=err2')
            raise Exception("dock error 2")
    send(keys['UI_Back'])
    send(keys['HeadLookReset'])
    send(keys['SetSpeedZero'], repeat=2)
    wait = 120
    for i in range(wait):
        sleep(1)
        if i > wait-1:
            print('dock=err3')
            raise Exception('dock error 3')
        if ship()['status'] == "in_station":
            break
    send(keys['UI_Up'], hold=3)
    send(keys['UI_Down'])
    send(keys['UI_Select'])
    print('dock=complete')
    return True

# ### Undock

def undock():
    print('undock')
    if ship()['status'] != "in_station":
        print('undock=err1')
        raise Exception('undock error 1')
    send(keys['UI_Back'], repeat=10)
    send(keys['HeadLookReset'])
    send(keys['UI_Down'], hold=3)
    send(keys['UI_Select'])
    sleep(1)
    if not (ship()['status'] == "starting_undock" or ship()['status'] == "in_undocking"):
        print('undock=err2')
        raise Exception("undock error 2")
    send(keys['HeadLookReset'])
    send(keys['SetSpeedZero'], repeat=2)
    wait = 120
    for i in range(wait):
        sleep(1)
        if i > wait - 1:
            print('undock=err3')
            raise Exception('undock error 3')
        if ship()['status'] == "in_space":
            break
    print('undock=complete')
    return True



# ### Refuel

def refuel(refuel_threshold=100):
    print('refuel')

    scoopable_stars = ['F', 'O', 'G', 'K', 'B', 'A', 'M']

    shipData = ship() #read once

    status = shipData['status']
    fuelpcnt = shipData['fuel_percent']
    star_class = shipData['star_class']

    if status != 'in_supercruise':
        print('refuel=err1')
        return False
        raise Exception('not ready to refuel')

    if fuelpcnt < refuel_threshold and star_class in scoopable_stars:
        print('refuel= start refuel')
        send(keys['SetSpeed100'])
    #     while not ship()['is_scooping']:
    #         sleep(1)
        sleep(4.4)
        print('refuel= wait for refuel')
        send(keys['SetSpeedZero'], repeat=3)

        fuelpcnt = ship()['fuel_percent']
        while not fuelpcnt > 55: #only place where constant monitoring is needed
            print("fuel level{}".format(fuelpcnt))
            sleep(1)
            fuelpcnt = ship()['fuel_percent']
        print('refuel=complete')
        return True
    elif fuelpcnt >= refuel_threshold:
        print('refuel= not needed')
        return False
    elif star_class not in scoopable_stars:
        print('refuel= needed, unsuitable star')
        return False
    else:
        return False



# ### Discovery scanner

# ### Discovery Scan

def discoveryScan():
    send(keys['PrimaryFire'],hold=5.3)
