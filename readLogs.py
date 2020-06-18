
# ## Read ED logs

# ### Get latest log file
from consoleOut import consoleHeadder
from os.path import join, isfile, getmtime
from sys import platform
from os import environ, listdir
from datetime import datetime
from json import loads

# ## Constants

if platform == "linux" or platform == "linux2":
    path_logs = "/home/" + environ['USER'] + "/.steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous"
elif platform == "darwin":
    path_logs = "mac path i dunno"
elif platform == "win32":
    path_logs = environ['USERPROFILE'] + "\Saved Games\Frontier Developments\Elite Dangerous"

def get_latest_log(path_logs):
    """Returns the full path of the latest (most recent) elite log file (journal) from specified path"""
    list_of_logs = [join(path_logs, f) for f in listdir(path_logs) if isfile(join(path_logs, f)) and f.startswith('Journal.')]
    if not list_of_logs:
        return None
    latest_log = max(list_of_logs, key=getmtime)
    return latest_log

PATH_LOG_FILES = path_logs

print('get_latest_log='+str(get_latest_log(PATH_LOG_FILES)))


# ### System information

def printSytemInformation():

    consoleHeadder("System Information")

    STAR_CLASS = ship()['star_class']
    print("star Class: " + str(STAR_CLASS))

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
                    # ship['status'] = 'starting_undocking'
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
                print("Exception occurred")
                print(e)
    return ship

print("fetching class :p")
STAR_CLASS = ship()['star_class']
