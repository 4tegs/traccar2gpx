# ##########################################################################################
# traccar 2 gpx
# Hans Straßgütl
#
# Fetches Tracks from Traccar 5.4 and builds a valid Garmin GPX track.
# ..........................................................................................
# More information: readme.md
# ##########################################################################################

# ------------------------------------------------------------------------------------------
# Global Imports
# ------------------------------------------------------------------------------------------
import os
import sys
import time
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

from gpx_converter import Converter
from multiprocessing.sharedctypes import Value

from tkinter import *
from tkinter import ttk
from tkinter.messagebox import showinfo

import gpxpy
import gpxpy.gpx

import json

# ...................................................
# lxml is a library for processing XML and HTML in the Python language.
# On windows lxml needs to be installed via "pip install lxml"
# unless doing so, it won't be imported.
# ...................................................
try:
    # Load LXML or fallback to cET or ET
    import lxml.etree as mod_etree  # type: ignore
except:
    try:
        import xml.etree.cElementTree as mod_etree  # type: ignore
    except:
        import xml.etree.ElementTree as mod_etree  # type: ignore


global my_config_file
global config_dic
global clean_Track

# ------------------------------------------------------------------------------------------
# End my Program
# 2022 10 20
# ------------------------------------------------------------------------------------------
def quit_my_program():
    ''' Save current Windows position in Config File. Afterwards quit my program'''
    '''
    Use sys.exit - not quit()!                                              
    Check if menue preselcts exists in Config JSON       
    If not: Create                                       
    '''
    widget_x, widget_y = mainframe.winfo_rootx(), mainframe.winfo_rooty()    
    config_dic.update({"winx" : widget_x}) 
    config_dic.update({"winy" : widget_y}) 
    config_dic.update({"tracker_selected" : choice_tracker.current()}) 
    config_dic.update({"track_color" : color_choice.current()}) 
    config_dic.update({"cleaning_track" : clean_Track.get()}) 
    config_dic.update({"smooth" : smooth_loops_w.current()}) 

    with open(my_config_file, "w") as data:
        json.dump(config_dic, data, indent=4)    

    sys.exit('Tschüss!')

# ------------------------------------------------------------------------------------------
# Errorsections
# 2022 10 20
# ------------------------------------------------------------------------------------------
def error_message(error):
    def exit_now():
        sys.exit('Oh weh - ein Fehler!')

    ''' Error Section. Hand over error-level. Program will be quit. '''
    
    # get the current path of where the program is started
    path = os.getcwd()
    root = Tk()
    root.title("Error!!")
    root.eval('tk::PlaceWindow . center')

    mainframe = ttk.Frame(root, padding="25 25 25 25")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    quitbutton = ttk.Button(mainframe, text='Exit', command=exit_now)
    quitbutton.grid(column=1, row=4, sticky="S")

    if error == 1:
        ttk.Label(mainframe, text="The configuration <traccar2gpx.json> is missing.").grid(column=1, row=1, sticky=W)
        ttk.Label(mainframe, text="A new version has been created here:    " +  path).grid(column=1, row=2, sticky=W)
        ttk.Label(mainframe, text="YOU MUST UPDATE the created version with your credentials before you can carry on!").grid(column=1, row=3, sticky=W)

    if error == 2:
        ttk.Label(mainframe, text="The JSON Inputfile is missing.").grid(
            column=1, row=1, sticky=W)
        ttk.Label(mainframe, text="Choose right filename").grid(
            column=1, row=2, sticky=W)

    if error == 3:
        ttk.Label(mainframe, text="The JSON File has been converted").grid(
            column=1, row=1, sticky=W)
        ttk.Label(mainframe, text="Check your directory").grid(
            column=1, row=2, sticky=W)
    if error == 4:
        ttk.Label(mainframe, text="Missing the TRACAR JSON input File").grid(
            column=1, row=1, sticky=W)
        ttk.Label(mainframe, text="Check if connection to Traccar is working.").grid(
            column=1, row=2, sticky=W)

    if error == 5:
        ttk.Label(mainframe, text="The configuration file is wrong. Check:").grid(
            column=1, row=1, sticky=W)
        ttk.Label(mainframe, text=path + r"\traccar2gpx.json").grid(column=1, row=2, sticky=W)

    if error == 6:
        ttk.Label(mainframe, text="Can't query the devices from Traccar.").grid(
            column=1, row=1, sticky=W)
        ttk.Label(mainframe, text="Make sure you have admin rights and at least one tracker device active.").grid(
            column=1, row=2, sticky=W)
    
    if error == 7:
            ttk.Label(mainframe, text="There are no active Tracker available on Traccar.").grid(
                column=1, row=1, sticky=W)
            ttk.Label(mainframe, text="Make sure you have admin rights and at least one tracker device active.").grid(
                column=1, row=2, sticky=W)

    if error == 8:
            ttk.Label(mainframe, text="Routine has been called without GPX content!").grid(
                column=1, row=1, sticky=W)
            ttk.Label(mainframe, text="This must not have happend. Call the programmer....").grid(
                column=1, row=2, sticky=W)


    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5)

    quitbutton.focus()
    root.bind("<Return>", "sys.exit('Tschüss!')")
    root.protocol("WM_DELETE_WINDOW", "sys.exit('Tschüss!')")
    root.mainloop()

