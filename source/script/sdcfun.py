#!/usr/bin/python3
# sdcfun.py
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

config = configparser.ConfigParser()
status = configparser.ConfigParser()
info   = configparser.ConfigParser()
remote = configparser.ConfigParser()

#Class RunPar with parameter
class RunPar:
        def __init__( self ):
                self.IDName = 'IDName'
                self.IDNo = 'IDNo'
                self.PeriodM = 1
                self.FTPupload = 1
                self.Stream = 0
                self.Series = 0
                self.ZoomMove = 0
                self.ZoomDrawRect = 1
                self.CamOffLine = 0
                self.RemoteCMD = 0
                self.Host = 'host'
                self.Port = 22
                self.User = 'user'
                self.Password = 'password'

        def Init( self, periodm, ftpupload, stream, series, zoommove, zoomdrawrect, sysoffline, remotecmd ):
                self.IDName = 'idname'
                self.IDNo = 'idno'
                self.PeriodM = periodm
                self.FTPupload = ftpupload
                self.Stream = stream
                self.Series = series
                self.ZoomMove = zoommove
                self.ZoomDrawRect = zoomdrawrect
                self.CamOffLine = sysoffline
                self.RemoteCMD = remotecmd
                self.Host = 'host'
                self.Port = 22
                self.User = 'user'
                self.Password = 'password'

        def AdjustPeriod( self, periodm ):
                ret = 0
                if( periodm == 0):
                        ret = 30
                elif( periodm > 15 ):
                        ret = 900
                else:
                        ret = 60 * int( periodm )
                return ret

