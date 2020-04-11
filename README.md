# WeatherFlow_DisplayHistory
This is a set of scripts that allows Weather Flow users to display all the entirety of their weather data in a single display.
It's not a dashboard display per-se because the nature of the display is such that there isn't much change in what it looks 
like over the course of a day. So the idea is that most people would only want to run this script once a day or perhaps
several times a week to see the overall weather and trends.
The display is broken down into ten panels where each shows a particular weather measurement over the entire period. In each panel, every vertical line represents an entire day with local noon in the middle and midnight at the top & bottom. 
Here's a sample of the temperature panel:

![TemperaturePanel](TemperaturePanel.png)

## Contents
**[Requirements](#requirements)**<br>
**[Installation Instructions](#installation-instructions)**<br>
**[Running the Script](#running-the-script)**<br>

## Requirements

* Python 3
  * having the python executable on your system search path is helpful but not strictly necessary.
* An SQL database containing the weather data
  * other database types should also work but would require script tweaks. 
* basic text file editing skills

WeatherFlow Display History is largely platform agnostic and should run on any machine capable of running python 3 with the necessary libraries. The SQL database doesn't have to be local to the platform you're running the script on.


## Installation Instructions

While the script doesn't require being in any particular place on the system, I'd recommend putting it in it's own folder as it does create some files.

1. Open a command prompt and enter the following command:
```
python -m pip install --upgrade pip
```

2. Once that process has finished, run: 
```
python -m pip install numpy matplotlib Pillow pymysql pandas
```

3. After that's done, open WeatherFlow_DisplayHistory.py in a text editor and go to the section marked #database info (about 23 lines in) and replace the default values with the ones for your database.
```
db_host = "localhost"
db_user = "user name"
db_pass = "password"
database= "Weather"
```

4. Next go down to next section in the file, marked #database tables, and replace those values with the correct table names in your database. If you have the same table for both your sky and air readings just name twice. 
```
airTable = "airobs"
skyTable = "skyobs"
```

5. Last bit of editing, go down to the section in the file marked #database field names and modify the default values with the actual field names used in your data tables.
```
timeField = 'TimeStamp' # assumed the same for both air and sky databases
tempField = 'AirTemp'
presField = 'SeaLevelPressure'
humdField = 'RelHumidty'
hidxField = 'FeelsLike'
battField = 'Battery'   # assumed the same for both air and sky databases
lghtField = 'Lux'
rainField = 'PrecipAccum'
rateField = 'RainRate'
windField = 'WindGust'
wdirField = 'WindDirection'
```

6. Everything should be good to go, there are additional things you may want to tweak but just make sure everything works at this point before taking off into the jungle.


## Running the Script
From a command prompt, navigate to the directory where you put WeatherFlow_DisplayHistory.py script. (This wasn't mentioned before but you need to have write permissions to that directory)
Enter the following command:
```
python WeatherFlow_DisplayHistory.py
```
Go get a cup of coffee and come back in 15 minutes to an hour depending on the speed of the your machine, amount of data you have, and possibly the amount of network bandwidth (if the database isn't local). 
If things are running properly, you'll see lines like this start popping up on your screen:
```
Loading libraries
Initializing
Loading data
Processing data
...building time/date arrays for air data
...building time/date arrays for sky data
...loading air image arrays
...loading sky image arrays
...loading battery arrays

Plotting data
...temperature
...humidity
...pressure
...heat index
...brightness
...rainfall
...wind speed
...wind direction
...batteries
```
When the script is done running it will pop up a window on your display using whatever the default picture viewer is (Photos, Preview, xv, etc). If you don't have a display (or even if you do) the resulting picture is saved off in the local directory under the name WeatherPlot.png

Here's a sample of the final image with about 2 1/2 years of data
![WeatherPlot](WeatherPlot.png)