# ------------------------------------------------------------------------------------------
# Convert seconds to a timezone.
#   Example: seconds = 3600 -> return = 02:00
# 2022 10 20
# ------------------------------------------------------------------------------------------
def convert_sec_2_TZ(seconds):
    '''TZ must be provided as seconds. Returns a formated 00:00 '''
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return '%02d:%02d' % (hour, min )

# ------------------------------------------------------------------------------------------
# Delete Files no longer needed. Called by main routine
# 2022 10 20
# ------------------------------------------------------------------------------------------
'''Delete file if it exists'''
def delete_file(a):
    if os.path.exists(a):
        os.remove(a)

# ------------------------------------------------------------------------------------------
# Load Configuration
# 2022 10 20
# ------------------------------------------------------------------------------------------
def load_config(my_config_file):
    ''' If exists: Load JSON Configuration file. -> JSON  '''
    ''' Similar to the load_json but with a different error code in case the file doesn't exist. '''
    try:																                # Lade die Config Datei
        with open(my_config_file) as f:												#
            return json.load(f)															#

    except FileNotFoundError:
        
        config_dic = {
            "root_url": "http://your-url.de:8082",
            "email": "your email",
            "password": "your password"
        }

        with open(my_config_file, "w") as data:
            json.dump(config_dic, data, indent=4)    
        error_message(1)


# ------------------------------------------------------------------------------------------
# Load Json
# ------------------------------------------------------------------------------------------
def load_json(my_config_file):
    ''' If exists: Load JSON file. -> JSON  '''
    try:																                # Lade die Config Datei
        with open(my_config_file) as f:												#
            return json.load(f)															#
    except FileNotFoundError:
        error_message(4)




# ...........................................................................
# Rufe alle Devices ab
# ...........................................................................
# ------------------------------------------------------------------------------------------
# Filter records for enabled devices only
# 2022 10 20
# ------------------------------------------------------------------------------------------
def find_device_enabled(my_json):
    ''' Filter all non active Devices '''
    ''' Used by get_all_devices'''
    if str(my_json["disabled"]) == 'False':
        check = True
    else:
        check = False
    return check

def get_all_devices(traccar_result):
    '''All User available devices will be fetched from Traccar'''
    url = config_dic['root_url'] + '/api/devices'
    headers = {'accept': 'application/json'}
    a = HTTPBasicAuth(config_dic['email'], config_dic['password'])
    payload = {'all': 'True'}
    r = requests.get(url,  params=payload, auth=a, headers=headers)
    # ...........................................................................
    if r.status_code != 200:
        error_message(6)
    else:
        with open(traccar_result, 'wb') as f:												# Schreibe eine binäre Datei
            f.write(r.content)
        # Das was ich von der API bekomme, ist noch kein fertiges JSON. Deshalb schreibe ich das raus
        # und lese es dann JSON mäßig wieder ein. Nun kann ich ordentlich JSON bearbeiten.
        my_json = load_json(traccar_result) 
        # Filter alle nicht aktiven Devices weg 
        my_json = list(filter(find_device_enabled, my_json))
        delete_file(traccar_result)
    return my_json