#Class Cam with parameter
class Cam:
        def __init__( self, camwidth, camheight ):
                self.CamWidth       = camwidth
                self.CamHeight      = camheight
                self.CropX2         = int( self.CropX1 + self.CropWidth )
                self.CropY2         = int( self.CropY1 + self.CropHeight )
                self.ZoomCentPercX  = int( 0 )
                self.ZoomCentPercY  = int( 0 )
                self.ZoomCentX      = int( self.CropWidth / 2 )
                self.ZoomCentY      = int( self.CropHeight / 2 )
                self.ZoomX1         = int( self.ZoomCentX - ( self.ZoomWidth / 2 ) )
                self.ZoomX2         = int( self.ZoomCentX + ( self.ZoomWidth / 2 ) )
                self.ZoomY1         = int( self.ZoomCentY - ( self.ZoomHeight / 2 ) )
                self.ZoomY2         = int( self.ZoomCentY + ( self.ZoomHeight / 2 ) )
                self.ZoomX1w        = int( self.ZoomX1 * self.CropWebWidth / self.CropWidth )
                self.ZoomX2w        = int( self.ZoomX2 * self.CropWebWidth / self.CropWidth )
                self.ZoomY1w        = int( self.ZoomY1 * self.CropWebHeight / self.CropHeight )
                self.ZoomY2w        = int( self.ZoomY2 * self.CropWebHeight / self.CropHeight )

        CropWidth         = int( 1860 )
        CropHeight        = int(  930 )
        CropX1            = int(  242 )
        CropY1            = int(  277 )
        CropWebWidth      = int(  800 )
        CropWebHeight     = int(  400 )
        ZoomPerc          = int(   22 )
        ZoomAspRatioPerc  = int(   75 )
        ZoomWebWidth      = int(  400 )
        ZoomWebHeight     = int(  300 )
        ZoomWidth         = int( CropWidth * ZoomPerc / 100 )
        ZoomHeight        = int( ZoomWidth * ZoomAspRatioPerc / 100 )
        ZoomCentPercX     = int(    0 )
        ZoomCentPercY     = int(    0 )
        ZoomCentX         = int( CropWidth * (50 + ZoomCentPercX) / 100 )
        ZoomCentY         = int( CropHeight * (50 + ZoomCentPercY) / 100 )
        DialW12X          = int( 1268 )
        DialW12Y          = int(  627 )
        DialS12X          = int( 1276 )
        DialS12Y          = int(  937 )
        DialE09X          = int(  957 )
        DialE09Y          = int(  752 )
        DialE15X          = int( 1458 )
        DialE15Y          = int(  700 )

        CropX2      = int( CropX1 + CropWidth )
        CropY2      = int( CropY1 + CropHeight )
        ZoomX1      = int( ZoomCentX - ( ZoomWidth / 2 ) )
        ZoomX2      = int( ZoomCentX + ( ZoomWidth / 2 ) )
        ZoomY1      = int( ZoomCentY - ( ZoomHeight / 2 ) )
        ZoomY2      = int( ZoomCentY + ( ZoomHeight / 2 ) )
        ZoomXshift  = int( 0 )
        ZoomYshift  = int( 0 )
        ZoomX1w     = int( ZoomX1 * CropWebWidth / CropWidth )
        ZoomX2w     = int( ZoomX2 * CropWebWidth / CropWidth )
        ZoomY1w     = int( ZoomY1 * CropWebHeight / CropHeight )
        ZoomY2w     = int( ZoomY2 * CropWebHeight / CropHeight )

        #Parameter zoom adjustment by actual shadow position
        def AdjustZoomParameterset( self, ticks ):
                return

        #Parameter adjust, check and limit
        def AdjustParameterset( self ):
                savepar = 0
                if self.CropPerc < 25:
                    self.CropPerc = 25
                    savepar = 1
                elif self.CropPerc > 100:
                    self.CropPerc = 100
                    savepar = 1
                if self.CropAspRatioPerc < 40:
                    self.CropAspRatioPerc = 40
                    savepar = 1
                elif self.CropAspRatioPerc > 150:
                    self.CropAspRatioPerc = 150
                    savepar = 1
                if self.CropCentPercX < -30:
                    self.CropCentPercX = -30
                    savepar = 1
                elif self.CropCentPercX > 30:
                    self.CropCentPercX = 30
                    savepar = 1
                if self.CropCentPercY < -30:
                    self.CropCentPercY = -30
                    savepar = 1
                elif self.CropCentPercY > 30:
                    self.CropCentPercY = 30
                    savepar = 1
                if self.CropWebWidth < 400:
                    self.CropWebWidth = 400
                    savepar = 1
                elif self.CropWebWidth > 800:
                    self.CropWebWidth = 800
                    savepar = 1
                if self.ZoomPerc < 15:
                    self.ZoomPerc = 15
                    savepar = 1
                elif self.ZoomPerc > 50:
                    self.ZoomPerc = 50
                    savepar = 1
                if self.ZoomAspRatioPerc < 50:
                    self.ZoomAspRatioPerc = 50
                    savepar = 1
                elif self.ZoomAspRatioPerc > 200:
                    self.ZoomAspRatioPerc = 200
                    savepar = 1
                if self.ZoomCentPercX < -40:
                    self.ZoomCentPercX = -40
                    savepar = 1
                elif self.ZoomCentPercX > 40:
                    self.ZoomCentPercX = 40
                    savepar = 1
                if self.ZoomCentPercY < -40:
                    self.ZoomCentPercY = -40
                    savepar = 1
                elif self.ZoomCentPercY > 40:
                    self.ZoomCentPercY = 40
                    savepar = 1
                if self.ZoomWebWidth < 300:
                    self.ZoomWebWidth = 300
                    savepar = 1
                elif self.ZoomWebWidth > 500:
                    self.ZoomWebWidth = 500
                    savepar = 1
                self.CropWidth     = int( self.CamWidth  * self.CropPerc / 100 )
                self.CropHeight    = int( self.CropWidth * self.CropAspRatioPerc / 100 )
                self.CropX1        = int( self.CamWidth  * (( 1 - self.CropWidth  / self.CamWidth  ) / 2 - self.CropCentPercX / 100 ) )
                self.CropY1        = int( self.CamHeight * (( 1 - self.CropHeight / self.CamHeight ) / 2 - self.CropCentPercY / 100 ) )
                self.CropX2        = int( self.CropX1 + self.CropWidth )
                self.CropY2        = int( self.CropY1 + self.CropHeight )
                self.ZoomWidth     = int( self.CropWidth * self.ZoomPerc / 100 )
                self.ZoomHeight    = int( self.ZoomWidth * self.ZoomAspRatioPerc / 100 )
                self.ZoomCentX     = int( self.CropWidth * (50 + self.ZoomCentPercX) / 100 )
                self.ZoomCentY     = int( self.CropHeight * (50 + self.ZoomCentPercY) / 100 )
                self.ZoomX1        = int( self.ZoomCentX - ( self.ZoomWidth / 2 ) )
                self.ZoomX2        = int( self.ZoomCentX + ( self.ZoomWidth / 2 ) )
                self.ZoomY1        = int( self.ZoomCentY - ( self.ZoomHeight / 2 ) )
                self.ZoomY2        = int( self.ZoomCentY + ( self.ZoomHeight / 2 ) )
                self.ZoomXshift    = int( 0 )
                self.ZoomYshift    = int( 0 )

                if ( self.ZoomX1 < 0 ) :
                        self.ZoomXshift = self.ZoomX1
                elif ( self.ZoomX2 > self.CamWidth ) :
                        self.ZoomXshift = self.ZoomX2 - self.CropWebWidth
                if ( self.ZoomY1 < 0 ) :
                        self.ZoomYshift = self.ZoomY1
                elif ( self.ZoomY2 > self.CamHeight ) :
                        self.ZoomYshift = self.ZoomY2 - self.CropWebHeight

                self.ZoomX1 = int( self.ZoomX1 - self.ZoomXshift )
                self.ZoomX2 = int( self.ZoomX2 - self.ZoomXshift )
                self.ZoomY1 = int( self.ZoomY1 - self.ZoomYshift )
                self.ZoomY2 = int( self.ZoomY2 - self.ZoomYshift )

                self.ZoomX1w = int( self.ZoomX1 * self.CropWebWidth / self.CropWidth )
                self.ZoomX2w = int( self.ZoomX2 * self.CropWebWidth / self.CropWidth )
                self.ZoomY1w = int( self.ZoomY1 * self.CropWebHeight / self.CropHeight )
                self.ZoomY2w = int( self.ZoomY2 * self.CropWebHeight / self.CropHeight )
                
                return savepar

