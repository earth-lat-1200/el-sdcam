#!/usr/bin/python3
# sdcfun2.py
VERSION = "Dec_08_2019"
# Autor: Kurt Niel, http://kepleruhr.at
# Aim: Intelligent webcam for sundials
# HW: Raspberry PI Std/Zero with PiCam, W1ThermSensors
# SW: Python3.4, PIL, PI-Cam, W1ThermSensor
# Modules
# sundialcam.py - Mainmodule
# sdcfun.py - Functions for parameter handling
# sdcfun2.py - Functions for further processing
# station.cfg - Containing working parameter
# remotecmd.cfg - Containing remote commands parameter
# sundialcam.log - Log file
# status.txt - Live status values
#
# History see Mainmodule

import configparser, os, time, math
from math import sin
from time import gmtime, strftime
from datetime import date, datetime, timedelta

#Waiting to get an exact capturing time = hh:mm:00 or hh:mm:30
def WaitCapture( goaltime, prolog ):
        settime = goaltime - prolog - 1
        ticksact = time.time()
        now = time.localtime( ticksact )
        nowS = int( time.strftime( "%S", now ) ) % goaltime
        nowMS = ticksact - int( ticksact )
        sleeptime = settime - nowS - nowMS
        if ( sleeptime > 0 ):
            time.sleep( sleeptime )
        while 1:
            ticksact = time.time()
            now = time.localtime( ticksact )
            nowS = int( time.strftime( "%S", now ) ) - sleeptime
            nowMS = ticksact - int( ticksact )
            if ( nowMS + nowS > prolog ):
                break

#Log status data to text file
def LogStatus( logticks, temp_CPU, temp_Cam, temp_Out, brightness ):
        logfile = strftime( 'sdcstatus%Y%b%d.txt', gmtime( logticks ) )
        if not os.path.isfile( logfile ):
                status_text = open( logfile, 'w' )
                status_text.write( 'date; time; T_CPU; T_Cam; T_Out; Brightness\n' )
        else:
                status_text = open( logfile, 'a' )
        dateUTC = strftime( "%d-%b-%Y", gmtime( logticks ) )
        timeUTC = strftime( "%H:%M:%S", gmtime( logticks ) )
        string = '{a}; {b}; {c}; {d}; {e}; {f}\n'.format( a = dateUTC, b = timeUTC, c = temp_CPU, d = temp_Cam, e = temp_Out, f = brightness )
        status_text.write( string )
        status_text.close()
        return

#Calculate equition of time [s] out of actual date within +/-2 sec
def fEoTs( dayticks ):
        eots   = 0.0
        pideg  = 3.14159265 / 180
        dayrel       = dayticks / 60 / 60 / 24 - 10957.54
        eps0         = 23.4391667 - dayrel / 36525 * 0.0130056
        L            = 36000.769 / 36525 * dayrel + 280.4656
        G            = 35999.05 / 36525 * dayrel + 357.528
        Lred         = L % 360.0
        Gred         = G % 360.0
        Lambda       = Lred + 1.915 * sin( Gred * pideg ) + 0.02 * sin( 2 * Gred * pideg )
        eotdeg       = -1.918 * sin( G * pideg ) - 0.02 * sin( 2 * G * pideg ) + 2.466 * sin( 2 * Lambda * pideg ) - 0.053 * sin( 4 * Lambda * pideg )
        #eots         = eotdeg * 4 * 60 - 1.8
        eots         = eotdeg * 4 * 60
        return eots

#Calculate equition of longitude [s] out of longitude
def fEoLs( long ):
        ret = 0
        ret = long * 24 / 360
        return ret * 60 * 60

#Calculate noon, sunset, and sunrise time in [h] out of ticks, longitude, and latitude
def SunRiseSetUTC( ticks, longitude, latitude ):
        dayyear = int( strftime( '%j', gmtime( ticks ) ) )
        #Latitude from Degree to Rad
        latirad = math.pi * latitude / 180
        #Declination of Sun at this day
        declisun = 0.4095 * math.sin( 0.016906 * ( dayyear - 80.086 ))
        #Definition of Sun height for rise and set - from Min to Rad
        sunset_h = -50.0 / 60.0 / 57.29578
        #From Noon to Set in hours
        noontoseth = 12 * math.acos(( math.sin(sunset_h ) - math.sin( latirad ) * math.sin( declisun )) / ( math.cos( latirad ) * math.cos( declisun ))) / math.pi
        #Equition of Time
        eoth = fEoTs( ticks ) / 60 / 60
        #Equition of Longitude
        eolh = longitude / 15
        #Calculate noon LAT and UTC, sunrise and sunset
        noonlat = datetime.combine( datetime.today(), datetime.strptime( '12:00:00', '%H:%M:%S').time() )
        noonutc = noonlat + timedelta( hours = -eoth - eolh )
        sunriseutc = noonlat + timedelta( hours = -noontoseth - eoth - eolh )
        sunsetutc = noonlat + timedelta( hours = noontoseth - eoth - eolh )
        return noonutc, sunriseutc, sunsetutc

#Summarize images of the day - e.g. make movie
def DoAfterSunset():
        #For future use
        return

###Calculate equition of time [s] out of day of year
##def fEoTs( doy ):
##        ret = 0
##        ret = -0.171 * sin( 0.0377 * doy + 0.465 ) - 0.1299 * sin( 0.01787 * doy - 0.168 )
##        return ret * 60 * 60
##
###Calculate equition of longitude [s] out of longitude
##def fEoLs( long ):
##        ret = 0
##        ret = long * 24 / 360
##        return ret * 60 * 60
##
###Calculate noon, sunset, and sunrise time in [h] out of ticks, longitude, and latitude
##def SunRiseSetUTC( ticks, longitude, latitude ):
##  dayyear = int( strftime( '%j', gmtime( ticks ) ) )
##  todate =  strftime( "%Y, %m, %d", gmtime( ticks ) )
##  #Latitude from Degree to Rad
##  latirad = math.pi * latitude / 180
##  #Declination of Sun at this day
##  declisun = 0.4095 * math.sin( 0.016906 * ( dayyear - 80.086 ))
##  #Definition of Sun height for rise and set - from Min to Rad
##  sunset_h = -50.0 / 60.0 / 57.29578
##  #From Noon to Set in hours
##  noontoseth = 12 * math.acos(( math.sin(sunset_h ) - math.sin( latirad ) * math.sin( declisun )) / ( math.cos( latirad ) * math.cos( declisun ))) / math.pi
##  #Equition of Time
##  eoth = -0.171 * math.sin( 0.0337 * dayyear + 0.465 ) - 0.1299 * math.sin( 0.01787 * dayyear - 0.168 )
##  # Differenz zwischen MOZ und MEZ/MESZ bestimmen
##  eolh = longitude/15
##  noonlat = datetime.combine( datetime.today(), datetime.strptime( '12:00:00', '%H:%M:%S').time() )
##  noonutc = noonlat + timedelta( hours = -eoth - eolh )
##  sunriseutc = noonlat + timedelta( hours = -noontoseth - eoth - eolh )
##  sunsetutc = noonlat + timedelta( hours = noontoseth - eoth - eolh )
##  return noonutc, sunriseutc, sunsetutc
##