# ...................................................
# Cleaning the Track
# 2022 10 20
# ...................................................
def gpx_clean_track(gpx):   
    '''
    Reduces the number of points in the track segment & smoothens the elevation graph.

    ### Args: 
    - Input gpx(parsed)

    - Returns: gpx(reworked parsed) - now with less trackpoints 

    ### Methods:
        - reduces by minimum distance = 1m
        - reduces by minimum speed of > 0.5
    '''
    if len(gpx.tracks) > 0:
        for track in gpx.tracks:
            
            for segment in track.segments:
                i = 0
                while i < (segment.get_points_no() -1):         # remove track points with speed < 0.5
                    speed = segment.get_speed(i)
                    if speed < 0.5 :
                        segment.remove_point(i) 
                    else:
                        i = i+1
                segment.reduce_points(1)                        # reduce by minimum distance of 1 Meter
        return gpx

# ...................................................
# Smooth the Track
# 2022 10 20
# ...................................................
def gpx_smooth_track(gpx, smoothen:int):   
    '''
    Smoothens the elevation graph.

    ### Args: 
    - Input gpx(parsed), int: smoothen runs

    - Returns: gpx(reworked parsed) - now with more realistic elevation data

    ### Methods:
        - "Smooths" the elevation graph. Runs multiple times, based on users decision.
    '''
    if len(gpx.tracks) > 0:
        for track in gpx.tracks:  
            for segment in track.segments:
                # Smoothen the track eleveation information. Should change between the trackers used!
                for  i in range(smoothen): segment.smooth(vertical=True, horizontal=False, remove_extremes = False )
        return gpx
    else:
        error_message(8)

# ...................................................
# Attach a name to the track
# 2022 10 20
# ...................................................
def gpx_set_new_trackname(gpx):   
    '''
    Traccar returns the name of the tracker as the tracks name only. Let's give it a more sounding name:
    year-month-day_TrackerName

    ### Args: 
    - Input: gpx(parsed)

    - Returns: 
        1) gpx(reworked parsed) - now with sounding name 
        2) new_name_for_gpx:string (to be used as filename later)

    '''
    if len(gpx.tracks) > 0:
        for track in gpx.tracks:
            format = "%Y-%m-%d_"
            name = datetime.strftime(track.segments[0].points[0].time, format)
            name = name + track.name
            track.name = name
    return gpx, name

# ...................................................
# Write Header that Garmin accepts
# 2022 10 20
# ...................................................
def gpx_set_new_header(gpx):
    '''
    Garmin needs a v1.1 GPX and we add some additional personalisation
    
    ### Args: 
    - Input gpx(parsed)

    - Returns: gpx(reworked parsed) - now with Garmin header
    '''
    namespace = '{gpxx}'                  # definition of extension
    nsmap = {namespace[1:-1]: 'http://www.garmin.com/xmlschemas/GpxExtensions/v3'}
    gpx.nsmap =nsmap
    gpx.creator='https://gravelmaps.de'
    gpx.version = '1.1'
    return gpx

# ...................................................
# Garmin doesn't accept a TZ - but traccar delivers that. 
# What it accepts is a Z for UTC. 
# As Traccar stores everything in UTC, let's 
# change the +02:00 to Z
# 2022 10 20
# ...................................................
def gpx_set_correct_timeformat(gpx):
    '''
    Garmin doesn't accept a TZ - but traccar delivers that. What Garmin accepts is a Z for UTC. 
    As Traccar stores everything in UTC, let's change the +02:00 to Z

    ### Args: 
    - Input gpx(parsed)

    - Returns: gpx(reworked parsed) - now all trackpoints in format as per example: <time>2022-10-17T07:16:59Z</time> 
    '''
    if len(gpx.tracks) > 0:                 # is there anything?
        for track in gpx.tracks:            # Coming from traccar there should be one track in it only, but who knows?
            for segment in track.segments:
                for point in segment.points:
                    pt = str(point.time)
                    pt, weg = pt.split("+", 1)
                    format = "%Y-%m-%d %H:%M:%S"
                    pt1 = datetime.strptime(pt, format)
                    point.time=pt1
        
    return gpx