#Write parameter file, if not exist
def WriteParameter( filename, cam, run, must ):
        if ( not os.path.isfile( filename ) ) or must:
                config[ 'Header' ] = { 'idname': run.IDName,
                                       'idno': run.IDNo }
                config[ 'FTP'    ] = { 'host': run.Host,
                                       'port': run.Port,
                                       'user': run.User,
                                       'password': run.Password }
                config[ 'Total'  ] = { 'cropperc': cam.CropPerc,
                                       'cropaspratioperc': cam.CropAspRatioPerc,
                                       'cropcentpercx': cam.CropCentPercX,
                                       'cropcentpercy': cam.CropCentPercY,
                                       'cropwebwidth': cam.CropWebWidth,
                                       'zoomperc': cam.ZoomPerc,
                                       'zoomaspratioperc': cam.ZoomAspRatioPerc,
                                       'zoomwebwidth': cam.ZoomWebWidth }
                config[ 'Detail' ] = { 'periodm': run.PeriodM,
                                       'ftpupload': run.FTPupload,
                                       'stream': run.Stream,
                                       'series': run.Series,
                                       'zoommove': run.ZoomMove,
                                       'zoomdrawrect': run.ZoomDrawRect,
                                       'camoffline': run.CamOffLine,
                                       'remotecmd': run.RemoteCMD,
                                       'zoomcentpercx': cam.ZoomCentPercX,
                                       'zoomcentpercy': cam.ZoomCentPercY }
                config[ 'Dial'   ] = { 'dialw12x': cam.DialW12X,
                                       'dialw12y': cam.DialW12Y,
                                       'dials12x': cam.DialS12X,
                                       'dials12y': cam.DialS12Y,
                                       'diale09x': cam.DialE09X,
                                       'diale09y': cam.DialE09Y,
                                       'diale15x': cam.DialE15X,
                                       'diale15y': cam.DialE15Y }
                with open( filename, 'w' ) as configfile:
                        config.write( configfile )

