# -*- coding: utf-8 -*-
print("Loading libraries")
import time

import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

import sys
import math
import pymysql

from time import time as TIME

import pandas as pd

from datetime import datetime,date,time,timedelta

print("Initializing")
runStart = datetime.now()

#database info
db_host = "localhost"
db_user = "user name"
db_pass = "password"
database= "Weather"

#database tables
airTable = "airobs"
skyTable = "skyobs"

# database field names
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

# color scale variables, build color gradients between specified RGB values across specified limit points
# bins describe the value limits
# colors are the RGB colors at those limits
TempColorBins=[0,45,60,80,100,110]
TempColors=[(0,0,64),(0,0,255),(0,255,0),(255,255,0),(255,0,0),(128,0,0)]
HumdColorBins=[0,15,30,50,80,100]
HumdColors=[(0,0,0),(31,120,193),(0,221,0),(0,255,0),(255,255,0),(255,0,0)]
FeelColorBins=[-32,-27,-19,-2,0,2,5,14,22]
FeelColors=[(109,31,98),(0,0,255),(0,120,193),(112,219,237),(0,0,0),(255,255,0),(255,132,0),(255,0,0),(137,0,0),(255,0,0)]
LuxColorBins=[0,4,400,30000,200000]
LuxColors=[(0,0,0),(0,0,85),(191,27,0),(234,184,57),(255,255,255)]
PresColorBins=[980,996,1012,1028,1044,1060]
PresColors=[(0,0,64),(0,0,255),(0,255,0),(255,255,0),(255,0,0),(128,0,0)]
#RainColorBins=[0,0.01,1,5,10,20,30]
RainColorBins=[0,0.01,0.1,0.3,0.5,1,3]
RainColors=[(0,0,0),(5,43,81),(10,67,124),(31,120,193),(81,149,206),(186,223,244),(255,255,255)]
WindColorBins=[0,5,15,30,50,60]
WindColors=[(0,0,0),(0,0,255),(0,255,0),(255,255,0),(255,0,0),(163,82,204)]
wDirColorBins=[0,45,90,13,180,225,270,315,360]
wDirColors=[(0,0,255),(0,255,255),(0,255,0),(119,255,0),(255,255,0),(255,119,0),(255,0,0),(255,0,255),(0,0,255)]

#convert meters per second into miles per hour, if you like mps set this to 1
mps2mph = 2.237


#-----------------------------------------------------------------------------------------------
# generate 8 bit scale factor without overflow
#-----------------------------------------------------------------------------------------------
def sf(x,scale):
    retval=255
    if x*scale<255:
        retval=x*scale
    return retval

#-----------------------------------------------------------------------------------------------
# get RGB color tuple based on input value and color bins
#-----------------------------------------------------------------------------------------------
def getColor(ival,bins,colors):
    cbin = 0
    if ival<bins[cbin]:
        return colors[cbin]
    if ival>bins[len(bins)-1]:
        return colors[len(colors)-1]
    while (cbin<len(bins)-1):
           #valRange = range(bins[cbin],bins[cbin+1])
           if (ival>=bins[cbin] and ival<=bins[cbin+1]):
               frac = (ival-float(bins[cbin]))/float(bins[cbin+1]-bins[cbin])
               r=colors[cbin][0]+frac*(colors[cbin+1][0]-colors[cbin][0])
               g=colors[cbin][1]+frac*(colors[cbin+1][1]-colors[cbin][1])
               b=colors[cbin][2]+frac*(colors[cbin+1][2]-colors[cbin][2])
               return (round(r),round(g),round(b))
           cbin=cbin+1        
    return (0,0,0) #shouldn't ever get here

#-----------------------------------------------------------------------------------------------
# scale RGB color tuple based on input scale factor
#-----------------------------------------------------------------------------------------------
def getScaledColor(ival,bins,colors,scaleFactor):
    cval = getColor(ival,bins,colors)
    cval = tuple(sf(c,scaleFactor) for c in cval)
    return cval

#-----------------------------------------------------------------------------------------------
# scale color based on some specified factor
#-----------------------------------------------------------------------------------------------
def getAlphaColor(ival,bins,colors,scaleFactor):
    cval = getColor(ival,bins,colors)
    cval = cval+(scaleFactor,)
    return cval

