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
|Selection of up to 90 days back from today  | - | x |
|Track format |KML | GPX|
|Track has a sounding name  | - | x |
|One track for each day  | - | x |
|Defined color of track  | - | x |
|Track can be cleaned from trackpoints not in motion or in motion with <2,5km/h  | - | x |
|Track includes timestamp data of each tracks waypoint  | - | x |
|Track can be used for geotagging  | - | x |

## Compatibility
This version has been tested with Traccar 5.2
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
* The file **must** be in the same directory as **traccar2gpx.exe**
* The file must include:
    *  the **URL** to access the traccar server & the **port** to access it. Typically this is http://your_url:8082 . <br />**Remark:** http not https!  <br /> If you self-host your traccar server, make sure the have the right port forward setup in your router.
    *  your user-id and password that has the proper rights to access your traccar admin API.
    
## Use of traccar2gpx

![traccar2gpx menue](https://motorradtouren.de/traccar2gpx.jpg "traccar2gpx menue options")


|Option |Explanation |
--- | --- |
|Amount of days back:|Select between 1..90 days. Day 1 = today.  |
|Tracker:|Select the tracker you want to pull the tracks from.  |
|Color of the GPX Track:|Select the color the GPX tracks should get.  |
|Clean track: |This is somehow tricky. It will delete all waypoints from the track that had no motion or motion is < 2,5km/H. It will delete the track if there are less then 10 trackpoints in total. Don't use this option if you use the track for e.g. Geotagging your pictures as no motion trackpoints can be of value.  |
|Result:|One GPX track per day selected. Each track has the days name as file- and trackname. If there is no file, there wasn't enough trackdata! |

## History
|Version |changes|
--- | --- |
|1.0 |Initial release|

## Future ideas (no commitment!)

* define a default preselect for tracker, color and Clean Track in the menue.