#Classe RunStatus with parameter
class RunStatus:
        def __init__( self, swversion ):
                self.SWVersion = swversion
                self.ImgUTC = 'none'
                self.ImgLAT = 'none'
                self.CPUTemp = 'CP.T'
                self.CamTemp = 'Ca.T'
                self.OutTemp = 'Ou.T'
                self.IMGBright = 0.0
                self.Sunny = 0
                self.Cloudy = 0
                self.Night = 0

        def Init( self, imgutc, imglat, cputemp, camtemp, outtemp, imgbright, sunny, cloudy, night ):
                self.ImgUTC = imgutc
                self.ImgLAT = imglat
                self.CPUTemp = cputemp
                self.CamTemp = camtemp
                self.OutTemp = outtemp
                self.IMGBright = imgbright
                self.Sunny = sunny
                self.Cloudy = cloudy
                self.Night = night

#Write status file
def WriteStatus( filename, runstat ):
        status[ 'System' ] = { 'swversion': runstat.SWVersion,
                               'capturetime': runstat.ImgUTC,
                               'capturelat': runstat.ImgLAT,
                               'cputemperature': runstat.CPUTemp,
                               'cameratemperature': runstat.CamTemp,
                               'outcasetemperature': runstat.OutTemp }
        status[ 'Dial'   ] = { 'brightness': runstat.IMGBright,
                               'sunny': runstat.Sunny,
                               'cloudy': runstat.Cloudy,
                               'night': runstat.Night }
        with open( filename, 'w' ) as statusfile:
                status.write( statusfile )

#Read parameter file
def GetParameter( filename, cam ):
        ret = RunPar()
        config.read( filename )
        cam.CropPerc          = config.getint( 'Total',  'cropperc' )
        cam.CropAspRatioPerc  = config.getint( 'Total',  'cropaspratioperc' )
        cam.CropCentPercX     = config.getint( 'Total',  'cropcentpercx' )
        cam.CropCentPercY     = config.getint( 'Total',  'cropcentpercy' )
        cam.CropWebWidth      = config.getint( 'Total',  'cropwebwidth' )
        cam.ZoomPerc          = config.getint( 'Total',  'zoomperc' )
        cam.ZoomAspRatioPerc  = config.getint( 'Total',  'zoomaspratioperc' )
        cam.ZoomWebWidth      = config.getint( 'Total',  'zoomwebwidth' )
        cam.DialW12X          = config.getint( 'Dial',   'dialw12x' )
        cam.DialW12Y          = config.getint( 'Dial',   'dialw12y' )
        cam.DialS12X          = config.getint( 'Dial',   'dials12x' )
        cam.DialS12Y          = config.getint( 'Dial',   'dials12y' )
        cam.DialE09X          = config.getint( 'Dial',   'diale09x' )
        cam.DialE09Y          = config.getint( 'Dial',   'diale09y' )
        cam.DialE15X          = config.getint( 'Dial',   'diale15x' )
        cam.DialE15Y          = config.getint( 'Dial',   'diale15y' )
        ret.IDName            = config.get(    'Header', 'idname' )
        ret.IDNo              = config.get(    'Header', 'idno' )
        ret.Host              = config.get(    'FTP',    'host' )
        ret.Port              = config.getint( 'FTP',    'port' )
        ret.User              = config.get(    'FTP',    'user' )
        ret.Password          = config.get(    'FTP',    'password' )
        ret.PeriodM           = config.getint( 'Detail', 'periodm' )
        ret.FTPupload         = config.getint( 'Detail', 'ftpupload' )
        ret.Stream            = config.getint( 'Detail', 'stream' )
        ret.Series            = config.getint( 'Detail', 'series' )
        ret.ZoomMove          = config.getint( 'Detail', 'zoommove' )
        ret.ZoomDrawRect      = config.getint( 'Detail', 'zoomdrawrect' )
        ret.CamOffLine        = config.getint( 'Detail', 'camoffline' )
        ret.RemoteCMD         = config.getint( 'Detail', 'remotecmd' )
        cam.ZoomCentPercX     = config.getint( 'Detail', 'zoomcentpercx' )
        cam.ZoomCentPercY     = config.getint( 'Detail', 'zoomcentpercy' )
        return ret

