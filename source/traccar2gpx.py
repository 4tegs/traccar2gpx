# ##########################################################################################
# traccar 2 gpx
# Hans Straßgütl
#
# Fetches Tracks from Traccar 5.4 and builds a valid Garmin GPX track.
# ..........................................................................................
# More information: readme.md
# 
# Changes:
#   2022 10 23      Took back "Smoothen the track" as the difference was close to null.
#   2022 12 04      Upgraded to Python 3.10
#                   Selection for 366 days instead of 90 only 
#   2023 03 27      Upgraded to Python 3.11
#                   Updated to Selection of Dates instead of days backward.
#                   Added option to pull either a single track or one track per day of selected range.
#   2023 04 13      Remebers last Start Date set via JSON
#   2023 04 16      Now having the choice to selec either a single tracker or all tracker at once
# 
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

from babel import Locale
from babel import numbers

# from gpx_converter import Converter

import tkinter as tk
from tkinter import *
from tkinter import ttk
# from tkinter.messagebox import showinfo
from ttkthemes import ThemedTk
# from ttkthemes import *

import tkinter.messagebox as msgbox
from datetime import datetime, timedelta
from tkcalendar import Calendar


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
    Check if menue preselects exists in Config JSON       
    If not: Create                                       
    '''
    # start_d = datetime.strptime(start_datum.get(), "%Y-%m-%d")
    # end_d = datetime.strptime(end_datum.get(), "%Y-%m-%d")
    # days = (end_d - start_d).days +1
    widget_x, widget_y = mainframe.winfo_rootx(), mainframe.winfo_rooty()    
    config_dic.update({"winx" : widget_x}) 
    config_dic.update({"winx" : widget_x}) 
    config_dic.update({"winy" : widget_y}) 
    config_dic.update({"tracker_selected" : choice_tracker.current()}) 
    config_dic.update({"track_color" : color_choice.current()}) 
    config_dic.update({"cleaning_track" : clean_Track.get()}) 
    config_dic.update({"statistics" : statistics.get()}) 
    config_dic.update({"all_tracker" : all_Tracker.get()}) 
    config_dic.update({"start_date" : start_datum.get()}) 
    # start_d = datetime.strptime(start_datum.get(), "%Y-%m-%d")
    # config_dic.update({"days_back" : (int(tage_choice.get())-1) })
    # config_dic.update({"smooth" : smooth_loops_w.current()}) 

    with open(my_config_file, "w", encoding='utf-8') as data:
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
        ttk.Label(mainframe, text="Missing the TRACAR JSON input File").grid(
            column=1, row=1, sticky=W)
        ttk.Label(mainframe, text="Check if connection to Traccar is working.").grid(
            column=1, row=2, sticky=W)

    if error == 3:
        ttk.Label(mainframe, text="The configuration file is wrong. Check:").grid(
            column=1, row=1, sticky=W)
        ttk.Label(mainframe, text=path + r"\traccar2gpx.json").grid(column=1, row=2, sticky=W)

    if error == 4:
        ttk.Label(mainframe, text="Can't query the devices from Traccar.").grid(
            column=1, row=1, sticky=W)
        ttk.Label(mainframe, text="Make sure you entered the right user credentials.").grid(
            column=1, row=2, sticky=W)        
        ttk.Label(mainframe, text="Make sure the user has admin rights and at least one tracker device applied.").grid(
            column=1, row=3, sticky=W)        
    
    if error == 5:
            ttk.Label(mainframe, text="There are no active Tracker available on Traccar.").grid(
                column=1, row=1, sticky=W)
            ttk.Label(mainframe, text="Make sure you have admin rights and at least one tracker device active.").grid(
                column=1, row=2, sticky=W)

    if error == 6:
            ttk.Label(mainframe, text="Routine has been called without GPX content!").grid(
                column=1, row=1, sticky=W)
            ttk.Label(mainframe, text="This must not have happend. Call the programmer....").grid(
                column=1, row=2, sticky=W)
            
    if error == 7:
            ttk.Label(mainframe, text="Your root URL seems to be wrong.").grid(
                column=1, row=1, sticky=W)
            ttk.Label(mainframe, text="Is it missing a http?").grid(
                column=1, row=2, sticky=W)
            
    if error == 8:
            ttk.Label(mainframe, text="Your root URL seems to be wrong.").grid(
                column=1, row=1, sticky=W)
            ttk.Label(mainframe, text="Are you sure that your root_url points to the right server?").grid(
                column=1, row=2, sticky=W)


    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5)

    quitbutton.focus()
    root.bind("<Return>", "sys.exit('Tschüss!')")
    root.protocol("WM_DELETE_WINDOW", "sys.exit('Tschüss!')")
    root.mainloop()

# ------------------------------------------------------------------------------------------
# get some statistics around the track
# 2022 10 21
# ------------------------------------------------------------------------------------------
def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

def statistics_init():
    '''Initialize a dictionary with the values for the statistics 
    
    Returns the dictionary.
    '''   
    statistic_dict = {
        'Points in track' : ['Points in Track'.ljust(19)+": "], 
        'Length 2D' : ['Length 2D'.ljust(19)+": "],
        'Length 3D' : ['Length 3D'.ljust(19)+": "],
        # "Unterwegs" : ['Duration'.ljust(19)+": "],
        # "Moving time" : ['Moving time'.ljust(19)+": "],
        # "Stopped time" : ['Stopped time'.ljust(19)+": "],
        # "Moving distance" : ['Moving Distance'.ljust(19)+": "],
        # "Stopped distance" : ['Stopped Distance'.ljust(19)+": "],
        "Max speed" : ['Max Speed'.ljust(19)+": "],
        "Elevation min" : ['Elevation min'.ljust(19)+": "],
        "Elevation max" : ['Elevation max'.ljust(19)+": "],
        "Uphill" : ['Uphill'.ljust(19)+": "],
        "Downhill" : ['Downhill'.ljust(19)+": "]
    }
    return statistic_dict


def gpx_statistics(gpx, statistic_dict): 
    '''Fill statistics dictionary. Append an entry to each list item.
    
    Returns the dictionary.
    '''
    if len(gpx.tracks) > 0:
        for track in gpx.tracks:
            for segment in track.segments:
                uphill, downhill = segment.get_uphill_downhill()
                unterwegs = gpx.get_duration() # floating 
                hoch_min, hoch_max = gpx.get_elevation_extremes()
                moving_time, stopped_time, moving_distance, stopped_distance, max_speed = gpx.get_moving_data()
                cc = statistic_dict["Points in track"]  ; cd = str(segment.get_points_no()).rjust(12)               ; cc.append(cd) ; statistic_dict['Points in track'] = cc
                cc = statistic_dict["Length 2D"]        ; cd = str(int(segment.length_2d())).rjust(10) + ' m'       ; cc.append(cd) ; statistic_dict['Length 2D'] = cc
                cc = statistic_dict["Length 3D"]        ; cd = str(int(segment.length_3d())).rjust(10) + ' m'       ; cc.append(cd) ; statistic_dict['Length 3D'] = cc
                # cc = statistic_dict["Unterwegs"]        ; cd = str(convert(unterwegs)).rjust(12)                     ; cc.append(cd) ; statistic_dict['Unterwegs'] = cc
                # cc = statistic_dict["Moving time"]      ; cd = str(convert(moving_time)).rjust(12)                   ; cc.append(cd) ; statistic_dict['Moving time'] = cc
                # cc = statistic_dict["Stopped time"]     ; cd = str(convert(stopped_time)).rjust(12)                  ; cc.append(cd) ; statistic_dict['Stopped time'] = cc
                # cc = statistic_dict["Moving distance"]  ; cd = str(round(moving_distance/1000 ,2)).rjust(9)+' Km'   ; cc.append(cd) ; statistic_dict['Moving distance'] = cc
                # cc = statistic_dict["Stopped distance"] ; cd = str(round(stopped_distance/1000 ,2)).rjust(9)+' Km'  ; cc.append(cd) ; statistic_dict['Stopped distance'] = cc
                cc = statistic_dict["Max speed"]        ; cd = str(round((max_speed/1000*3600),2)).rjust(8)+' Km/h' ; cc.append(cd) ; statistic_dict['Max speed'] = cc
                cc = statistic_dict["Elevation min"]    ; cd = str(int(hoch_min)).rjust(10) + ' m'                   ; cc.append(cd) ; statistic_dict['Elevation min'] = cc
                cc = statistic_dict["Elevation max"]    ; cd = str(int(hoch_max)).rjust(10) + ' m'                   ; cc.append(cd) ; statistic_dict['Elevation max'] = cc
                cc = statistic_dict["Uphill"]           ; cd = str(int(uphill)).rjust(10) + ' m'                     ; cc.append(cd) ; statistic_dict['Uphill'] = cc
                cc = statistic_dict["Downhill"]         ; cd = str(int(downhill)).rjust(10) + ' m'                   ; cc.append(cd) ; statistic_dict['Downhill'] = cc
    return statistic_dict

def gpx_statistics_print(statistic_dict, lines):
    '''
    Loops through dictionary and prepares readable statistics, line by line, for later write to file
    
    * Input: dictionary, lines (list of lines)
    * Return: lines

    '''
    line = "-".ljust(21) +  'Raw GPX'.rjust(12) +  'Reworked'.rjust(12) +'\n'
    lines.append(line)

    for x in statistic_dict:
        line = ''
        for y in statistic_dict[x]: 
            line = line + y
        line = line + "\n"
        lines.append(line)
    
    return lines


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
        with open(my_config_file, encoding='utf-8') as f:												#
            return json.load(f)															#

    except FileNotFoundError:
        
        config_dic = {
            "root_url": "http://your-url.de:8082",
            "email": "your email",
            "password": "your password"
        }

        with open(my_config_file, "w", encoding='utf-8') as data:
            json.dump(config_dic, data, indent=4)    
        error_message(1)


# ------------------------------------------------------------------------------------------
# Load Json
# ------------------------------------------------------------------------------------------
def load_json(my_config_file):
    ''' If exists: Load JSON file. -> JSON  '''
    try:																                # Lade die Config Datei
        with open(my_config_file, encoding='utf-8') as f:												#
            return json.load(f)															#
    except FileNotFoundError:
        error_message(2)

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
    try: 
        r = requests.get(url,  params=payload, auth=a, headers=headers)
    except requests.exceptions.InvalidSchema:
        # You may need to enter a http:// before your URL
        error_message(7)
    except requests.exceptions.ConnectionError:
        # URL is wrong. Program can't connect to server.
        error_message(8)
    # ...........................................................................
    if r.status_code != 200:
        # Alle anderen Fehler die nicht zum crash des Programs führen
        error_message(4)
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
    Reduces the number of points in the track segment.

    ### Args: 
    - Input gpx(parsed)

    - Returns: gpx(reworked parsed) - now with less trackpoints 

    ### Methods:
        - reduces by minimum distance = 1m
        - reduces by minimum speed of < 0.5
        - reduces by max speed of > 250km/h
        - reduces if similar latitude and longitude as next point in track
    '''
    if len(gpx.tracks) > 0:
        for track in gpx.tracks:           
            for segment in track.segments:
                i = 0
                kill = False
                while i < (segment.get_points_no() -2):         # remove track points with speed < 0.5
                    # print(segment)
                    lat1 = segment.points[i].latitude
                    lon1 = segment.points[i].longitude
                    lat2 = segment.points[i+1].latitude
                    lon2 = segment.points[i+1].longitude
                    if (lat1 == lat2) & (lon1 == lon2): kill = True
                    speed = segment.get_speed(i)    
                    if speed == None: 
                        kill = True
                        speed = 0
                    if (speed < 0.5) | (speed > 250) : kill = True
                    if kill == True: 
                        segment.remove_point(i) 
                        kill = False
                    else:
                        i = i+1
                segment.reduce_points(1)                        # reduce by minimum distance of 1 Meter
        return gpx