#-----------------------------------------------------------------------------------------------
# generate gradient scale bar
#-----------------------------------------------------------------------------------------------
def scaleImage(df,bins,colors): 
    imgScale = Image.new("RGB",(20,365))
    draw = ImageDraw.Draw(imgScale)
    ymn=df.min()
    ymx=df.max()
    yrg=ymx-ymn
    for y in range(0,360):
        c=ymn+(y/360.0)*yrg
        tc = getColor(c,bins,colors)
        co = tuple([int(x) for x in tc])
        draw.line([(0,360-y),(20,360-y)],co)
    return imgScale

#-----------------------------------------------------------------------------------------------
# generate gradient scale bar with labeled values
#-----------------------------------------------------------------------------------------------
def scaleImageVals(vals,df,bins,colors): 
    imgScale = Image.new("RGB",(40,365))
    draw = ImageDraw.Draw(imgScale)
    barWidth = 20
    txtStart = 23
    txtWidth = int(math.log10(max(vals))) # we need to narrow the scale bar when text is long

    if txtWidth>2:
        barWidth = barWidth-4*(txtWidth-2)
        txtStart = txtStart-4*(txtWidth-2)
        
    ymn=df.min()
    ymx=df.max()
    yrg=ymx-ymn
    valdx = 0
    for y in range(0,360):
        cl=ymn+(y/360.0)*yrg
        ch=ymn+(y+1)/360.0*yrg
        tc = getColor(cl,bins,colors)
        co = tuple([int(x) for x in tc])
        draw.line([(0,360-y),(barWidth,360-y)],co)
        if (valdx<len(vals) and vals[valdx]>=cl and vals[valdx]<=ch):
            yy=360-y-5
            if (yy<0):
                yy=0
            #print(y,(23,yy),str(vals[valdx]))
            draw.text((txtStart,yy),str(vals[valdx]),fill=(255,255,255))
            valdx=valdx+1
    return imgScale

#-----------------------------------------------------------------------------------------------
# generate the scale and legends for the image
#-----------------------------------------------------------------------------------------------
def scaleAndLegends(base,title,pos,ylabels,data,bins,colors,startTime=0):
#    print(title,pos,ylabels)
    drawImg = ImageDraw.Draw(base)
#    img = Image.fromarray(np.uint8(tempArray),mode="RGB").resize((1750,360))
#    base.paste(img,box=(25,75))
    if (type(ylabels[0]) is str):
        imgScale = scaleImage(data,bins,colors)
        idx=0
        for label in ylabels:
            repos = (pos[0]+1798,pos[1]-5+int(360.0/(len(ylabels)-1))*idx)
            #print(idx,":\t",label,repos)
            drawImg.text(repos,label,fill=(255,255,255))
            idx=idx+1
    else:
        imgScale = scaleImageVals(ylabels,data,bins,colors)
    repos = (pos[0]+1775,pos[1])
    base.paste(imgScale,box=repos)
    repos = (pos[0],pos[1]-15)
    drawImg.text(repos, title, fill=(255,255,255))

#-----------------------------------------------------------------------------------------------
# generate the x-axis 
#-----------------------------------------------------------------------------------------------
def xAxis(base,pos,start,stop):
    drawImg = ImageDraw.Draw(base)
    cDate=start
    idx=0
    dT=timedelta(days=1)
    timeSpan=stop-start
    spanFactor=1750/timeSpan.days
#    print(pos,timeSpan,spanFactor)
    while cDate<airEndTimePlot:
        if cDate.day==1:
            repos=(24+int(idx*spanFactor),pos[1]+365)
#            print(cDate,repos)
            label = str(cDate.month)+"/"+str(cDate.year-2000)
            drawImg.text(repos, label, fill=(255,255,255))
        idx=idx+1
        cDate=cDate+dT
    
#-----------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------

try:
    conn = pymysql.connect(host = db_host,
                           user=db_user,
                           passwd=db_pass,
                           db = database)
except pymysql.Error as e:
    print("Error %d: %s" % (e.args[0],e.args[1]))
    sys.exit(1)

conn.autocommit = True
cursor = conn.cursor(pymysql.cursors.DictCursor)

query = 'select '+timeField+' from '+airTable
#print query
try:
    cursor.execute(query)
    conn.commit()