#Class Station with parameter
class Station:
        def __init__( self ):
                self.Name = 'Name'
                self.Location = 'Location'
                self.Latitude = 45.000000
                self.Longitude = 0.000000
                self.TypeWebcam = 'TypeWebcam'
                self.TypeTransfer = 'TypeTransfer'
                self.Team = 'Team'
                self.Organization = 'Organization'
                self.Website = 'Website'
                self.Text = 'Text'
                self.NearbyPublicInst = 'NearbyPublicInst'
        def Init( self ):
                self.Name = 'Name'
                self.Location = 'Location'
                self.Latitude = 45.000000
                self.Longitude = 0.000000
                self.TypeWebcam = 'TypeWebcam'
                self.TypeTransfer = 'TypeTransfer'
                self.Team = 'Team'
                self.Organization = 'Organization'
                self.Website = 'Website'
                self.Text = 'Text'
                self.NearbyPublicInst = 'NearbyPublicInst'

#Read station info file
def GetStationInfo( filename ):
        ret = Station()
        config.read( filename )
        ret.Name              = config.get(      'Info', 'name' )
        ret.Location          = config.get(      'Info', 'location' )
        ret.Latitude          = config.getfloat( 'Info', 'latitude' )
        ret.Longitude         = config.getfloat( 'Info', 'longitude' )
        ret.TypeWebcam        = config.get(      'Info', 'typewebcam' )
        ret.TypeTransfer      = config.get(      'Info', 'typetransfer' )
        ret.Team              = config.get(      'Info', 'team' )
        ret.Organization      = config.get(      'Info', 'organization' )
        ret.Website           = config.get(      'Info', 'website' )
        ret.Text              = config.get(      'Info', 'text' )
        ret.NearbyPublicInst  = config.get(      'Info', 'nearbypublicinst' )
        return ret

#Write station information file, if not exist
def WriteStationInfo( filename, run, station ):
        if not os.path.isfile( filename ):
                info[ 'Header' ] = { 'idname': run.IDName,
                                     'idno': run.IDNo }
                info[ 'Info'   ] = { 'name': station.Name,
                                     'location': station.Location,
                                     'latitude': station.Latitude,
                                     'longitude': station.Longitude,
                                     'typewebcam': station.TypeWebcam,
                                     'typetransfer': station.TypeTransfer,
                                     'team': station.Team,
                                     'organization': station.Organization,
                                     'website': station.Website,
                                     'text': station.Text,
                                     'nearbypublicinst': station.NearbyPublicInst }
                with open( filename, 'w' ) as stationfile:
                        info.write( stationfile )

#Class Remote with parameter
class Remote:
        def __init__( self ):
                self.CamOffLine = 0
                self.PerodM = 1
                self.Series = 0
                self.ZoomMove = 0
                self.ZoomDrawRect = 0
                self.ZoomCentPercX = 0
                self.ZoomCentPercY = 0
        def Init( self ):
                self.CamOffLine = 0
                self.PerodM = 1
                self.Series = 0
                self.ZoomMove = 0
                self.ZoomDrawRect = 0
                self.ZoomCentPercX = 0
                self.ZoomCentPercY = 0

#Read Remote file
def GetRemote( filename ):
        ret = Remote()
        remote.read( filename )
        ret.CamOffLine     = remote.getint( 'Command', 'camoffline' )
        ret.PeriodM        = remote.getint( 'Command', 'periodm' )
        ret.Series         = remote.getint( 'Command', 'series' )
        ret.ZoomMove       = remote.getint( 'Command', 'zoommove' )
        ret.ZoomDrawRect   = remote.getint( 'Command', 'zoomdrawrect' )
        ret.ZoomCentPercX  = remote.getint( 'Detail',  'zoomcentpercx' )
        ret.ZoomCentPercY  = remote.getint( 'Detail',  'zoomcentpercy' )
        return ret

#Write remote command file
def WriteRemote(filename, remote):
        remote[ 'Command' ] = { 'camoffline': remote.CamOffLine,
                                'periodm': remote.PerodM,
                                'series': remote.Series, 
                                'zoommove': remote.ZoomMove, 
                                'zoomdrawrect': remote.ZoomDrawRect }
        remote[ 'Detail'  ] = { 'zoomcentpercx': remote.ZoomCentPercX,
                                'zoomcentpercy': remote.ZoomCentPercY }
        with open( filename, 'w' ) as stationfile:
                info.write( stationfile )