# ...................................................
# Attach a name to the track
# 2022 10 20
# ...................................................
def gpx_set_new_trackname(gpxdate, gpx):   
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
            # name = datetime.strftime(track.segments[0].points[0].time, format)
            name = gpxdate + "_"+ track.name
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



    def select_start_date():
        '''Get Start Date from Menue'''
        end_date = end_datum.get()
        start_date = start_datum.get()
        date = datetime.strptime(start_date,"%Y-%m-%d")

        # Make Menue
        root = Tk()
        root.title("Set Start Date")
        root.eval('tk::PlaceWindow . center')
        top = ttk.Frame(root, padding="25 25 25 25")
        top.grid(column=0, row=0, sticky=(N, W, E, S))
        root.geometry('+{}+{}'.format(winx,winy))  
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        cal = Calendar(top, selectmode="day", year=date.year, month=date.month, day=date.day)
        cal.grid(column=1, row=2, sticky="S")
        
        def set_date():
            start_date = cal.selection_get().strftime("%Y-%m-%d")
            jetzt = datetime.now().strftime("%Y-%m-%d")
            if start_date > end_date:
                start_date = end_date
            if start_date > jetzt:
                start_date = jetzt
            start_datum.set(start_date)
            # start_d = datetime.strptime(start_datum.get(), "%Y-%m-%d")
            # end_d = datetime.strptime(end_datum.get(), "%Y-%m-%d")
            # days = (end_d - start_d).days +1
            # style = ttk.Style()
            # style.configure("Red.TLabel", foreground="red")
            # ttk.Label(mainframe, text="Fetching "+str(days).rjust(5)+" days", style="Red.TLabel").grid(column=1, row=8, sticky="W")
            root.destroy()

        # Add buttons to set the start and end dates
        button = ttk.Button(top, text="Set Start Date", command=set_date)
        button.grid(column=1, row=4, sticky="S")

    def select_end_date():
        '''Get End Date from Menue'''
        start_date = start_datum.get()
        end_date = end_datum.get()
        date = datetime.strptime(end_date,"%Y-%m-%d")
        
        # Make Menue
        root = Tk()
        root.title("Set End Date")
        root.eval('tk::PlaceWindow . center')
        top = ttk.Frame(root, padding="25 25 25 25")
        top.grid(column=0, row=0, sticky=(N, W, E, S))
        root.geometry('+{}+{}'.format(winx,winy))  
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        cal = Calendar(top, selectmode="day", year=date.year, month=date.month, day=date.day)
        cal.grid(column=1, row=2, sticky="S")
        
        def set_date():
            end_date = cal.selection_get().strftime("%Y-%m-%d")
            jetzt = datetime.now().strftime("%Y-%m-%d")
            if end_date < start_date:
                end_date = start_date
            if end_date > jetzt:
                end_date = jetzt
            end_datum.set(end_date)

            # start_d = datetime.strptime(start_datum.get(), "%Y-%m-%d")
            # end_d = datetime.strptime(end_datum.get(), "%Y-%m-%d")
            # days = (end_d - start_d).days +1
            # style = ttk.Style()
            # style.configure("Red.TLabel", foreground="red")
            # ttk.Label(mainframe, text="Fetching "+str(days).rjust(5)+" days", style="Red.TLabel").grid(column=1, row=8, sticky="W")
            root.destroy()
            
        # Add buttons to set the start and end dates
        button = ttk.Button(top, text="Set End Date", command=set_date)
        button.grid(column=1, row=4, sticky="S")


    def select_today_date():
        start_datum.set(datetime.now().strftime("%Y-%m-%d"))
        start_entry = ttk.Entry(mainframe, textvariable=start_datum, state="readonly")
        start_entry.grid(column=2,columnspan=3,  row=1, sticky=W)
        end_datum.set(datetime.now().strftime("%Y-%m-%d"))
        end_entry = ttk.Entry(mainframe, textvariable=end_datum, state="readonly")
        end_entry.grid(column=2,columnspan=3,  row=2, sticky=W)

      

    def get_one_traccar():
        '''Get One huge track from Traccar'''
        def get_my_track():
            ''' Subroutine is used in two ways: When looping through all tracker or when working on a single tracker only.'''
            lines = []
            track_cleaning = clean_Track.get()
            trackcolor = color_choice.get()
            get_gpx_data(from_time, to_time, tracker_id, gpx_file_name)
            
            # ...........................................
            # Make all necessary changes to the GPX track
            # ...........................................
            # first load it
            # ...........................................
            gpx_file = open(gpx_file_name, 'r', encoding='utf-8')     # Lese die GPX File ein als das was sie ist: Text
            gpx = gpxpy.parse(gpx_file)             # Jetzt mache ein GPX/XML aus dem Text
            if gpx.get_track_points_no() > 0:
                statistic_dict = statistics_init()
                statistic_dict = gpx_statistics(gpx, statistic_dict)
                
                if track_cleaning: gpx = gpx_clean_track(gpx)
                gpxdate = from_time[:10] + "-" + to_time[:10]
                gpx, new_gpx_fileName = gpx_set_new_trackname(gpxdate, gpx)
                gpx = gpx_set_new_header(gpx)
                gpx = gpx_set_correct_timeformat(gpx)
                gpx = gpx_set_color(gpx, trackcolor) 

                statistic_dict = gpx_statistics(gpx, statistic_dict)
                lines = gpx_statistics_print(statistic_dict, lines)
                # ...........................................
                # Finally write GPX to disc
                # ...........................................
                new_gpx_fileName1 = new_gpx_fileName + ".gpx"
                with open(new_gpx_fileName1, 'w', encoding='utf-8') as f:     
                    f.write(gpx.to_xml())  
                f.close()
        
                if statistics.get():
                    new_gpx_fileName1 = new_gpx_fileName + ".txt"
                    with open(new_gpx_fileName1, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    f.close()
                
            gpx_file.close()     
            delete_file(gpx_file_name)
    
        style = ttk.Style()
        style.configure("Red.TLabel", foreground="red")
        ttk.Label(mainframe, text="Running!", style="Red.TLabel").grid(column=1, row=8, sticky="W")
        root.update()
        
        start_d = datetime.strptime(start_datum.get(), "%Y-%m-%d")
        end_d = datetime.strptime(end_datum.get(), "%Y-%m-%d")

        # Der Traccar server speichert alles in UTC. 
        # Wir benötigen daher für die richtige Abfrage die eigene TZ
        # Dann verändert sich der TZ Offseet je nachdem, ob wir in Daylight Saving sind oder nicht.
        # Die Zahlen benötigst du Für die Abfrage beim Traccar Server
        local_tz_offset = (-time.timezone)                                              # TZ of wich this computer is in. Returns seconds
        TZ_Offset = '00:00'
        if time.daylight > 0: 
            local_tz_offset= local_tz_offset+3600
        if local_tz_offset != 0:
            TZ_Offset = convert_sec_2_TZ(local_tz_offset) 
        
        # The to_time is in date format. To further work on it, make it a string
        from_time = str(start_d)
        # remove the time from the string and add an new time including a TZ offset
        from_time = from_time[:10] + 'T00:00:01.0000+' + str(TZ_Offset)
        to_time = str(end_d)
        to_time = to_time[:10] + 'T23:59:59.0000+' +  str(TZ_Offset)

        # Jetzt frage ich ab, ob nur der eine Tracker abgefragt wird oder alle
        if all_Tracker.get():
            i = 0
            tracker_loops = my_tracker_amount
            for i in range(tracker_loops):
                tracker_id = my_tracker_id[i]
                get_my_track()
        else:
            tracker_id = my_tracker_id[my_tracker_names.index(choice_tracker.get())]
            get_my_track()
        
        style = ttk.Style()
        style.configure("Green.TLabel", foreground="green")
        ttk.Label(mainframe, text="Done!    ", style="Green.TLabel").grid(column=1, row=8, sticky="W")



    # ...........................................
    # Get the tracks per day 
    # ...........................................
    def get_daily_traccar():
        '''Get Daily Tracks from Traccar'''
        def get_my_track():                 
            ''' Subroutine is used in two ways: When looping through all tracker or when working on a single tracker only.'''
            start_d = datetime.strptime(start_datum.get(), "%Y-%m-%d")
            end_d = datetime.strptime(end_datum.get(), "%Y-%m-%d")
            days = (end_d - start_d).days +1
            jetzt = datetime.now().strftime("%Y-%m-%d")
            track_cleaning = clean_Track.get()
            trackcolor = color_choice.get()
            # Der Traccar server speichert alles in UTC. 
            # Wir benötigen daher für die richtige Abfrage die eigene TZ
            # Dann verändert sich der TZ Offseet je nachdem, ob wir in Daylight Saving sind oder nicht.
            # Die Zahlen benötigst du zweimal: 
            #   1 Für die Abfrage beim Traccar Server
            local_tz_offset = (-time.timezone)                                              # TZ of wich this computer is in. Returns seconds
            TZ_Offset = '00:00'
            if time.daylight > 0: 
                local_tz_offset= local_tz_offset+3600
            if local_tz_offset != 0:
                TZ_Offset = convert_sec_2_TZ(local_tz_offset) 
            
            start_d += timedelta(days=-1)
            from_date = start_d
            for i in range(days):														# eine for 0 to Anzahl Tage daysback loop
                lines = []
                from_date += timedelta(days=1)
                # The to_time is in date format. To further work on it, make it a string
                from_time = str(from_date)
                # remove the time from the string and add an new time including a TZ offset
                from_time = from_time[:10] + 'T00:00:01.0000+' + str(TZ_Offset)
                to_time = str(from_date)
                to_time = to_time[:10] + 'T23:59:59.0000+' +  str(TZ_Offset)
                get_gpx_data(from_time, to_time, tracker_id, gpx_file_name)
                
                # ...........................................
                # Make all necessary changes to the GPX track
                # ...........................................
                # first load it
                # ...........................................
                gpx_file = open(gpx_file_name, 'r', encoding='utf-8')     # Lese die GPX File ein als das was sie ist: Text
                gpx = gpxpy.parse(gpx_file)             # Jetzt mache ein GPX/XML aus dem Text
                if gpx.get_track_points_no() > 0:
                    # lines = gpx_statistics(gpx, lines)
                    statistic_dict = statistics_init()
                    statistic_dict = gpx_statistics(gpx, statistic_dict)
                    
                    if track_cleaning: gpx = gpx_clean_track(gpx)
                    # if smooth_loops > 0: gpx = gpx_smooth_track(gpx, smooth_loops)
                    # gpx, new_gpx_fileName = gpx_set_new_trackname(gpx)
                    gpxdate = from_time[:10]
                    gpx, new_gpx_fileName = gpx_set_new_trackname(gpxdate, gpx)
                    gpx = gpx_set_new_header(gpx)
                    gpx = gpx_set_correct_timeformat(gpx)
                    gpx = gpx_set_color(gpx, trackcolor) 

                    # lines = gpx_statistics(gpx, lines) 
                    statistic_dict = gpx_statistics(gpx, statistic_dict)
                    lines = gpx_statistics_print(statistic_dict, lines)
                    # ...........................................
                    # Finally write GPX to disc
                    # ...........................................
                    new_gpx_fileName1 = new_gpx_fileName + ".gpx"
                    with open(new_gpx_fileName1, 'w', encoding='utf-8') as f:     
                        f.write(gpx.to_xml())  
                    f.close()
            
                    if statistics.get():
                        new_gpx_fileName1 = new_gpx_fileName + ".txt"
                        with open(new_gpx_fileName1, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                        f.close()
                    
                gpx_file.close()     # Lese die GPX File ein als das was sie ist: Text
                delete_file(gpx_file_name)

        style = ttk.Style()
        style.configure("Red.TLabel", foreground="red")
        ttk.Label(mainframe, text="Running!", style="Red.TLabel").grid(column=1, row=8, sticky="W")
        root.update()
        # Jetzt frage ich ab, ob nur der eine Tracker abgefragt wird oder alle
        if all_Tracker.get():
            i = 0
            tracker_loops = my_tracker_amount
            for i in range(tracker_loops):
                tracker_id = my_tracker_id[i]
                get_my_track()
        else:
            tracker_id = my_tracker_id[my_tracker_names.index(choice_tracker.get())]
            get_my_track()

        style = ttk.Style()
        style.configure("Green.TLabel", foreground="green")
        ttk.Label(mainframe, text="Done!    ", style="Green.TLabel").grid(column=1, row=8, sticky="W")
    
    # ...........................................
    # Hier wird der Status des Click Select Buttons
    # für Alle Tracker aus einmal
    # abgefragt und entsprechend das Tracker Selektionsmenü
    # an- oder ausgeschaltet
    # ...........................................
    def toggle_tracker_selection():
        if all_Tracker.get():
            choice_tracker.state(["disabled"])
        else:
            choice_tracker.state(["!disabled"])

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
        error_message(3)
    # ................
    # Check days back
    # x = config_dic.get("days_back")
    # if not x: config_dic.update({"days_back" : 0})                                   # Init die Variable in der Config File
    # daysback = config_dic.get("days_back")
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
    if not x: config_dic.update({"cleaning_track" : False})                       # Init die Variable in der Config File
    # ................
    # Check for last Status of Statistics waned
    x = config_dic.get("statistics")
    if not x: config_dic.update({"statistics" : False})                                   # Init die Variable in der Config File
    # ................
    # Check for last Status of Smoothening Elevation data
    # x = config_dic.get("smooth")
    # if not x: config_dic.update({"smooth" : 0})                                   # Init die Variable in der Config File
    # smooth_loops = config_dic.get("smooth")

    # ................
    # Check for last Start Date set
    x = config_dic.get("start_date")
    start_date = (datetime.now().strftime("%Y-%m-%d"))
    if not x: config_dic.update({"start_date" : start_date})                                   # Init die Variable in der Config File
    start_date = config_dic.get("start_date")

    # ................
    # Check for All Tracker Flag set
    x = config_dic.get("all_tracker")
    if not x: config_dic.update({"all_tracker" : False})                                   # Init die Variable in der Config File
    all_tracker = config_dic.get("all_tracker")

    # ....................................................
    # Baue das Menü auf
    # ....................................................
    # root = Tk()
    root = ThemedTk(theme='radiance')
    # root = ThemedTk(theme='clearlooks')
    # root = ThemedTk(theme='adapta')
    # root = ThemedTk(theme='aquativo')
    # root = ThemedTk(theme='arc')
    # root = ThemedTk(theme='black')
    # root = ThemedTk(theme='blue')
    # root = ThemedTk(theme='elegance')
    # root = ThemedTk(theme='kroc')
    # root = ThemedTk(theme='plastik')
    # root = ThemedTk(theme='winxpblue')
    # root = ThemedTk(theme='smog')
    # root = ThemedTk(theme='yaru')
    '''Setting the x and y position from where the menue should pop up'''
    root.geometry('+{}+{}'.format(winx,winy))  
    root.title("Traccar2GPX - v2.3 (tested with Traccar v5.4 - v5.12)")
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
        error_message(5)

    # ....................................................
    # Setzte das Auswahlmenü für die Datümer
    # ....................................................
    start_button = ttk.Button(mainframe, text='Start Day:', command=select_start_date)
    start_button.grid(column=1,  row=1, sticky="E")
    start_datum = tk.StringVar()
    # start_datum.set(datetime.now().strftime("%Y-%m-01"))
    start_datum.set(start_date)
    start_entry = ttk.Entry(mainframe, textvariable=start_datum, state="readonly")
    start_entry.grid(column=2,columnspan=3,  row=1, sticky=W)

    # ttk.Label(mainframe, text="End Day:").grid(column=1, row=2, sticky=E)
    end_button = ttk.Button(mainframe, text='End Day:', command=select_end_date)
    end_button.grid(column=1,  row=2, sticky="E")
    end_datum = tk.StringVar()
    end_datum.set(datetime.now().strftime("%Y-%m-%d"))
    end_entry = ttk.Entry(mainframe, textvariable=end_datum, state="readonly")
    end_entry.grid(column=2,columnspan=3,  row=2, sticky=W)

    start_button = ttk.Button(mainframe, text='Today:', command=select_today_date)
    start_button.grid(column=3,  row=2, sticky="WE")
    # start_datum.set(datetime.now().strftime("%Y-%m-01"))


    # ....................................................
    # Setzte das Auswahlmenü für den Tracker
    # ....................................................
    ttk.Label(mainframe, text="Tracker:").grid(column=1, row=3, sticky="E")
    choice_tracker = ttk.Combobox(mainframe)
    choice_tracker['values'] = my_tracker_names
    choice_tracker.current(tracker_selected)                    # tracker_selected Wurde weiter oben in der Initialisierungsektion der Config Presets gesetzt
    choice_tracker.grid(column=2,columnspan=3,  row=3, sticky=W)
    choice_tracker.state(["readonly"])

    # ....................................................
    # Setzte das Auswahlmenü für Alle Tracks!
    # ....................................................
    # ttk.Label(mainframe, text="All Tracks at once:").grid(column=4, row=3, sticky=W)
    all_Tracker = BooleanVar(value=True)                                    # Zwingend die init einer TkInter BooleanVar machen!
    all_Tracker.set(config_dic.get("all_tracker"))                       # Die BoolenVar wird mit set und get behandelt.
    check_all_Tracker = ttk.Checkbutton(mainframe,  variable=all_Tracker, text="All Tracker at once")
    check_all_Tracker.grid(column=3, row=3, sticky="W")
    toggle_tracker_selection()                                              # stelle sicher, dass der letzte Status gesetzt wird.

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
        'LightGray',
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
        column=1, row=4, sticky=E)
    color_choice = ttk.Combobox(mainframe)
    color_choice['values'] = TrackColor
    color_choice.current(track_color_set)                   # track_color Wurde weiter oben in der Initialisierungsektion der Config Presets gesetzt
    color_choice.grid(column=2,columnspan=3,  row=4, sticky="W")
    color_choice.state(['readonly'])


    # ....................................................
    # Setzte das Auswahlmenü für Cleaning Track
    # ....................................................
    ttk.Label(mainframe, text="Clean Track:").grid(column=1, row=5, sticky=E)
    clean_Track = BooleanVar(value=True)                                    # Zwingend die init einer TkInter BooleanVar machen!
    clean_Track.set(config_dic.get("cleaning_track"))                       # Die BoolenVar wird mit set und get behandelt.
    check_clean_Track = ttk.Checkbutton(mainframe,  variable=clean_Track)
    check_clean_Track.grid(column=2, row=5, sticky="W")

    # ....................................................
    # Setzte das Auswahlmenü für Statistics y/n
    # ....................................................
    ttk.Label(mainframe, text="Statistics").grid(column=1, row=6, sticky=E)
    statistics = BooleanVar(value=True)                                    # Zwingend die init einer TkInter BooleanVar machen!
    statistics.set(config_dic.get("statistics"))                           # Die BoolenVar wird mit set und get behandelt.
    check_statistics = ttk.Checkbutton(mainframe,  variable=statistics)
    check_statistics.grid(column=2, row=6, sticky="W")

    # ....................................................
    # Setze die "Arbeitsknöpfe"
    # ....................................................

    one_track_button = ttk.Button(mainframe, text='Get ONE GPX Track', command=get_one_traccar)
    one_track_button.grid(column=1,  row=7, sticky="EW")
    # work_button.focus()

    work_button = ttk.Button(mainframe, text='Get DAILY GPX Track', command=get_daily_traccar)
    work_button.grid(column=2,  row=7, sticky="EW")
    # work_button.focus()

    quitbutton = ttk.Button(mainframe, text='Exit', command=quit_my_program)
    quitbutton.grid(column=3, row=7, sticky="EW")

    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5) 

    check_all_Tracker.configure(command=toggle_tracker_selection)

    root.update()
    
    root.protocol("WM_DELETE_WINDOW", quit_my_program)
    root.mainloop()