except:
    st=sys.exc_type
    se=sys.exc_value
    if (se[0] != 1062):
        print("==")
        print("Query: ",query)
        print("Exception:",st," [",se,"]")
        print("==")
    #break
airRows = cursor.fetchall()

airObs=0
if airRows:
    airObs = len(airRows)
    firstTime= airRows[0]['TimeStamp'] # first measurement from Air unit should logically be the first time overall
    firstDay = (int(TIME())-firstTime)/86400
else:
    print("No data to work with")
    exit

query = 'select '+timeField+' from '+skyTable
#print query
try:
    cursor.execute(query)
except:
    st=sys.exc_type
    se=sys.exc_value
    if (se[0] != 1062):
        print("==")
        print("Query: ",query)
        print("Exception:",st," [",se,"]")
        print("==")
    #break
skyRows = cursor.fetchall()

skyObs=0
if skyRows:
    skyObs = len(skyRows)

#figure how many observations we're dealing with in total
maxObs = max(airObs,skyObs)

#figure out what date the plot will start on
airStartTime=datetime.utcfromtimestamp(airRows[0][timeField])

# plot always starts at beginning of the day
airStartTimePlot = airStartTime.replace(hour=0,minute=0,second=0) 

#figure out what date the plot will end on
airEndTime=datetime.utcfromtimestamp(airRows[len(airRows)-1][timeField])
airEndTimePlot = airEndTime.replace(hour=0,minute=0,second=0)

#create the data arrays to hold all the plot data
dateArray  = airEndTimePlot - np.arange((airEndTimePlot-airStartTimePlot).days) * timedelta(days=1)
maxDays    = (airEndTimePlot-airStartTimePlot).days+1
dayArray   = np.linspace(0,1439,1440,dtype=int)
tempArray  = np.zeros((1440,maxDays,3))
humidArray = np.zeros((1440,maxDays,3))
feelsArray = np.zeros((1440,maxDays,3))
luxArray   = np.zeros((1440,maxDays,3))
pressArray = np.zeros((1440,maxDays,3))
slprsArray = np.zeros((1440,maxDays,3))
rainArray  = np.zeros((1440,maxDays,3))
windArray  = np.zeros((1440,maxDays,3))
wdirArray  = np.zeros((1440,maxDays,3))
wdirArray1 = np.zeros((1440,maxDays,3))
wdirArray2 = np.zeros((1440,maxDays,4))
aBattArray = np.zeros(maxDays)
sBattArray = np.zeros(maxDays)
gustArray  = np.zeros(maxDays)

print("Loading data")
sql_Query = pd.read_sql_query('select * from '+airTable, conn)

df  = pd.DataFrame(sql_Query, columns=[timeField,tempField,'Pressure',presField,humdField,hidxField,battField])

sql_Query = pd.read_sql_query('select * from '+skyTable, conn)
dfs = pd.DataFrame(sql_Query, columns=[timeField,lghtField,rainField,rateField,windField,wdirField,battField])

print("Processing data")
print("...building time/date arrays for air data")
df['datetimes'] = [datetime.fromtimestamp(t) for t in df[timeField]]
df['date'] = [ dt.date() for dt in df['datetimes']]
df['time'] = [ dt.time() for dt in df['datetimes']]
df['minutes'] = [ (dt.hour*60+dt.minute) for dt in df['datetimes']]
df['days'] = [ (dt.date()-airStartTimePlot.date()).days for dt in df['datetimes']]

print("...building time/date arrays for sky data")
dfs['datetimes'] = [datetime.fromtimestamp(t) for t in dfs[timeField]]
dfs['date'] = [ dt.date() for dt in dfs['datetimes']]
dfs['time'] = [ dt.time() for dt in dfs['datetimes']]
dfs['minutes'] = [ (dt.hour*60+dt.minute) for dt in dfs['datetimes']]
dfs['days'] = [ (dt.date()-airStartTimePlot.date()).days for dt in dfs['datetimes']]

print("...loading air image arrays")
obs = 0
feels = df[hidxField]-df[tempField]
while (obs<airObs):
    tempArray[df['minutes'][obs],df['days'][obs]]=getColor(df[tempField][obs],TempColorBins,TempColors)
    humidArray[df['minutes'][obs],df['days'][obs]]=getColor(df[humdField][obs],HumdColorBins,HumdColors)
    feelsArray[df['minutes'][obs],df['days'][obs]]=getColor(feels[obs],FeelColorBins,FeelColors)
    pressArray[df['minutes'][obs],df['days'][obs]]=getColor(df[presField][obs],PresColorBins,PresColors)