# ...................................................
# Set Tracks color
# Use the lxml library to handle GPX / XML extensions.
# 2022 10 20
# ...................................................
def gpx_set_color(gpx, track_color ):   
    '''
    Traccar doesn't deliver color as its not defined in standard GPX. Garmin supports that with its own <extension> definition.
    Color is helpful to manage tracks in Mapsource or Basecamp.
    
    ### Args: 
    - Input gpx(parsed), track_color:string

    - Returns: gpx(reworked parsed) - now with color for track

    '''
    gpx.name = 'traccar2gpx_4_garmin'
    gpx.description = 'This track was pulled from Traccar and formated for Garmin Software by https://gravelmaps.de'

    #definition of extension
    namespace = '{gpxx}'

    #create extension element
    root = mod_etree.Element(f'{namespace}TrackExtension')
    # create level 2 SubElement
    rootElement2 = mod_etree.SubElement(root,f'{namespace}DisplayColor')
    rootElement2.text = track_color

    if len(gpx.tracks) > 0:                 # is there anything?
        for track in gpx.tracks:            # Coming from traccar there should be one track in it only, but who knows?
            track.extensions.append(root)
    return gpx


# ###################################################################################################


# ------------------------------------------------------------------------------------------
# Get GPX from Traccar
# 2022 10 20
# ------------------------------------------------------------------------------------------
def get_gpx_data(from_time, to_time, tracker_id, gpx_file_name ): 				# Wird vom Hauptprogramm geladen
    '''Get Route in GPX format from Traccar
        
    ### Args: 
    - Input: from-date-time:datetime, to-date-time:datetime, trackerid:int, gpx_file_name:string

    - Returns: gpx file based on gpx_file_name

    '''
    global config_dic
                                                                                    # global statusNachricht1
                                                                                    # Hänge noch die benötigten Aufrufparameter an
    url = config_dic['root_url'] + '/api/positions/gpx' 
                                                                                    # Wenn du die Daten per http://syno.motorradtouren.de:8082 abholen willst,
                                                                                    # vergesse nicht, die 8082 zur Syno weiter zu leiten!
                                                                                    # Machen den Auth Aufruf vie die HTTPBasicAuth
    my_auth = HTTPBasicAuth(config_dic['email'], config_dic['password'])
    payload = {																		# Stelle die weiteren Parameter zusammen um die Daten von Traccar zu bekommen
                                                                                    # Welche Device? Es darf nur eine angegeben werden!
        'deviceId': [tracker_id],                                                   #
        'from': from_time,															#
        'to': to_time																#
    }																			    #
    headers = {'accept': 'application/gpx+xml'}
    data_from_traccar = requests.get(url,  params=payload, auth=my_auth,headers=headers)	# Hole die Datensätze
    if data_from_traccar.status_code != 200:										# Wenn alles ok, dann gibt get 200 zurück.
        error_message(9)

    with open(gpx_file_name, 'wb') as f:											# Schreibe eine Datei
        f.write(data_from_traccar.content)                                          # r wurde mit requests gefüllt. Schreibe nun den content von r raus
                                                                                    # die File ist nun ein einziger langer String im GPX / XML Format

    

