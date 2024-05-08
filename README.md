# traccar2gpx

## What is Traccar?
With Traccar you can view defined GPS devices in real-time with no delay.

## How is Traccar working?
You need to own a tracker. A tracker is a small device, either handheld (e.g. „Traccar Client App“ using your mobile, mobile tracker „Incutex TK5000“) or fix mounted (e.g. OBD connected devices). A tracker sends its GPS position frequently via GPRS to a portal: Traccar.

Traccar is Open Source and can be hosted by yourself - or you buy it as a service. If you are interested in details: [Traccar.org](https://www.traccar.org/).

## Why traccar2gpx?
I'm doing lots of bicycle or motorbike trips that I'm tracking. The Traccar portal gives me the option to download a range of days and returns them as one track.

See the export options:
| |Legacy	|Modern|API|Traccar2gpx
:--- | :---: | :---: | :----: | :---: |
Excel|x||x|
KML||x||
Json|||x|
GPX||||x

While Traccars export option is pretty good, I have different needs. Let's compare some options:

|Option |Traccar |traccar2gpx|
--- | :---: | :---: |
|Several selections of days, weeks, month, range  | x | - |
|Selection of Start and End date  | - | x |
|Track format |KML | GPX|
|Track has a sounding name  | - | x |
|One track for timespan selected  | x | x |
|One track per day of selected timespan. | - | x |
|Get data from a single tracker or all tracker at once.  | - | x |
|Defined color of track  | - | x |
|Track can be cleaned from trackpoints not in motion or in motion with <2,5km/h  | - | x |
|Track includes timestamp data of each tracks waypoint  | - | x |
|Track can be used for geotagging  | - | x |

## Compatibility
This version has been tested with Traccar 5.4, 5.5, 5.6, 5.8
## Configuration file

traccar2gpx is configured by a sidecar configuration file. If you don't edit your config file with the needed credentials, traccar2gpx fails to run with an error exception.  
Here is an example of how to edit your config file:

```json
{
    "root_url": "your_url:port",
    "email": "your_email_2_access_traccar_server",
    "password": "your_password"
}
```
### More about the config file
* The config file **must** be named: **traccar2gpx.json**
* The file must be in valid json format.
* The file **must** be in the same directory as **traccar2gpx.exe**
* The file must include:
    *  the **URL** to access the traccar server & the **port** to access it. Typically this is http://your_url:8082 . <br />**Remark:** http not http**s**!  <br /> If you self-host your traccar server, make sure the have the right port forward setup in your router.
    *  your user-id and password that has the proper rights to access your traccar admin API.
    
## Use of traccar2gpx

![traccar2gpx menue](https://motorradtouren.de/traccar2gpx.jpg "traccar2gpx menue options")


|Option |Explanation |
--- | --- |
|Start Day:|Select the first day you want to pull tracks from Traccar. If you just want today, set todays date.
|End Day:|Select the last day. If you just want today, set todays date.
|Today:|Set Satrt Day and End Day to todays date.
|Tracker:|Select the tracker you want to pull the tracks from.  |
|All Tracker at once:|Check the box if you want the tracks of all tracker you own within the selected timeframe. You still can receive the tracks as "daily tracks" or as "one track per timefrime".  |
|Color of the GPX Track:|Select the color the GPX tracks should get.  |
|Clean track: |This is somehow tricky. It will delete all waypoints from the track that had no motion or motion is < 2,5km/H. It will delete the track if there are less then 10 trackpoints in total. Don't use this option if you use the track for e.g. Geotagging your pictures as no motion trackpoints can be of value.  |
|Get ONE GPX Track:|All trackdata from "Start Day" to "End Day" will be pulled into one single track. Usage example: Use the track for geotagging all pictures from a vacation. The tracks name shows the start and end date + tracker name. If there is no file, there wasn't enough trackdata! |
|Get DAILY GPX Track:|One GPX track per day range selected. Each track has the days and tracker name as file- and trackname. If there is no file, there wasn't enough trackdata! |

**REMARK:** If Windows Defender claims this program to have a virus: That is an known issue that comes with compiling Python code. Either add an exeption to Windows Defender or run the source code provided instead.

## History
|Version |changes|
--- | --- |
|1.0 |Initial release|
|1.1 |Reworked configuration file with initial setup.|
| | Menue selection of Tracker, Track Color and Clean Track are now saved in configuration as preselect.|
| | Menue window location is now saved in configuration for next start.|
|1.2 |Reworked most of the code. Pulling data from Traccar now in "Standard GPX Format" and reworking it for use with Garmin Software.|
| | Added smoothening of elevation data.|
|1.2.b | Removed smoothening of elevation data as algorythms used had no impact.|
| | You can pull data now back to one year.|
| | EXE file didn't work standalone. Should be fixed now.|
|2.0 | Moved from dayrange to date selection. Added option to pull either a single track or one track per day of selected range.|
|2.1 | Included checkbox to receive tracks within the selected timeframe for all tracker you own by one click. <br> Startdate is now saved in traccar2gpx.json. This can be convienient if you regulary prefer to start from a given date. The end date is always set to todays date. |
|2.2 | Added Today button to ease life when one wants to get only todays tracks.|
|2.3 | Fixed some minor problems.|
|2.4 | Fixed problems with codepages. Thanks to pki791.|
