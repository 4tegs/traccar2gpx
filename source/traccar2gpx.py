# ##########################################################################################
# traccar 2 gpx
# Hans Straßgütl
#
# Fetches Tracks from Traccar and builds a valid Garmin GPX track.
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
#   2023 04 13      Remembers last Start Date set via JSON
#   2023 04 16      Now having the choice to selec either a single tracker or all tracker at once
#   2024 10 06      Many updates: 
#                       * Now with choices to select date range
#                       * Within the config JSON one can pre-set options per tracker. Details see Readme
# 
#   2026 06 10      Major update: 
#                       * complete recoding. First attempt was my first python code. Now 
#                   
#                   
#                   
# ##########################################################################################


# ------------------------------------------------------------------------------------------
# Global Imports
# ------------------------------------------------------------------------------------------
import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

import tkinter as tk
from tkinter import ttk, messagebox as msgbox
from ttkthemes import ThemedTk
from tkcalendar import Calendar

import gpxpy
import gpxpy.gpx
import numpy as np

# Optional: Use lxml for XML handling (fallback to standard library)
try:
    import lxml.etree as mod_etree
except ImportError:
    try:
        import xml.etree.cElementTree as mod_etree
    except ImportError:
        import xml.etree.ElementTree as mod_etree


# ..........................................................................................
# Constants and Defaults
# ..........................................................................................
DEFAULT_CONFIG = {
    "root_url": "http://your-url.de:8082",
    "email": "your_email",
    "password": "your_password",
    "winx": 100,
    "winy": 100,
    "track_color": 11,  # DarkBlue
    "cleaning_track": False,
    "statistics": True,
    "smooth": 5,
    "all_tracker": False,
    "start_date": datetime.now().strftime("%Y-%m-%d"),
    "end_date": datetime.now().strftime("%Y-%m-%d"),
}

# Color options: mapping from numeric codes to color names for BaseCamp compatibility
COLOR_OPTIONS = {
    0: "Magenta",
    1: "Cyan",
    2: "Green",
    3: "Red",
    4: "Blue",
    5: "Yellow",
    6: "LightGray",
    7: "DarkMagenta",
    8: "DarkCyan",
    9: "DarkGreen",
    10: "DarkRed",
    11: "DarkBlue",
    12: "DarkYellow",
    13: "DarkGrey",
    14: "Black",
}

# Reverse mapping for color names to numeric codes
COLOR_NAME_TO_CODE = {v: k for k, v in COLOR_OPTIONS.items()}