# ------------------------------------------------------------------------------------------
# Hauptprogram
# ------------------------------------------------------------------------------------------
if __name__ == "__main__":
    ''' Hier startet das Program '''
    # global my_xml_filename
    # global statusNachricht

    def get_from_traccar():
        '''Get Tracks from Traccar'''
        daysback = int(tage_choice.get())
        tracker_name = str(choice_tracker.get())
        tracker_id = my_tracker_id[my_tracker_names.index(choice_tracker.get())]
        track_cleaning = clean_Track.get()
        trackcolor = color_choice.get()
        # Der Traccar server speichert alles in UTC. 
        # Wir benötigen daher für die richtige Abfrage die eigene TZ
        # Dann verändert sich der TZ Offseet je nachdem, ob wir in Daylight Saving sind oder nicht.
        # Die Zahlen benötigst du zweimal: 
        #   1 Für die Abfrage beim Traccar Server
        #   2 Wenn du den Namen des Tracks baust
        local_tz_offset = (-time.timezone)                                              # TZ of wich this computer is in. Returns seconds
        TZ_Offset = '00:00'
        if time.daylight > 0: 
            local_tz_offset= local_tz_offset+3600
        if local_tz_offset != 0:
            TZ_Offset = convert_sec_2_TZ(local_tz_offset) 

        for i in range(daysback):														# eine for 0 to Anzahl Tage daysback loop
            from1 = i*-1
            to1 = i*-1																	# Ebenfalls eine MinusZahl
            from_time = datetime.now() + timedelta(days=from1)
            to_time = datetime.now() + timedelta(days=to1)
            # The to_time is in date format. To further work on it, make it a string
            from_time = str(from_time)
            # remove the time from the string and add an new time including a TZ offset
            from_time = from_time[:10] + 'T00:00:01.0000+' + str(TZ_Offset)
            to_time = str(to_time)
            to_time = to_time[:10] + 'T23:59:59.0000+' +  str(TZ_Offset)
            
            get_gpx_data(from_time, to_time, tracker_id, gpx_file_name)
            
            # ...........................................
            # Make all necessary changes to the GPX track
            # ...........................................
            # first load it
            # ...........................................
            gpx_file = open(gpx_file_name, 'r')     # Lese die GPX File ein als das was sie ist: Text
            gpx = gpxpy.parse(gpx_file)             # Jetzt mache ein GPX/XML aus dem Text

            if gpx.get_track_points_no() > 0:
                if track_cleaning: gpx = gpx_clean_track(gpx)
                if smooth_loops > 0: gpx = gpx_smooth_track(gpx, smooth_loops)
                gpx, new_gpx_fileName = gpx_set_new_trackname(gpx)
                gpx = gpx_set_new_header(gpx)
                gpx = gpx_set_correct_timeformat(gpx)
                gpx = gpx_set_color(gpx, trackcolor)  
                # ...........................................
                # Finally write GPX to disc
                # ...........................................
                new_gpx_fileName = new_gpx_fileName + ".gpx"
                with open(new_gpx_fileName, 'w') as f:     
                    f.write(gpx.to_xml())  

            gpx_file.close()     # Lese die GPX File ein als das was sie ist: Text
            delete_file(gpx_file_name)
            

            
            style = ttk.Style()
            style.configure("Green.TLabel", foreground="green")
            ttk.Label(mainframe, text="Done!", style="Green.TLabel").grid(column=1, row=6, sticky="W")
    
    # ....................................................
    # Setzte deine Variablen
    # ....................................................
    traccar_result = "traccar-result.json"      # needed to analyze the various devices applied to the user
    my_config_file = 'traccar2gpx.json'         # the configuration file name
    gpx_file_name  = "traccar-get.gpx"         # interim gpx file name

    # ....................................................
    # Read config File
    # ....................................................
    config_dic = load_config(my_config_file) 

    # check if config file has been edited with sense
    if config_dic['email'] == "your email" or config_dic['root_url'] == "http://your-url.de:8082" or config_dic['password'] == "your password":
        error_message(5)
    # ................
    # Check if window x position key exists in Config JSON    
    # If not: Create                                      
    x = config_dic.get("winx")
    if not x: config_dic.update({"winx" : 10})                                   # Init die Variable in der Config File
    winx = config_dic.get("winx")
    # ................
    # Check if window y position key exists in Config JSON    
    # If not: Create                                       
    x = config_dic.get("winy")
    if not x: config_dic.update({"winy" : 10})                                   # Init die Variable in der Config File
    winy = config_dic.get("winy")
    # ................
    # Check for last setting of tracker
    x = config_dic.get("tracker_selected")
    if not x: config_dic.update({"tracker_selected" : 0})                        # Init die Variable in der Config File
    tracker_selected  = config_dic.get("tracker_selected")
    # ................
    # Check for last setting of color
    x = config_dic.get("track_color")
    if not x: config_dic.update({"track_color" : 0})                             # Init die Variable in der Config File
    track_color_set  = config_dic.get("track_color")
    # ................
    # Check for last Status of Cleaning Track
    x = config_dic.get("cleaning_track")
    if not x: config_dic.update({"cleaning_track" : False})                                   # Init die Variable in der Config File
    # ................
    # Check for last Status of Smoothening Elevation data
    x = config_dic.get("smooth")
    if not x: config_dic.update({"smooth" : 0})                                   # Init die Variable in der Config File
    smooth_loops = config_dic.get("smooth")

    # ....................................................
    # Baue das Menü auf
    # ....................................................
    root = Tk()
    '''Setting the x and y position from where the menue should pop up'''
    root.geometry('+{}+{}'.format(winx,winy))  
    root.title("Traccar2GPX - v1.2 (use with Traccar 5.4)")
    mainframe = ttk.Frame(root, borderwidth=5, relief="ridge", padding="5 5 5 5")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # ....................................................
    # Lese von Traccar die Anzahl Devices, deren Namen und ID's
    # ....................................................
    if config_dic['email']:
        # Hole alle devices in ein Tuple
        my_devices = get_all_devices(traccar_result)
    else:
        error_message(5)
    my_tracker_amount = 0
    my_tracker_names = []
    my_tracker_id = []
    for i in my_devices:
        my_tracker_names.append(i['name'])
        my_tracker_id.append(i['id'])
    my_tracker_amount = len(my_tracker_names)
    if my_tracker_amount == 0:
        error_message(7)

    # ....................................................
    # Setzte das Auswahlmenü für die Anzahl der Tage zurück
    # ....................................................
    TageZurueck = []
    for x in range(1, 91):
        TageZurueck.append(x)
    ttk.Label(mainframe, text="Amount of days back:").grid(
        column=1, row=1, sticky=E)
    tage_choice = ttk.Combobox(mainframe)
    tage_choice['values'] = TageZurueck
    tage_choice.current(0)
    tage_choice.grid(column=2, row=1, sticky="W")
    tage_choice.state(['readonly'])

    # ....................................................
    # Setzte das Auswahlmenü für den Tracker
    # ....................................................
    ttk.Label(mainframe, text="Tracker:").grid(column=1, row=2, sticky="E")
    choice_tracker = ttk.Combobox(mainframe)
    choice_tracker['values'] = my_tracker_names
    choice_tracker.current(tracker_selected)                    # tracker_selected Wurde weiter oben in der Initialisierungsektion der Config Presets gesetzt
    choice_tracker.grid(column=2, row=2, sticky=EW)
    choice_tracker.state(["readonly"])

    # ....................................................
    # Setzte das Auswahlmenü für die Farben des Tracks
    # ....................................................
    TrackColor = (
        'Magenta',
        'Cyan',
        'Green',
        'Red',
        'Blue',
        'Yellow',
        'LightGrey',
        'DarkMagenta',
        'DarkCyan',
        'DarkGreen',
        'DarkRed',
        'DarkBlue',
        'DarkYellow',
        'DarkGrey',
        'Black'
    )
    ttk.Label(mainframe, text="Color of GPX Track:").grid(
        column=1, row=3, sticky=E)
    color_choice = ttk.Combobox(mainframe)
    color_choice['values'] = TrackColor
    color_choice.current(track_color_set)                   # track_color Wurde weiter oben in der Initialisierungsektion der Config Presets gesetzt
    color_choice.grid(column=2, row=3, sticky="W")
    color_choice.state(['readonly'])

    # ....................................................
    # Setzte das Auswahlmenü für Cleaning Track
    # ....................................................
    ttk.Label(mainframe, text="Clean Track:").grid(column=1, row=4, sticky=E)
    clean_Track = BooleanVar(value=True)                                    # Zwingend die init einer TkInter BooleanVar machen!
    clean_Track.set(config_dic.get("cleaning_track"))                       # Die BoolenVar wird mit set und get behandelt.
    check_clean_Track = ttk.Checkbutton(mainframe,  variable=clean_Track)
    check_clean_Track.grid(column=2, row=4, sticky="W")

    # ....................................................
    # Setzte das Auswahlmenü für Smoothening der Elevation
    # ....................................................
    smoothRange = []
    for x in range(0, 31): smoothRange.append(x)
    ttk.Label(mainframe, text="Smooth Elevation data:").grid(column=1, row=5, sticky=E)
    smooth_loops_w = ttk.Combobox(mainframe)
    smooth_loops_w['values'] = smoothRange
    smooth_loops_w.current(smooth_loops)
    smooth_loops_w.grid(column=2, row=5, sticky="W")
    smooth_loops_w.state(['readonly'])
    # smooth_loops.state(['disabled'])

    # ....................................................
    # Setze die "Arbeitsknöpfe"
    # ....................................................
    work_button = ttk.Button(mainframe, text='Get GPX Track', command=get_from_traccar)
    work_button.grid(column=2, row=6, sticky="EW")
    work_button.focus()

    quitbutton = ttk.Button(mainframe, text='Exit', command=quit_my_program)
    quitbutton.grid(column=3, row=6, sticky="E")

    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5) 

    root.update()
    
    root.protocol("WM_DELETE_WINDOW", quit_my_program)
    root.mainloop()