#    prsArray[df['minutes'][obs],df['days'][obs]]=getColor(df['Pressure'][obs],PresColorBins,PresColors)
    obs=obs+1

print("...loading sky image arrays")
obs = 0
meanWind = dfs[windField].mean()
while (obs<skyObs):
    luxArray[dfs['minutes'][obs],dfs['days'][obs]]=getColor(dfs[lghtField][obs],LuxColorBins,LuxColors)
    rainArray[dfs['minutes'][obs],dfs['days'][obs]]=getColor(dfs[rainField][obs],RainColorBins,RainColors)
    windArray[dfs['minutes'][obs],dfs['days'][obs]]=getColor(dfs[windField][obs]*mps2mph,WindColorBins,WindColors)
    windScaleFactor = dfs[windField][obs]/meanWind # used to set transparency of wind direction based on wind speed
    wdirArray[dfs['minutes'][obs],dfs['days'][obs]]=getColor(dfs[wdirField][obs],wDirColorBins,wDirColors)
#    wdirArray1[dfs['minutes'][obs],dfs['days'][obs]]=getScaledColor(dfs[wdirField][obs],wDirColorBins,wDirColors,windScaleFactor)
    wdirArray2[dfs['minutes'][obs],dfs['days'][obs]]=getAlphaColor(dfs[wdirField][obs],wDirColorBins,wDirColors,windScaleFactor)
    obs=obs+1

print("...loading battery arrays")
day=0
while day<maxDays:
    aBattArray[day]=df[df['days']==day][battField].max()
    if not math.isnan(dfs[dfs['days']==day][battField].max()):
        sBattArray[day]=dfs[dfs['days']==day][battField].max()
        gustArray[day]=dfs[dfs['days']==day][windField].max()*mps2mph
    day=day+1
    
print("\nPlotting data")
baseImg = Image.new("RGB",(1900,4275))
drawImg = ImageDraw.Draw(baseImg)

print("...temperature")
img = Image.fromarray(np.uint8(tempArray),mode="RGB").resize((1750,360))
baseImg.paste(img,box=(25,75))
scaleAndLegends(baseImg,"Temperature (°F)",(25,75),(df[tempField].min(),df[tempField].max()),df[tempField],TempColorBins,TempColors)
xAxis(baseImg,(25,75),airStartTimePlot,airEndTimePlot)
img.save("WeatherTemp.png")

print("...humidity")
img = Image.fromarray(np.uint8(humidArray),mode="RGB").resize((1750,360))
baseImg.paste(img,box=(25,490))
scaleAndLegends(baseImg,"Humidity (%)",(25,490),("100%","0%"),df[humdField],HumdColorBins,HumdColors)
xAxis(baseImg,(25,490),airStartTimePlot,airEndTimePlot)
img.save("WeatherHumd.png")

print("...pressure")
img = Image.fromarray(np.uint8(pressArray),mode="RGB").resize((1750,360))
imgScale = scaleImage((df[presField]),PresColorBins,PresColors)
baseImg.paste(img,box=(25,905))
xAxis(baseImg,(25,905),airStartTimePlot,airEndTimePlot)
scaleAndLegends(baseImg,"Sea Level Pressure",(25,905),(df[presField].min(),df[presField].max()),df[presField],PresColorBins,PresColors)
img.save("WeatherSLPress.png")

print("...heat index")
img = Image.fromarray(np.uint8(feelsArray),mode="RGB").resize((1750,360))
hif=df[hidxField]-df[tempField]
baseImg.paste(img,box=(25,1320))
scaleAndLegends(baseImg,"Heat Index/Wind Chill dT",(25,1320),(hif.min(),0,hif.max()),hif,FeelColorBins,FeelColors)
xAxis(baseImg,(25,1320),airStartTimePlot,airEndTimePlot)
img.save("WeatherFeel.png")

