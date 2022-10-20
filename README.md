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
GPX|||x|x
GPX Garmin Format||||x

While Traccars export option is pretty good, I have different needs. Let's compare some options:

|Option |Traccar |traccar2gpx|
--- | :---: | :---: |
|Several selections of days, weeks, month, range  | x | - |
|Selection of up to 90 days back from today  | - | x |
|Track format |KML | GPX|
|Garmin GPX format | - | x |
|Track has a sounding name  | - | x |
|One track for each day  | - | x |
|Defined color of track  | - | x |
|Track can be cleaned from trackpoints with little motion  | - | x |
|Track elevation can be smoothend  | - | x |
|Track includes timestamp data of each tracks waypoint  | - | x |
|Track can be used for geotagging  | - | x |

## Compatibility
This version has been tested with Traccar 5.4
## Configuration file

traccar2gpx is configured by a sidecar configuration file. Here is an example:

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
* There is an example of traccar2gpx.json on Github. 

* The file **must** be in the same directory as **traccar2gpx.exe**
* The file must include:
    *  the **URL** to access the traccar server & the **port** to access it. Typically this is http://your_url:8082 . <br />**Remark:** http not https!  <br /> If you self-host your traccar server, make sure to have the right port forward setup in your router.
    *  your user-id and password that has the proper rights to access your traccar admin API.
    * If you feel uncertain of how to write such a JSON file, start traccar2gpx.exe once. It will end with a failure message telling that a new configuration file has been created. 
    **Now edit this file by updating with your credentials to access your traccar server!**

* Viewing the config file after successfully running traccar2gpx you will find additional keys. They are updated automatically and you should not touch them.
    
## Use of traccar2gpx

![traccar2gpx menue](https://motorradtouren.de/traccar2gpx.jpg "traccar2gpx menue options")


|Option |Explanation |
--- | --- |
|Amount of days back:|Select between 1..90 days. Day 1 = today.  |
|Tracker:|Select the tracker you want to pull the tracks from.  |
|Color of the GPX Track:|Select the color the GPX tracks should get.  |
|Clean track: | This removes all trackpoints that have a speed of less than 0.5 km/h or a distance from point to point less than 1m. <br/>Don't use this option if you use the track for e.g. geotagging your pictures, as no motion trackpoints can be of value.  |
|Smooth Elevation data:| Smoothens the elevation data. Running multiple times may be helpful (1..30). <br/>Test with your device. |
|Result:|One GPX track per day selected. Each track has the days name as file- and trackname. If there is no file, there wasn't enough trackdata! |

## History
|Version |changes|
--- | --- |
|1.0 |Initial release|
|1.1 |Reworked configuration file with initial setup.|
| | Menue selection of Tracker, Track Color and Clean Track are now saved in configuration as preselect.|
| | Menue window location is now saved in configuration for next start.|
|1.2 |Reworked most of the code. Pulling data from Traccar now in "Standard GPX Format" and reworking it for use with Garmin Software.|
| | Added smoothening of elevation data.|