# ------------------------------------------------------------------------------
# Klasse: Utility
# Zweck : Utility Functions
# ------------------------------------------------------------------------------
class Utility:
    @staticmethod
    # ..............................................................................
    # Routine : delete_file()
    # ..............................................................................
    def delete_file(filepath: str) -> None:
        """Delete a file if it exists."""
        if os.path.exists(filepath):
            os.remove(filepath)

    @staticmethod
    # ..............................................................................
    # Routine : load_config()
    # ..............................................................................
    def load_config(config_file: str) -> Dict[str, Any]:
        """Load or create the configuration file."""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG.copy()
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file '{config_file}'.")

    @staticmethod
    # ..............................................................................
    # Routine : save_config()
    # ..............................................................................
    def save_config(config_file: str, data: Dict[str, Any]) -> None:
        """Save the configuration to a file."""
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    # ..............................................................................
    # Routine : convert_seconds_to_time()
    # ..............................................................................
    def convert_seconds_to_time(seconds: float) -> str:
        """Convert seconds to a formatted time string (HH:MM:SS)."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# ------------------------------------------------------------------------------
# Klasse: ErrorHandler
# Zweck : Error Handling
# ------------------------------------------------------------------------------
class ErrorHandler:
    ERROR_MESSAGES = {
        1: {
            "title": "Configuration Missing",
            "message": (
                "The configuration file <traccar2gpx.json> is missing.\n"
                "A template has been created in the current directory.\n"
                "Please update it with your Traccar credentials."
            ),
        },
        2: {
            "title": "Missing Traccar Data",
            "message": "Failed to fetch data from Traccar. Check your connection and credentials.",
        },
        3: {
            "title": "Invalid Configuration",
            "message": "The configuration file is invalid. Check the JSON format.",
        },
        4: {
            "title": "No Devices Found",
            "message": (
                "Could not fetch devices from Traccar.\n"
                "Ensure your user has admin rights and at least one active tracker."
            ),
        },
        5: {
            "title": "No Active Trackers",
            "message": "No active trackers available. Check your Traccar setup.",
        },
    }

    @staticmethod
    # ..............................................................................
    # Routine : show_error()
    # ..............................................................................
    def show_error(error_code: int) -> None:
        """Display an error message in a popup window."""
        msg = ErrorHandler.ERROR_MESSAGES.get(
            error_code,
            {"title": "Error", "message": "An unknown error occurred."}
        )
        root = tk.Tk()
        root.title(msg["title"])
        root.eval('tk::PlaceWindow . center')
        ttk.Label(root, text=msg["message"], padding=25).grid(column=0, row=0)
        ttk.Button(root, text="Exit", command=sys.exit).grid(column=0, row=1, pady=10)
        root.mainloop()



# ------------------------------------------------------------------------------
# Klasse: GPXProcessor
# Zweck: GPX Processing (BaseCamp-Compatible)
# ------------------------------------------------------------------------------
class GPXProcessor:
    @staticmethod
    # ..............................................................................
    # Routine : clean_track()
    # ..............................................................................
    def clean_track(gpx: gpxpy.gpx.GPX) -> gpxpy.gpx.GPX:
        """Remove invalid track points (speed < 0.5 km/h or > 250 km/h)."""
        if not gpx.tracks:
            return gpx

        for track in gpx.tracks:
            for segment in track.segments:
                i = 0
                while i < len(segment.points) - 1:
                    point = segment.points[i]
                    next_point = segment.points[i + 1]
                    
                    # Check for duplicate coordinates
                    if (point.latitude == next_point.latitude and
                        point.longitude == next_point.longitude):
                        segment.points.pop(i)
                        continue
                    
                    # Check speed (convert m/s to km/h)
                    speed = segment.get_speed(i)
                    if speed is None or speed < 0.5 / 3.6 or speed > 250 / 3.6:
                        segment.points.pop(i)
                        continue
                    i += 1
                segment.reduce_points(min_distance=1.0)
        return gpx

    @staticmethod
    # ..............................................................................
    # Routine : smooth_track()
    # ..............................................................................
    def smooth_track(gpx: gpxpy.gpx.GPX, window_size: int) -> gpxpy.gpx.GPX:
        """Smooth elevation data using a moving average."""
        if not gpx.tracks or window_size <= 0:
            return gpx

        for _ in range(window_size):
            for track in gpx.tracks:
                for segment in track.segments:
                    segment.smooth(vertical=True, horizontal=False, remove_extremes=False)
        return gpx

    @staticmethod
    # ..............................................................................
    # Routine : set_track_name()
    # ..............................................................................
    def set_track_name(gpx: gpxpy.gpx.GPX, date_str: str) -> Tuple[gpxpy.gpx.GPX, str]:
        """Set a descriptive name for the track (e.g., '2024-06-09_TrackerName')."""
        if not gpx.tracks:
            return gpx, ""

        for track in gpx.tracks:
            track.name = f"{date_str}_{track.name}"
        return gpx, f"{date_str}_{gpx.tracks[0].name}"

    @staticmethod
    # ..............................................................................
    # Routine : set_header()
    # ..............................................................................
    def set_header(gpx: gpxpy.gpx.GPX) -> gpxpy.gpx.GPX:
        """Set GPX header for BaseCamp compatibility."""
        gpx.nsmap = {
            "gpxx": "http://www.garmin.com/xmlschemas/GpxExtensions/v3",
            "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
        }
        gpx.creator = "https://gravelmaps.de"
        gpx.version = "1.1"
        
        # Add metadata for BaseCamp compatibility
        try:
            gpx.metadata = gpxpy.gpx.GPXMetadata()
            gpx.metadata.name = "Traccar2GPX Track"
            gpx.metadata.description = "Converted from Traccar to Garmin-compatible GPX"
        except (AttributeError, TypeError):
            # Fallback: Manually add metadata as XML elements
            try:
                gpx_xml = gpx.to_xml()
                root = mod_etree.fromstring(gpx_xml.encode('utf-8'))
                
                # Add metadata element
                metadata = mod_etree.Element("metadata")
                name = mod_etree.SubElement(metadata, "name")
                name.text = "Traccar2GPX Track"
                desc = mod_etree.SubElement(metadata, "desc")
                desc.text = "Converted from Traccar to Garmin-compatible GPX"
                
                # Insert metadata after the root element
                root.insert(1, metadata)
                
                # Parse back to gpx object
                gpx.from_xml(mod_etree.tostring(root, encoding='unicode'))
            except Exception:
                pass

        return gpx

    @staticmethod
    # ..............................................................................
    # Routine : set_time_format()
    # ..............................................................................
    def set_time_format(gpx: gpxpy.gpx.GPX) -> gpxpy.gpx.GPX:
        """Convert timezone-aware timestamps to UTC (Z) for Garmin compatibility."""
        if not gpx.tracks:
            return gpx

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point.time:
                        time_str = str(point.time)
                        
                        if " " in time_str and "Z" in time_str:
                            time_str = time_str.replace(" ", "T")
                        elif " " in time_str and "." in time_str:
                            time_str = time_str.replace(" ", "T") + "Z"
                        elif " " in time_str:
                            time_str = time_str.replace(" ", "T") + "Z"
                        elif "+" in time_str:
                            time_str = time_str.split("+")[0] + "Z"
                        elif "-" in time_str and time_str.count("-") > 2:
                            parts = time_str.split("-", 2)
                            time_str = parts[0] + "-" + parts[2].replace(":", "") + "Z"
                        elif "Z" not in time_str:
                            time_str = time_str + "Z"
                        
                        try:
                            point.time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
                        except ValueError:
                            pass
        return gpx

    @staticmethod
    # ..............................................................................
    # Routine : set_color()
    # ..............................................................................
    def set_color(gpx: gpxpy.gpx.GPX, color: str) -> gpxpy.gpx.GPX:
        """Add Garmin-compatible color extension to the track using color names."""
        namespace = "{http://www.garmin.com/xmlschemas/GpxExtensions/v3}"
        color_element = mod_etree.Element(f"{namespace}TrackExtension")
        color_sub = mod_etree.SubElement(color_element, f"{namespace}DisplayColor")
        
        # Use color name instead of numeric code for BaseCamp compatibility
        # color_name = COLOR_OPTIONS.get(color, "DarkBlue")
        color_sub.text = color

        if gpx.tracks:
            for track in gpx.tracks:
                track.extensions.append(color_element)
        return gpx

    @staticmethod
    # ..............................................................................
    # Routine : calculate_statistics()
    # ..............................................................................
    def calculate_statistics(gpx: gpxpy.gpx.GPX) -> Dict[str, str]:
        """Calculate and return statistics for the GPX track."""
        if not gpx.tracks:
            return {}

        stats = {}
        for track in gpx.tracks:
            for segment in track.segments:
                uphill, downhill = segment.get_uphill_downhill()
                min_elevation, max_elevation = gpx.get_elevation_extremes()
                moving_time, stopped_time, moving_distance, stopped_distance, max_speed = gpx.get_moving_data()

                stats = {
                    "Points in track": str(segment.get_points_no()),
                    "Length 2D": f"{int(segment.length_2d())} m",
                    "Length 3D": f"{int(segment.length_3d())} m",
                    "Max speed": f"{round((max_speed/1000*3600), 2)} Km/h",
                    "Elevation min": f"{int(min_elevation)} m",
                    "Elevation max": f"{int(max_elevation)} m",
                    "Uphill": f"{int(uphill)} m",
                    "Downhill": f"{int(downhill)} m",
                }
        return stats


# ..........................................................................................
# Traccar API Interaction
# ..........................................................................................

# ------------------------------------------------------------------------------
# Klasse: TraccarAPI
# Zweck : Kapselt logisch zusammengehörige Funktionen und Daten.
# ------------------------------------------------------------------------------
class TraccarAPI:
    @staticmethod
    # ..............................................................................
    # Routine : get_devices()
    # ..............................................................................
    def get_devices(config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch all enabled devices from Traccar."""
        url = f"{config['root_url']}/api/devices"
        auth = requests.auth.HTTPBasicAuth(config["email"], config["password"])
        params = {"all": "True"}

        try:
            response = requests.get(url, auth=auth, params=params, headers={"accept": "application/json"})
            response.raise_for_status()
        except requests.exceptions.InvalidSchema:
            ErrorHandler.show_error(7)
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            ErrorHandler.show_error(8)
            sys.exit(1)
        except requests.exceptions.HTTPError:
            ErrorHandler.show_error(4)
            sys.exit(1)

        devices = response.json()
        return [device for device in devices if not device.get("disabled", True)]

    @staticmethod
    # ..............................................................................
    # Routine : fetch_gpx()
    # ..............................................................................
    def fetch_gpx(
        config: Dict[str, Any],
        from_time: str,
        to_time: str,
        device_id: int,
        output_file: str
    ) -> None:
        """Fetch GPX data for a specific device and time range."""
        url = f"{config['root_url']}/api/positions/gpx"
        auth = requests.auth.HTTPBasicAuth(config["email"], config["password"])
        params = {
            "deviceId": [device_id],
            "from": from_time,
            "to": to_time,
        }
        headers = {"accept": "application/gpx+xml"}

        try:
            response = requests.get(url, auth=auth, params=params, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                ErrorHandler.show_error(2)
            else:
                ErrorHandler.show_error(4)
            sys.exit(1)

        with open(output_file, "wb") as f:
            f.write(response.content)


# ------------------------------------------------------------------------------
# Klasse: Traccar2GPXApp
# Main Application GUI
# ------------------------------------------------------------------------------
class Traccar2GPXApp:
    # ..............................................................................
    # Routine : __init__()
    # ..............................................................................
    def __init__(self, root: tk.Tk, config_file: str):
        self.root = root 
        self.config_file = config_file
        self.config = Utility.load_config(config_file)
        self.devices = []
        self.mainframe = None
        self.status_text = None
        self.setup_ui()

    # ..............................................................................
    # Routine : setup_ui()
    # ..............................................................................
    def setup_ui(self) -> None:
        """Initialize the user interface."""
        self.root.title("Traccar2GPX v3.0 (tested with Traccar 6.14.2)")
        self.root.eval('tk::PlaceWindow . center')

        self.mainframe = ttk.Frame(self.root, padding="25 25 25 25")
        self.mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Date selection
        ttk.Button(self.mainframe, text="Start Date:", command=self.select_start_date).grid(column=0, row=0, sticky=tk.W, pady=2)
        self.start_date = tk.StringVar(value=self.config.get("start_date", datetime.now().strftime("%Y-%m-%d")))
        start_entry = ttk.Entry(self.mainframe, textvariable=self.start_date, state="readonly")
        start_entry.grid(column=1, row=0, sticky=tk.W, pady=2)


        ttk.Button(self.mainframe, text="End Date:", command=self.select_end_date).grid(column=0, row=1, sticky=tk.W, pady=2)
        self.end_date = tk.StringVar(value=self.config.get("end_date", datetime.now().strftime("%Y-%m-%d")))
        end_entry = ttk.Entry(self.mainframe, textvariable=self.end_date, state="readonly")
        end_entry.grid(column=1, row=1, sticky=tk.W, pady=2)

        # Date range buttons
        # ttk.Label(self.mainframe, text="Quick Dates:").grid(column=0, row=2, sticky=tk.W, pady=2)
        ttk.Button(self.mainframe, text="Today", command=self.set_today).grid(column=0, row=2, sticky=tk.W, pady=2)
        ttk.Button(self.mainframe, text="Yesterday", command=self.set_yesterday).grid(column=1, row=2, sticky=tk.W, pady=2)
        ttk.Button(self.mainframe, text="This Week", command=self.set_this_week).grid(column=0, row=3, sticky=tk.W, pady=2)
        ttk.Button(self.mainframe, text="Last Week", command=self.set_last_week).grid(column=1, row=3, sticky=tk.W, pady=2)
        ttk.Button(self.mainframe, text="This Month", command=self.set_this_month).grid(column=0, row=4, sticky=tk.W, pady=2)
        ttk.Button(self.mainframe, text="Last Month", command=self.set_last_month).grid(column=1, row=4, sticky=tk.W, pady=2)
        ttk.Button(self.mainframe, text="This Year", command=self.set_this_year).grid(column=0, row=5, sticky=tk.W, pady=2)
        ttk.Button(self.mainframe, text="Last Year", command=self.set_last_year).grid(column=1, row=5, sticky=tk.W, pady=2)

        # Tracker selection

        ttk.Label(self.mainframe, text="Tracker:").grid(column=2, row=0, sticky=tk.E, pady=2)
        self.tracker_var = tk.StringVar()
        self.tracker_combobox = ttk.Combobox(self.mainframe, textvariable=self.tracker_var, state="readonly")
        self.tracker_combobox.grid(column=3, row=0, sticky=tk.W, pady=2)
        self.tracker_combobox.bind("<<ComboboxSelected>>", self.on_tracker_selected)

        # Color selection (using color names)
        ttk.Label(self.mainframe, text="Track Color:").grid(column=2, row=1, sticky=tk.E, pady=2)
        self.color_var = tk.StringVar(value=list(COLOR_OPTIONS.values())[self.config.get("track_color", 1)])
        self.color_combobox = ttk.Combobox(self.mainframe, textvariable=self.color_var, state="readonly")
        self.color_combobox["values"] = list(COLOR_OPTIONS.values())
        self.color_combobox.grid(column=3, row=1, sticky=tk.W, pady=2)
        
        # All trackers checkbox
        ttk.Label(self.mainframe, text="All Tracker at once:").grid(column=2, row=2, sticky=tk.E, pady=2)
        self.all_trackers = tk.BooleanVar(value=self.config.get("all_tracker", False))
        ttk.Checkbutton(self.mainframe, variable=self.all_trackers).grid(column=3, row=2, sticky=tk.W, pady=2)

        # Clean track checkbox
        ttk.Label(self.mainframe, text="Clean Track:").grid(column=2, row=3, sticky=tk.E, pady=2)
        self.clean_track = tk.BooleanVar(value=self.config.get("cleaning_track", False))
        ttk.Checkbutton(self.mainframe, variable=self.clean_track).grid(column=3, row=3, sticky=tk.W, pady=2)

        # Statistics checkbox
        ttk.Label(self.mainframe, text="Statistics:").grid(column=2, row=4, sticky=tk.E, pady=2)
        self.statistics = tk.BooleanVar(value=self.config.get("statistics", True))
        ttk.Checkbutton(self.mainframe, variable=self.statistics).grid(column=3, row=4, sticky=tk.W, pady=2)
        
        # Smooth elevation
        ttk.Label(self.mainframe, text="Smooth Elevation:").grid(column=2, row=5, sticky=tk.E, pady=2)
        self.smooth_var = tk.IntVar(value=self.config.get("smooth", 1))
        self.smooth_spinbox = ttk.Spinbox(self.mainframe, from_=0, to=59, textvariable=self.smooth_var)
        self.smooth_spinbox.grid(column=3, row=5, sticky=tk.W, pady=2)


        # Track type selection
        # ttk.Label(self.mainframe, text="Track Type:").grid(column=0, row=5, sticky=tk.W, pady=2)
        self.track_type = tk.StringVar(value=self.config.get("track_type", "daily"))
        ttk.Radiobutton(self.mainframe, text="Daily Tracks", variable=self.track_type, value="daily").grid(column=0, row=6, sticky=tk.W, pady=2)
        ttk.Radiobutton(self.mainframe, text="One Track", variable=self.track_type, value="one").grid(column=1, row=6, sticky=tk.W, pady=2)

        # Status text field with scrollbar
        ttk.Label(self.mainframe, text="Status:").grid(column=0, row=8, sticky=tk.W, pady=2)
        self.status_frame = ttk.Frame(self.mainframe)
        self.status_frame.grid(column=0, row=9, columnspan=6, sticky=tk.W+tk.E, pady=2)
        
        self.status_text = tk.Text(self.status_frame, height=5, width=80, state=tk.DISABLED, wrap=tk.WORD)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.status_scroll = ttk.Scrollbar(self.status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=self.status_scroll.set)

        # Set window position
        self.root.geometry(f"+{self.config.get('winx', 100)}+{self.config.get('winy', 100)}")

        # Load devices and set initial tracker
        self.load_devices()

        # Action buttons
        ttk.Button(self.mainframe, text="Fetch and Convert", command=self.fetch_and_convert).grid(column=0, row=10, pady=20)
        ttk.Button(self.mainframe, text="Exit", command=self.save_and_exit).grid(column=1, row=10, pady=20)

        # Clear status field on startup
        self.update_status("Ready")


    # ..............................................................................
    # Routine : update_status()
    # ..............................................................................
    def update_status(self, message: str) -> None:
        """Update the status text field with a new message (newest on top)."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)  # Scroll to the new message
        self.status_text.config(state=tk.DISABLED)
        self.root.update_idletasks()  # Force immediate GUI update

    # ..............................................................................
    # Routine : clear_status()
    # ..............................................................................
    def clear_status(self) -> None:
        """Clear the status text field."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)

    # ..............................................................................
    # Routine : on_tracker_selected()
    # ..............................................................................
    def on_tracker_selected(self, event=None) -> None:
        """Load tracker-specific defaults from config when tracker is selected."""
        selected_tracker = self.tracker_var.get()
        if not selected_tracker or not self.devices:
            return

        tracker_config = self.config.get(selected_tracker, {})

        if "track_color" in tracker_config:
            color_code = tracker_config["track_color"]
            self.color_var.set(COLOR_OPTIONS.get(color_code, "DarkBlue"))
        
        if "cleaning_track" in tracker_config:
            self.clean_track.set(tracker_config["cleaning_track"])
        
        if "smooth" in tracker_config:
            self.smooth_var.set(tracker_config["smooth"])

        if "statistics" in tracker_config:
            self.statistics.set(tracker_config["statistics"])

    # ..............................................................................
    # Routine : load_devices()
    # ..............................................................................
    def load_devices(self):
        """Lädt die Geräte asynchron und zeigt den Splash Screen an."""
        self.show_splash()  # Splash Screen anzeigen
        self.root.after(0, self._load_devices_async)  # Asynchron laden

    # ..............................................................................
    # Routine : _load_devices_async()
    # ..............................................................................
    def _load_devices_async(self):
        """Lädt die Geräte im Hintergrund und schließt den Splash Screen danach."""
        try:
            self.devices = TraccarAPI.get_devices(self.config)
            device_names = [device["name"] for device in self.devices]
            self.tracker_combobox["values"] = device_names
            
            initial_tracker = self.config.get("tracker_selected", device_names[0] if device_names else "")
            if initial_tracker in device_names:
                self.tracker_var.set(initial_tracker)
                self.on_tracker_selected()
            elif device_names:
                self.tracker_var.set(device_names[0])
                self.on_tracker_selected()
        except Exception:
            ErrorHandler.show_error(4)
        finally:
            self.hide_splash()  # Splash Screen schließen

    # ..............................................................................
    # Routine : select_start_date()
    # ..............................................................................
    def select_start_date(self) -> None:
        """Open a calendar to select the start date."""
        try:
            current_date = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
        except ValueError:
            current_date = datetime.now()
        
        date_window = tk.Toplevel(self.root)
        date_window.title("Select Start Date")
        date_window.geometry("300x300")
        date_window.update_idletasks()
        date_window.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")
        
        cal = Calendar(date_window, selectmode="day", year=current_date.year, month=current_date.month, day=current_date.day)
        cal.pack(padx=25, pady=25)

        # ..............................................................................
        # Routine : set_date()
        # ..............................................................................
        def set_date() -> None:
            selected_date = cal.selection_get().strftime("%Y-%m-%d")
            end_date = self.end_date.get()
            today = datetime.now().strftime("%Y-%m-%d")
            if selected_date > end_date:
                selected_date = end_date
            if selected_date > today:
                selected_date = today
            self.start_date.set(selected_date)
            date_window.destroy()

        ttk.Button(date_window, text="Set Date", command=set_date).pack(pady=10)

    # ..............................................................................
    # Routine : select_end_date()
    # ..............................................................................
    def select_end_date(self) -> None:
        """Open a calendar to select the end date."""
        try:
            current_date = datetime.strptime(self.end_date.get(), "%Y-%m-%d")
        except ValueError:
            current_date = datetime.now()
        
        date_window = tk.Toplevel(self.root)
        date_window.title("Select End Date")
        date_window.geometry("300x300")
        date_window.update_idletasks()
        date_window.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")
        
        cal = Calendar(date_window, selectmode="day", year=current_date.year, month=current_date.month, day=current_date.day)
        cal.pack(padx=25, pady=25)

        # ..............................................................................
        # Routine : set_date()
        # ..............................................................................
        def set_date() -> None:
            selected_date = cal.selection_get().strftime("%Y-%m-%d")
            start_date = self.start_date.get()
            today = datetime.now().strftime("%Y-%m-%d")
            if selected_date < start_date:
                selected_date = start_date
            if selected_date > today:
                selected_date = today
            self.end_date.set(selected_date)
            date_window.destroy()

        ttk.Button(date_window, text="Set Date", command=set_date).pack(pady=10)

    # ..............................................................................
    # Routine : set_today()
    # ..............................................................................
    def set_today(self) -> None:
        """Set date range to today."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.start_date.set(today)
        self.end_date.set(today)

    # ..............................................................................
    # Routine : set_yesterday()
    # ..............................................................................
    def set_yesterday(self) -> None:
        """Set date range to yesterday."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.start_date.set(yesterday)
        self.end_date.set(yesterday)

    # ..............................................................................
    # Routine : set_this_week()
    # ..............................................................................
    def set_this_week(self) -> None:
        """Set date range to this week."""
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        self.start_date.set(start_of_week.strftime("%Y-%m-%d"))
        self.end_date.set(now.strftime("%Y-%m-%d"))

    # ..............................................................................
    # Routine : set_last_week()
    # ..............................................................................
    def set_last_week(self) -> None:
        """Set date range to last week."""
        now = datetime.now()
        start_of_this_week = now - timedelta(days=now.weekday())
        start_of_last_week = start_of_this_week - timedelta(weeks=1)
        end_of_last_week = start_of_this_week - timedelta(days=1)
        self.start_date.set(start_of_last_week.strftime("%Y-%m-%d"))
        self.end_date.set(end_of_last_week.strftime("%Y-%m-%d"))

    # ..............................................................................
    # Routine : set_this_month()
    # ..............................................................................
    def set_this_month(self) -> None:
        """Set date range to this month."""
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        self.start_date.set(start_of_month.strftime("%Y-%m-%d"))
        self.end_date.set(now.strftime("%Y-%m-%d"))

    # ..............................................................................
    # Routine : set_last_month()
    # ..............................................................................
    def set_last_month(self) -> None:
        """Set date range to last month."""
        now = datetime.now()
        first_day_of_last_month = datetime(now.year, now.month - 1, 1) if now.month > 1 else datetime(now.year - 1, 12, 1)
        last_day_of_last_month = datetime(now.year, now.month, 1) - timedelta(days=1)
        self.start_date.set(first_day_of_last_month.strftime("%Y-%m-%d"))
        self.end_date.set(last_day_of_last_month.strftime("%Y-%m-%d"))

    # ..............................................................................
    # Routine : set_this_year()
    # ..............................................................................
    def set_this_year(self) -> None:
        """Set date range to this year."""
        now = datetime.now()
        start_of_year = datetime(now.year, 1, 1)
        self.start_date.set(start_of_year.strftime("%Y-%m-%d"))
        self.end_date.set(now.strftime("%Y-%m-%d"))

    # ..............................................................................
    # Routine : set_last_year()
    # ..............................................................................
    def set_last_year(self) -> None:
        """Set date range to last year."""
        now = datetime.now()
        start_of_last_year = datetime(now.year - 1, 1, 1)
        end_of_last_year = datetime(now.year - 1, 12, 31)
        self.start_date.set(start_of_last_year.strftime("%Y-%m-%d"))
        self.end_date.set(end_of_last_year.strftime("%Y-%m-%d"))

    # ..............................................................................
    # Routine : show_splash()
    # ..............................................................................
    def show_splash(self):
        """Zeigt einen Splash Screen, während die Geräte geladen werden."""
        self.splash = tk.Toplevel(self.root)
        # self.splash.overrideredirect(True)  # Kein Fensterrahmen
        self.splash.geometry(f"+{self.config.get('winx')}+{self.config.get('winy')}")
        # self.splash.geometry("300x100+500+300")
        self.splash.title("Traccar2GPX - Loading available Tracker")

        label = ttk.Label(
            self.splash,
            text="Loading available Tracker from your TRACCAR server via API.\nThis usually takes a few seconds.\n\nPlease wait.", font=("Helvetica", 12)
        )
        label.pack(padx=130,pady=220)

        # Fenster zentrieren
        self.splash.update()
        self.splash.lift()
        self.splash.grab_set()  # Blockiert Interaktion mit anderen Fenstern

    # ..............................................................................
    # Routine : hide_splash()
    # ..............................................................................
    def hide_splash(self):
        """Schließt den Splash Screen und zeigt das Hauptfenster an."""
        if hasattr(self, 'splash'):
            self.splash.destroy()
        self.root.deiconify()  # Hauptfenster anzeigen

    # ..............................................................................
    # Routine : fetch_and_convert()
    # ..............................................................................
    def fetch_and_convert(self) -> None:
        """Fetch data from Traccar and convert to GPX."""
        # Clear status field
        self.clear_status()
        
        start_date = self.start_date.get()
        end_date = self.end_date.get()
        track_type = self.track_type.get()
        all_trackers = self.all_trackers.get()

        if all_trackers:
            device_ids = [device["id"] for device in self.devices]
        else:
            selected_device = self.tracker_var.get()
            device_ids = [device["id"] for device in self.devices if device["name"] == selected_device]

        if not device_ids:
            self.update_status("Error: No tracker selected or available.")
            return

        for device_id in device_ids:
            device_name = next(device["name"] for device in self.devices if device["id"] == device_id)
            
            if track_type == "one":
                self.update_status(f"Starting: {start_date}_to_{end_date}_{device_name}")
                self.process_device(device_id, device_name, start_date, end_date, f"{start_date}_to_{end_date}")
            else:
                current_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                while current_date <= end_date_obj:
                    date_str = current_date.strftime("%Y-%m-%d")
                    self.update_status(f"Starting: {date_str}_{device_name}")
                    self.process_device(device_id, device_name, date_str, date_str, date_str)
                    current_date += timedelta(days=1)

        self.update_status("GPX files created successfully!")

    # ..............................................................................
    # Routine : process_device()
    # ..............................................................................
    def process_device(
        self,
        device_id: int,
        device_name: str,
        start_date: str,
        end_date: str,
        filename_prefix: str
    ) -> None:
        """Process a single device and date range."""
        temp_gpx_file = f"temp_{device_id}_{start_date}_to_{end_date}.gpx"
        output_gpx_file = f"{filename_prefix}_{device_name}.gpx"

        try:
             # Fetch GPX from Traccar
            TraccarAPI.fetch_gpx(
                self.config,
                f"{start_date}T00:00:00Z",
                f"{end_date}T23:59:59Z",
                device_id,
                temp_gpx_file
            )
            # Load and process GPX
            with open(temp_gpx_file, "r", encoding="utf-8") as f:
                gpx = gpxpy.parse(f)

            # Skip if no tracks
            if not gpx.tracks:
                self.update_status(f"No data for {device_name} on {start_date} to {end_date}")
                return

            # Skip if all segments are empty
            has_points = False
            for track in gpx.tracks:
                for segment in track.segments:
                    if segment.points:
                        has_points = True
                        break
                if has_points:
                    break

            if not has_points:
                self.update_status(f"No track points for {device_name} on {start_date} to {end_date}")
                return

             # Apply Garmin-specific processing
            gpx = GPXProcessor.set_header(gpx)
            gpx = GPXProcessor.set_time_format(gpx)

            # Berechne Statistiken für Raw GPX (vor allen Änderungen)
            raw_stats = GPXProcessor.calculate_statistics(gpx)

            # Bereinige den Track, falls "Clean Track" aktiviert ist
            if self.clean_track.get():
                gpx = GPXProcessor.clean_track(gpx)

            # Glätte den Track, falls "Smooth" aktiviert ist
            if self.smooth_var.get() > 0:
                gpx = GPXProcessor.smooth_track(gpx, self.smooth_var.get())

            # Berechne Statistiken für Reworked GPX (nach allen Änderungen)
            reworked_stats = GPXProcessor.calculate_statistics(gpx) if (self.clean_track.get() or self.         smooth_var.get() > 0) else None

            gpx, track_name = GPXProcessor.set_track_name(gpx, filename_prefix)
            gpx = GPXProcessor.set_color(gpx, self.color_var.get())

            # Save the processed GPX with Garmin-compatible XML
            with open(output_gpx_file, "w", encoding="utf-8") as f:
                f.write(gpx.to_xml())

            self.update_status(f"Created: {output_gpx_file}")

            if self.statistics.get():
                stats_file = f"{filename_prefix}_{device_name}.txt"
                with open(stats_file, "w", encoding="utf-8") as f:
                    f.write(f"Statistics for {stats_file}\n")
                    f.write("=" * 53 + "\n\n")

                    # Header für die Tabelle
                    f.write(" " * 27 + "Raw GPX        Reworked\n")
                    f.write("-" * 53 + "\n")

                    # Definiere die Kategorien und ihre Formatierung
                    categories = [
                        ("Points in Track", "Points in track", ": {:>13} {:>15}"),
                        ("Length 2D", "Length 2D", ": {:>15} {:>15}"),
                        ("Length 3D", "Length 3D", ": {:>15} {:>15}"),
                        ("Max Speed", "Max speed", ": {:>18} {:>15}"),
                        ("Elevation min", "Elevation min", ": {:>15} {:>15}"),
                        ("Elevation max", "Elevation max", ": {:>15} {:>15}"),
                        ("Uphill", "Uphill", ": {:>15} {:>15}"),
                        ("Downhill", "Downhill", ": {:>15} {:>15}"),
                    ]

                    # ....................................................
                    # Gib die Statistiken aus
                    # ....................................................
                    for category, key, format_str in categories:
                        raw_value = raw_stats.get(key, "0")
                        reworked_value = reworked_stats.get(key, raw_value) if reworked_stats else raw_value
                        f.write(f"{category:<17}{format_str.format(raw_value, reworked_value)}\n")
           
        except Exception as e:
            self.update_status(f"Error processing {device_name}: {str(e)}")
        finally:
            Utility.delete_file(temp_gpx_file)

    # ..............................................................................
    # Routine : save_and_exit()
    # ..............................................................................
    def save_and_exit(self) -> None:
        """Save configuration and exit the application."""
        self.config["winx"] = self.root.winfo_x()
        self.config["winy"] = self.root.winfo_y()
        
        self.config["track_color"] = COLOR_NAME_TO_CODE.get(self.color_var.get(), 11)
        self.config["cleaning_track"] = self.clean_track.get()
        self.config["statistics"] = self.statistics.get()
        self.config["all_tracker"] = self.all_trackers.get()
        self.config["start_date"] = self.start_date.get()
        self.config["end_date"] = self.end_date.get()
        self.config["smooth"] = self.smooth_var.get()
        self.config["track_type"] = self.track_type.get()
        
        # nicht sichern, der soll wirklich über die json gesteuert sein
        # selected_tracker = self.tracker_var.get()
        # if selected_tracker:
            # self.config[selected_tracker] = {
                # "track_color": COLOR_NAME_TO_CODE.get(self.color_var.get(), 11),  
                # "cleaning_track": self.clean_track.get(),
                # "smooth": self.smooth_var.get(),
                # "statistics": self.statistics.get()
            # }
        # self.config["tracker_selected"] = selected_tracker
        
        Utility.save_config(self.config_file, self.config)
        self.root.destroy()


# ------------------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------------------
if __name__ == "__main__":
    ''' Hier startet das Program '''
    root = ThemedTk(theme="radiance")  # oder ein anderes Thema wie "clam", "alt", "default", etc.
    app = Traccar2GPXApp(root, "traccar2gpx.json")
    root.mainloop()