print("...brightness")
img = Image.fromarray(np.uint8(luxArray),mode="RGB").resize((1750,360))
baseImg.paste(img,box=(25,1735))
scaleAndLegends(baseImg,"Brightness",(25,1735),(dfs[lghtField].min(),dfs[lghtField].max()),dfs[lghtField],LuxColorBins,LuxColors)
xAxis(baseImg,(25,1735),airStartTimePlot,airEndTimePlot)
img.save("WeatherLux.png")

print("...rainfall")
img = Image.fromarray(np.uint8(rainArray),mode="RGB").resize((1750,360))
baseImg.paste(img,box=(25,2150))
scaleAndLegends(baseImg,"Rainfall",(25,2150),(dfs[rainField].min(),dfs[rainField].max()),dfs[rainField],RainColorBins,RainColors)
xAxis(baseImg,(25,2150),airStartTimePlot,airEndTimePlot)
img.save("WeatherRain.png")

print("...wind speed")
img = Image.fromarray(np.uint8(windArray),mode="RGB").resize((1750,360))
baseImg.paste(img,box=(25,2565))
scaleAndLegends(baseImg,"Windspeed",(25,2565),(dfs[windField].min()*mps2mph,dfs[windField].max()*mps2mph),dfs[windField]*mps2mph,WindColorBins,WindColors)
xAxis(baseImg,(25,2565),airStartTimePlot,airEndTimePlot)
img.save("WeatherWind.png")

print("...wind direction")
img = Image.fromarray(np.uint8(wdirArray),mode="RGB").resize((1750,360))
imgScale = scaleImage((dfs[wdirField]),wDirColorBins,wDirColors)
baseImg.paste(img,box=(25,2980))
xAxis(baseImg,(25,2980),airStartTimePlot,airEndTimePlot)
scaleAndLegends(baseImg,"Wind Direction",(25,2980),("N","W","S","E","N"),dfs[wdirField],wDirColorBins,wDirColors)
img.save("WeatherWDir.png")

# the idea for this plot is that not all wind directions are equal, sometimes the wind is hardly blowing and the
# direction can be nearly random. So this plot fades out the wind direction for the wind speeds lower the mean.
img = Image.fromarray(np.uint8(wdirArray2),mode="RGBA").resize((1750,360))
baseImg.paste(img,box=(25,3395))
scaleAndLegends(baseImg,"Wind Direction scaled by Wind Speed",(25,3395),("N","W","S","E","N"),dfs[wdirField],wDirColorBins,wDirColors)
xAxis(baseImg,(25,3395),airStartTimePlot,airEndTimePlot)
img.save("WeatherWDir2.png")

# local air pressure plot for people interested in that
##img = Image.fromarray(np.uint8(pressArray),mode="RGB").resize((1750,360))
##imgScale = scaleImage((df['Pressure']),PresColorBins,PresColors)
##baseImg.paste(img,box=(25,3810))
##xAxis(baseImg,(25,3810),airStartTimePlot,airEndTimePlot)
##scaleAndLegends(baseImg,"Air Pressure",(25,3810),(df['Pressure'].min(),df['Pressure'].max()),df['Pressure'],PresColorBins,PresColors)
##img.save("WeatherPress.png")

print("...batteries")
dateArray.sort()
dpi=100
fig_size = 1750/float(dpi), 360/float(dpi)
plt.style.use('dark_background')
fig = plt.figure(figsize=fig_size)

ax = fig.add_subplot(111)
ax.set(ylim=(2.5,4.0))
ax.plot(dateArray,aBattArray[:len(dateArray)],'r',label="Air")
ax.plot(dateArray,sBattArray[:len(dateArray)],'g',label="Sky")
ax.set_ylabel('Battery (V)')
ax.legend()

imgByt = BytesIO()
fig.savefig(imgByt)
img = Image.open(imgByt)

baseImg.paste(img,box=(25,3810))

baseImg.show()
baseImg.save("WeatherPlot.png")

#
# this figure was solely to figure where I should place the bin values for wind speed
#
fig = plt.figure(figsize=fig_size)

ax = fig.add_subplot(111)
ax.set(ylim=(2.5,4.0))
ax.plot(dateArray,gustArray[:len(dateArray)],'b')
ax.set_ylabel('Windspeed (mph)')

imgByt = BytesIO()
fig.savefig(imgByt)
img = Image.open(imgByt)
#img.show()

print()
print("All done")
print("Elapsed time: ",(datetime.now()-runStart).seconds," seconds")
# Fini!
