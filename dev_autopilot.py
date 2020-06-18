
from functions import align, jump, discoveryScan, refuel, position
from consoleOut import consoleHeadder
from readLogs import ship, printSytemInformation
from immageProcessing import createWindows
from emulation import send, keys

# ## Autopilot main

def autopilot():

    consoleHeadder("AUTOPILOT START")

    shipData = ship()
    status = shipData['status']

    print('shipData='+str(shipData))

    #     if ship()['target']:
    #         undock()

    if status != 'in_space' and status != 'in_supercruise':
        print("not readdy to start currently {}".format(status))
    else:
        createWindows(select=True)
        printSytemInformation();
        while ship()['target']:
            if status == 'in_space' or status == 'in_supercruise':
                consoleHeadder("AUTOPILOT ALIGN");  align();
                consoleHeadder("AUTOPILOT JUMP");   jump();  printSytemInformation();
                consoleHeadder("AUTOPILOT SCAN");   discoveryScan();
                consoleHeadder("AUTOPILOT REFUEL"); refueled = refuel(); #return weather or not a reful occured
                consoleHeadder("AUTOPILOT POSIT");  position(refueled); #pitch up more because you are closer to the star

                status = ship()['status']

        send(keys['SetSpeedZero'])
    consoleHeadder("AUTOPILOT END")
