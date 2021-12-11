#!/usr/bin/python3
# sundialcam.py
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
# History:
# Apr 24 2019 - starting version
# Oct 27 2019 - correction of EoL: inserting the hour number
#               improving temperatur reading via W1Thermsensor: reread while reading a wrong number '85.0'
#               correct names in station.cfg to English
# Nov 16 2019 - add some more comment to the code
#               prepare SW switch for partly bluring image
#               insert brand to the total image
#               insert name to the total image
# Dec 08 2019 - cleanup naming conventions
#               cleanup parameters for more convenient usage.

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os, sys, getopt, time, ftplib, configparser, logging
import picamera
from w1thermsensor import W1ThermSensor
import sdcfun, sdcfun2
from time import gmtime, strftime
from datetime import date, datetime, timedelta
from math import sin
import requests, base64

# FontPath = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"
# FontPathBold = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
FontPath = "fonts/LiberationSans-Regular.ttf"
FontPathBold = "fonts/LiberationSans-Bold.ttf"
Sans10 = ImageFont.truetype( FontPath, 10 )
Sans11 = ImageFont.truetype( FontPath, 11 )
Sans12 = ImageFont.truetype( FontPath, 12 )
SansBold12 = ImageFont.truetype( FontPathBold, 12 )
Sans16 = ImageFont.truetype( FontPathBold, 16 )

def main( argv ):
        print( 'Sundialcam warmup ..........' )
        #Delay on startup
        time.sleep( 30 )

        loglevel = "INFO"
        try:
                opts, args = getopt.getopt( argv, "l:", ["llevel="] )
        except getopt.GetoptError:
                print( 'sundialcam.py -l <loglevel> DEBUG | INFO | WARNING | ERROR | CRITITCAL' )
                print( '.Terminated.' )
                exit( 2 )
        for opt, arg in opts:
                if opt == '-l':
                        loglevel = arg

        numeric_level = getattr( logging, loglevel.upper(), None )
        if not isinstance( numeric_level, int ):
                print( 'sundialcam.py -l <loglevel> DEBUG | INFO | WARNING | ERROR | CRITITCAL' )
                print( '.Terminated.' )
                exit( 2 )

        #Start after warmup
        TicksAct = time.time()
        ActTime = time.asctime( time.localtime( TicksAct ) )
        print( 'Starting after warmup ......', ActTime )
        logfilename = strftime( "sdc%Y%b.log", gmtime( TicksAct ) )
        logging.basicConfig( filename = logfilename, format = '%(asctime)s %(levelname)s: %(message)s', level = numeric_level )
        logging.info( 'Start --- sundialcam.py - V.%s ---', VERSION )

        #Working parameter
        PlotInfo       = 0
        OPDelayS       = 8
        OPDelayMax     = 20
        OPRestS        = 10
        InPeriod       = 1
        AfterSunset    = 0
        WLANon         = 0                #yet not checked and in use
        IPSDCon        = 0                #yet not checked and in use
        FTPSDCon       = 0
        P_Capture      = 1
        P_TransTot     = 1
        P_TransDet     = 1
        P_TransInfo    = 1
        P_TransOffline = 0
        P_TransDark    = 0
        BlurImage      = 0                #Blur region off/on, region parameters at blur section

        #File parameter
        FileImgLive        = '/mnt/ramdisk/imgLive.bmp'
        FileImgTotal       = '/mnt/ramdisk/imgTotal.jpg'
        FileImgDetail      = '/mnt/ramdisk/imgDetail.jpg'
        FileImgMask        = '/mnt/ramdisk/imgMask.png'
        FileImgOffline     = 'imgCamOffLine.jpg'
        FileImgCloudyNight = 'imgCloudyNight.jpg'
        FileStationCfg     = 'station.cfg'
        FileStationInfo    = 'stationinfo.txt'
        FileStatus         = '/mnt/ramdisk/status.txt'
        FileRemoteCmdCfg   = '/mnt/ramdisk/remotecmd.cfg'

        #Time parameters
        PeriodS    = 60
        DayYear    = 0
        EoTs       = 0
        EoLs       = 0
        NoonUTC    = '00:00:00'
        SunRiseUTC = '00:00:00'
        SunSetUTC  = '00:00:00'

        #Control parameter - stored within parameter file
        PeriodM      = 1
        FTPupload    = 1
        Stream       = 0
        Series       = 0
        ZoomMove     = 0
        ZoomDrawRect = 1
        SysOffline   = 1
        RemoteCmd    = 0

        #Control parameter - not yet stored within parameter file
        BThresCloudy = 3300
        BThresSunny = 280000
        BThresCloudyHyst = 200
        BThresSunnyHyst = 20000

        #Initializing Pi Camera
        try:
                Cam = picamera.PiCamera()
        except:
                print( 'Could not connect to camera.' )
                logging.info( 'End: Could not connect to camera ----------' )
                exit( 2 )

        Cam.resolution = Cam.MAX_RESOLUTION
        camwidth = Cam.resolution.width
        camheight = Cam.resolution.height

        #Initializing camera, capturing, and remote parameter
        SDCCam = sdcfun.Cam( camwidth, camheight )
        SDCRun = sdcfun.RunPar()
        PeriodS = SDCRun.AdjustPeriod( SDCRun.PeriodM )
        SDCRun.Init( PeriodM, FTPupload, Stream, Series, ZoomMove, ZoomDrawRect, SysOffline, RemoteCmd )
        SDCStatus = sdcfun.RunStatus( VERSION )
        SDCStatus.Sunny = 0
        SDCStatus.Cloudy = 0
        SDCStatus.Night = 0
        SDCRemote = sdcfun.Remote()

        #Write parameter file if not exist
        sdcfun.WriteParameter( FileStationCfg, SDCCam, SDCRun, 0 )
        sdcfun.WriteStatus( FileStatus, SDCStatus )

        #Read parameter file and write if modified
        SDCRun = sdcfun.GetParameter( FileStationCfg, SDCCam )
        if ( SDCCam.AdjustParameterset() == 1 ):
            sdcfun.WriteParameter( FileStationCfg, SDCCam, SDCRun, 1 )

        #Initialize, read, and write station parameter
        SDCStation = sdcfun.Station()
        sdcfun.WriteStationInfo( FileStationInfo, SDCRun, SDCStation )
        SDCStation = sdcfun.GetStationInfo( FileStationInfo )

        #Initialize and count applied W1ThermSensors if available
        N_W1Sensors = 0
        W1Sensors = []
        try:
                for sensor in W1ThermSensor.get_available_sensors():
                        W1Sensors.append( sensor )
                        N_W1Sensors += 1
                print( "T.Sensors: ", N_W1Sensors )
        except:
                logging.info( 'No W1ThermSensor applied.' )

        #Start evaluation
        TicksAct = time.time()
        ActTime = time.asctime( time.localtime( TicksAct ) )
        print( 'Start evaluation ...........', ActTime )

        #Infinit loop
        InPeriod = 1
        while InPeriod:
                try:
                        P_Capture  = 1
                        if ( (SDCStatus.Night == 0) and (SDCRun.CamOffLine == 0) ):
                                P_TransTot = 1
                                P_TransDet = 1
                        P_TransCmd = 0

                        #Check CPU and system parameter
                        res = os.popen("vcgencmd measure_temp").readline()
                        CPUTemp = (res.replace("temp=", "").replace("'C\n",""))
                        SDCStatus.CPUTemp = CPUTemp
                        if N_W1Sensors == 1:
                                SDCStatus.CamTemp = "%.1f" % W1Sensors[0].get_temperature()
                                text = ( 'Temperature: Case {a}°C  CPU {b}°C' ).format( a = SDCStatus.CamTemp, b = SDCStatus.CPUTemp )
                                print( text )
                        elif N_W1Sensors == 2:
                                SDCStatus.OutTemp = "%.1f" % W1Sensors[0].get_temperature()
                                if ( float( SDCStatus.OutTemp ) == 85.0 ):
                                    SDCStatus.OutTemp = "%.1f" % W1Sensors[0].get_temperature()
                                    if ( float( SDCStatus.OutTemp ) == 85.0 ):
                                        SDCStatus.OutTemp = "TT.T"
                                SDCStatus.CamTemp = "%.1f" % W1Sensors[1].get_temperature()
                                if ( float( SDCStatus.CamTemp ) == 85.0 ):
                                    SDCStatus.CamTemp = "%.1f" % W1Sensors[1].get_temperature()
                                    if ( float( SDCStatus.CamTemp ) == 85.0 ):
                                        SDCStatus.CamTemp = "TT.T"
                                text = ( 'Temperature: Out {a}°C  Case {b}°C  CPU {c}°C' ).format( a = SDCStatus.OutTemp, b = SDCStatus.CamTemp, c= SDCStatus.CPUTemp )
                                print( text )
                        else:
                                text = ( 'Temperature: CPU {a}°C' ).format( a = SDCStatus.CPUTemp )
                                print( text )

                        #Waiting to get an exact capturing time = hh:mm:00 or hh:mm:30 ( sec, prolog )
                        sdcfun2.WaitCapture( 30, 3.1 ) #prolog 3.3 until Feb. 25 2019

                        #Image capture and evaluate timings
##                        TicksCap = time.time()
##                        NoonUTC, SunRiseUTC, SunSetUTC = sdcfun2.SunRiseSetUTC( TicksCap, SDCStation.Longitude, SDCStation.Latitude )
##                        DayYear = int( strftime( '%j', gmtime( TicksCap ) ) )
##                        #tbd: correction with fractions of a day; in the meanwhile take half of the day - high noon
##                        EoTs = sdcfun2.fEoTs( DayYear + 0.5 )
                        TicksCap = time.time()
                        NoonUTC, SunRiseUTC, SunSetUTC = sdcfun2.SunRiseSetUTC( TicksCap, SDCStation.Longitude, SDCStation.Latitude )
                        EoTs = sdcfun2.fEoTs( TicksCap )
                        EoLs = sdcfun2.fEoLs( SDCStation.Longitude )
                        if ( EoTs < 0 ):
                                ImgEoT = strftime( 'EoT:  -%M:%S', gmtime( -EoTs ) )
                        else:
                                ImgEoT = strftime( 'EoT: +%M:%S', gmtime( EoTs ) )
                        if ( EoLs < 0 ):
                                ImgEoL = strftime( 'EoL:  -%H:%M:%S', gmtime( -EoLs ) )
                        else:
                                ImgEoL = strftime( 'EoL: +%H:%M:%S', gmtime( EoLs ) )
                        if P_Capture:
                                #preview() + sleep() for brightness control
                                Cam.start_preview()
                                time.sleep( 1 )
                                Cam.stop_preview()
                                Cam.capture( FileImgLive )
                                logging.debug( 'Image capture - period %i sec', PeriodS )
                                TicksIm = time.time()
                                ImageTime = time.asctime( time.localtime( TicksIm ) )
                                SDCStatus.ImgUTC = strftime( "UTC: %d %b %Y %H:%M:%S", gmtime( TicksIm ) )
                                SDCStatus.ImgLAT = strftime( 'LAT: %d %b %Y %H:%M:%S', gmtime( TicksIm + EoTs + EoLs ) )
                                print( 'Image capture', ImageTime, 'Ticks', TicksIm, 'Period', PeriodS )

                                #Evaluating image brightness caused by weather condition
                                again = float( Cam.analog_gain )
                                dgain = float( Cam.digital_gain )
                                gain = again * dgain + 0.01
                                SDCStatus.IMGBright = int( 1e9 / float( Cam.exposure_speed ) / gain )
                                if SDCStatus.IMGBright > (BThresCloudy + BThresCloudyHyst):
                                        BThresCloudyHyst = -abs( BThresCloudyHyst )
                                        SDCStatus.Night = 0
                                        SDCStatus.Cloudy = 1
                                        SDCStatus.Sunny = 0
                                        P_TransTot = 1
                                        P_TransDet = 1
                                        P_TransDark = 0
                                else:
                                        BThresCloudyHyst = abs( BThresCloudyHyst )
                                        if SDCStatus.Night == 0:
                                                P_TransDark = 1
                                        else:
                                                P_TransDark = 0
                                        SDCStatus.Night = 1
                                        SDCStatus.Cloudy = 0
                                        SDCStatus.Sunny = 0
                                if SDCStatus.IMGBright > (BThresSunny + BThresSunnyHyst):
                                        BThresSunnyHyst = -abs( BThresSunnyHyst )
                                        SDCStatus.Night = 0
                                        SDCStatus.Cloudy = 0
                                        SDCStatus.Sunny = 1
                                else:
                                        BThresSunnyHyst = abs( BThresSunnyHyst )
                                print( 'IMGBright ', SDCStatus.IMGBright,'Night ', SDCStatus.Night, 'Cloudy ', SDCStatus.Cloudy, 'Sunny ', SDCStatus.Sunny )

                                #Image processing
                                logging.debug( 'Start image processing' )

                                #Select image by online/offline and brightness
                                if ( not( SDCRun.RemoteCMD ) and SDCRun.CamOffLine ) or ( SDCRun.RemoteCMD and SDCRemote.CamOffLine ):
                                        pil_imo = Image.open( FileImgOffline ).convert( 'RGB' )
                                        P_TransOffline = 1
                                else:
                                        P_TransOffline = 0
                                        if SDCStatus.Night == 1:
                                                pil_imo = Image.open( FileImgCloudyNight ).convert( 'RGB' )
                                        else:
                                                pil_imo = Image.open( FileImgLive ).convert( 'RGB' )

                                #Croping camera image to fit the sundial
                                cropbox = (SDCCam.CropX1, SDCCam.CropY1, SDCCam.CropX2, SDCCam.CropY2)
                                total_im = pil_imo.crop( cropbox )
                                if PlotInfo:
                                        im = array( total_im )
                                        imshow( im )
                                        x = [SDCCam.ZoomCentX, SDCCam.ZoomX1, SDCCam.ZoomX1, SDCCam.ZoomX2, SDCCam.ZoomX2]
                                        y = [SDCCam.ZoomCentY, SDCCam.ZoomY1, SDCCam.ZoomY2, SDCCam.ZoomY1, SDCCam.ZoomY2]
                                        plot( x, y, 'r*' )
                                        show()

                                #Magnifier for detail onto croped image
                                zoombox = ( SDCCam.ZoomX1, SDCCam.ZoomY1, SDCCam.ZoomX2, SDCCam.ZoomY2 )
                                detail_im = total_im.crop( zoombox )

                                #Fit images for web
                                out = total_im.resize( (SDCCam.CropWebWidth, SDCCam.CropWebHeight) )
                                outdetail = detail_im.resize( (SDCCam.ZoomWebWidth, SDCCam.ZoomWebHeight) )

                                #Blur accesable region
                                if not os.path.isfile( FileImgMask ):
                                        #create polygon mask
                                        mask = Image.new( 'L', out.size, 0 )
                                        maskdraw = ImageDraw.Draw( mask )
                                        #the follwing polygon defines the blur region
                                        maskdraw.polygon( [ ( 2, SDCCam.CropWebHeight - 70 ),
                                                            ( SDCCam.CropWebWidth - 3, SDCCam.CropWebHeight - 130 ),
                                                            ( SDCCam.CropWebWidth - 3, SDCCam.CropWebHeight - 3 ),
                                                            ( 2, SDCCam.CropWebHeight - 3 ) ], fill = "white" )
                                        mask.save( FileImgMask )
                                else:
                                        mask = Image.open( FileImgMask )
                                mask = mask.resize( (SDCCam.CropWebWidth, SDCCam.CropWebHeight) )
                                blurred = out.filter( ImageFilter.GaussianBlur( 5 ) )
                                if BlurImage == 1:
                                        out.paste( blurred, mask = mask )

                                #Prepare info print onto total image
                                watermark = Image.new( 'RGBA', out.size )
                                #watermark = Image.new( 'RGBA', out.size, (255,255,255,0) )
                                draw = ImageDraw.Draw( watermark, 'RGBA' )
                                #Print brand onto total image
                                draw.rectangle( ( (   0, 0), ( 95, 14 ) ), fill = "gray", outline = "gray" )
                                draw.text( (  2,  1), 'Sdcam@kepleruhr', font = Sans11, fill = "white" )
                                #Print station name onto total image
                                namecent = SDCCam.CropWebWidth / 2
                                namelenpix2 = 52 / 16 * len( SDCStation.Name )
                                draw.rectangle( ( ( namecent - namelenpix2 - 15, 2), ( namecent + namelenpix2 + 15, 20 ) ), fill = "white", outline = "white" )
                                #draw.rectangle( ( ( namecent - 100, 2), ( namecent + 100, 21 ) ), fill = (255,255,255,128), outline = "white" )
                                draw.text( (  namecent - namelenpix2,  5), SDCStation.Name, font = SansBold12, fill = "black" )
                                #Print Noon, Sunrise, Sunset (UTC) on top of the image
                                TodayUTCstr   = 'Today locals in UTC:'
                                SunRiseUTCstr = 'Sunrise  {:%H:%M:%S}'.format( SunRiseUTC )
                                NoonUTCstr    = 'Noon      {:%H:%M:%S}'.format( NoonUTC )
                                SunSetUTCstr  = 'Sunset   {:%H:%M:%S}'.format( SunSetUTC )
                                draw.rectangle( ( ( SDCCam.CropWebWidth - 119, 2), ( SDCCam.CropWebWidth - 3, 78 ) ), fill = "white", outline = "white" )
                                draw.text( (SDCCam.CropWebWidth - 116,   6), TodayUTCstr, font = Sans12, fill = "black" )
                                draw.text( (SDCCam.CropWebWidth - 111,  25), SunRiseUTCstr, font = Sans12, fill = "black" )
                                draw.text( (SDCCam.CropWebWidth - 111,  44), NoonUTCstr, font = Sans12, fill = "black" )
                                draw.text( (SDCCam.CropWebWidth - 111,  63), SunSetUTCstr, font = Sans12, fill = "black" )
                                #Print capturing time (UTC, EoT, EoL, LAT) onto total image
                                draw.rectangle( ( (   2, SDCCam.CropWebHeight - 22), ( 160, SDCCam.CropWebHeight - 3 ) ), fill = "white", outline = "white" )
                                draw.rectangle( ( ( 163, SDCCam.CropWebHeight - 22), ( 240, SDCCam.CropWebHeight - 3 ) ), fill = "white", outline = "white" )
                                draw.rectangle( ( ( 243, SDCCam.CropWebHeight - 22), ( 334, SDCCam.CropWebHeight - 3 ) ), fill = "white", outline = "white" )
                                draw.rectangle( ( ( 337, SDCCam.CropWebHeight - 22), ( 494, SDCCam.CropWebHeight - 3 ) ), fill = "white", outline = "white" )
                                draw.text( (  5, SDCCam.CropWebHeight - 18), SDCStatus.ImgUTC, font = Sans12, fill = "black" )
                                draw.text( (166, SDCCam.CropWebHeight - 18), ImgEoT, font = Sans12, fill = "black" )
                                draw.text( (246, SDCCam.CropWebHeight - 18), ImgEoL, font = Sans12, fill = "black" )
                                draw.text( (340, SDCCam.CropWebHeight - 18), SDCStatus.ImgLAT, font = Sans12, fill = "black" )
                                #Print temperature values onto total image
                                draw.rectangle( ( ( SDCCam.CropWebWidth - 269, SDCCam.CropWebHeight - 22), ( SDCCam.CropWebWidth - 3, SDCCam.CropWebHeight - 3 ) ), fill="white", outline = "white" )
                                draw.text( (SDCCam.CropWebWidth - 265, SDCCam.CropWebHeight - 18), 'Temp:', font = Sans12, fill = "black" )
                                draw.text( (SDCCam.CropWebWidth - 223, SDCCam.CropWebHeight - 18), 'Out ' + SDCStatus.OutTemp + '°C', font = Sans12, fill = "black" )
                                draw.text( (SDCCam.CropWebWidth - 153, SDCCam.CropWebHeight - 18), 'Case ' + SDCStatus.CamTemp + '°C', font = Sans12, fill = "black" )
                                draw.text( (SDCCam.CropWebWidth -  75, SDCCam.CropWebHeight - 18), 'CPU ' + SDCStatus.CPUTemp + '°C', font = Sans12, fill = "black" )

                                #Print zoom window onto total image
                                if (not( SDCRun.RemoteCMD ) and SDCRun.ZoomDrawRect) or (SDCRun.RemoteCMD and SDCRemote.ZoomDrawRect):
                                        draw.rectangle( ( ( SDCCam.ZoomX1w, SDCCam.ZoomY1w ), ( SDCCam.ZoomX2w, SDCCam.ZoomY2w ) ), fill = 0, outline = "white" )

                                #Save composed total image
                                Image.composite( watermark, out, watermark ).save( FileImgTotal )
                                #testing transparent overlay - still not finished
                                #Image.alpha_composite( watermark, out ).save( FileImgTotal )

                                #Save detail image
                                outdetail.save( FileImgDetail )

                                #Finalize image processing
                                logging.debug( 'End image processing' )
                                P_Capture = 0

                        #Store status information
                        sdcfun.WriteStatus( FileStatus, SDCStatus )

                        #Transfer images via FTP
                        if ( SDCRun.FTPupload ):
                                logging.debug( 'Start image transfer' )

                                #Check internet connection
                                if os.system( "sudo ping -c 1 " + SDCRun.Host + " > /dev/null 2>&1 &") == 0:
                                        IPSDCon = 1
                                        logging.debug( 'Host is reachable' )
                                else:
                                        IPSDCon = 0
                                        logging.warning( 'Host not reachable' )

                                #connect and login to FTP server
                                if ( FTPSDCon == 0 ):
                                        try:
                                                logging.debug( 'Opening FTP connection' )
                                                ftp = ftplib.FTP( SDCRun.Host, timeout=10 )
                                                logging.debug( 'Before connection to FTP server' )
                                                ftp.login( SDCRun.User, SDCRun.Password )
                                                logging.debug( 'Connected to FTP server' )
                                                FTPSDCon = 1
                                        except:
                                                logging.warning( 'Error connecting to FTP server' )
                                                FTPSDCon = 0
                                                print( 'FTP error connecting' )

                                #send and quit FTP connection
                                if FTPSDCon:
                                        try:
                                                if P_TransInfo:
                                                        f = open( FileStationInfo, 'rb' )
                                                        ftp.storbinary( 'STOR stationinfo.txt', f )
                                                        logging.debug( 'End stationinfo transfer' )
                                                        f.close()
                                                        P_TransInfo = 0
                                                if P_TransTot or P_TransOffline or P_TransDark:
                                                        f = open( FileImgTotal, 'rb' )
                                                        ftp.storbinary( 'STOR imgtotal.jpg', f )
                                                        logging.debug( 'End imgtotal transfer' )
                                                        f.close()
                                                        P_TransTot = 0
                                                if P_TransDet or P_TransOffline or P_TransDark:
                                                        f = open( FileImgDetail, 'rb' )
                                                        ftp.storbinary( 'STOR imgdetail.jpg', f )
                                                        logging.debug( 'End imgdetail transfer' )
                                                        f.close()
                                                        P_TransDet = 0
                                                f = open( FileStatus, "rb" )
                                                ftp.storbinary( "STOR status.txt", f )
                                                logging.debug( 'End status transfer' )
                                                f.close()
                                                try:
                                                        f = open( FileRemoteCmdCfg, 'wb' )
                                                        ftp.retrbinary( 'RETR remotecmd.cfg', f.write )
                                                        logging.debug( 'End remotecmd transfer' )
                                                        f.close()
                                                        P_TransCmd = 1
                                                except:
                                                        P_TransCmd = 0
                                                ftp.quit()
                                                logging.debug( 'FTP closed' )
                                                FTPSDCon = 0
                                        except:
                                                logging.warning( 'Error uploading to FTP server' )
                                                FTPSDCon = 0
                                                print( 'FTP error uploading' )

                                        TicksAct = time.time()
                                        OPDelayS = int( TicksAct - TicksCap )
                                        if ( OPDelayS > OPDelayMax ):
                                                logging.warning( 'Exceeded expected runtime - OPDelayS %i sec', OPDelayS )

                                logging.debug( 'End image transfer' )
                        
                        else:
                                # image transfer via REST
                                logging.debug( 'Start image transfer' )
                                requestData = {}

                                if P_TransInfo:
                                        requestData['stationInfo'] = {
                                                'header': {
                                                        'idName': SDCRun.IDName,
                                                        'idNo': SDCRun.IDNo
                                                },
                                                'info': {
                                                        'name': SDCStation.Name,
                                                        'location': SDCStation.Location,
                                                        'latitude': SDCStation.Latitude,
                                                        'longitude':SDCStation.Longitude,
                                                        'typeWebCam': SDCStation.TypeWebcam,
                                                        'typeTransfer': SDCStation.TypeTransfer,
                                                        'text': SDCStation.Text,
                                                        'website': SDCStation.Website,
                                                        'team': SDCStation.Team,
                                                        'nearbyPublicInst': SDCStation.NearbyPublicInst,
                                                        'organization': SDCStation.Organization
                                                }
                                        }
                                        P_TransInfo = 0

                                if P_TransTot or P_TransOffline or P_TransDark:
                                        imgTotal_base64 = ''
                                        with open(FileImgTotal, 'rb') as image_file:
                                                imgTotal_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                                        requestData['imgTotal'] = imgTotal_base64
                                        P_TransTot = 0

                                if P_TransDet or P_TransOffline or P_TransDark:
                                        imgDetail_base64 = ''
                                        with open(FileImgTotal, 'rb') as image_file:
                                                imgDetail_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                                        requestData['imgDetail'] = imgDetail_base64
                                        P_TransDet = 0
                                
                                requestData['status'] = {
                                        'system' : {
                                                'swVersion': SDCStatus.SWVersion,
                                                'captureTime': SDCStatus.ImgUTC,
                                                'captureLat': SDCStatus.ImgLAT,
                                                'cpuTemperature': SDCStatus.CPUTemp,
                                                'cameraTemperature': SDCStatus.CamTemp,
                                                'outcaseTemperature': SDCStatus.OutTemp 
                                        },
                                        'dial' : {
                                                'brightness': SDCStatus.IMGBright,
                                                'sunny': SDCStatus.Sunny,
                                                'cloudy': SDCStatus.Cloudy,
                                                'night': SDCStatus.Night
                                        }
                                }
                                
                                try:
                                        key = ''
                                        # In Header
                                        route = 'http://localhost:7071/api/transfer-images/%s' % key
                                        headers = {'x-functions-key': 'xxx'}
                                        response = requests.post(route, json=requestData, headers=headers)
                                        responseData = response.json()['data']

                                        SDCRemote.CamOffLine = responseData['command']['camOffline']
                                        SDCRemote.PerodM = responseData['command']['periodM']
                                        SDCRemote.Series = responseData['command']['series']
                                        SDCRemote.ZoomMove = responseData['command']['zoomMove']
                                        SDCRemote.ZoomDrawRect = responseData['command']['zoomDrawRect']
                                        SDCRemote.ZoomCentPercX = responseData['detail']['zoomCentPercX']
                                        SDCRemote.ZoomCentPercY = responseData['detail']['zoomCentPercY']
                                        sdcfun.WriteRemote(FileRemoteCmdCfg, SDCRemote)

                                        P_TransCmd = 1
                                except:
                                        logging.debug( 'error getting reponse' )
                                        P_TransCmd = 0

                                TicksAct = time.time()
                                OPDelayS = int( TicksAct - TicksCap )
                                if ( OPDelayS > OPDelayMax ):
                                        logging.warning( 'Exceeded expected runtime - OPDelayS %i sec', OPDelayS )
                                logging.debug( 'End image transfer' )

                        logging.debug( 'End period' )

                        #Read operating parameter
                        if P_TransCmd:
                                try:
                                        text = ( 'Before fetch remotecmd.cfg: SDCRemote.Series {a}' ).format( a = SDCRemote.Series )
                                        print( text )
                                        SDCRemote = sdcfun.GetRemote( FileRemoteCmdCfg )
                                        text = ( 'Got remotecmd.cfg: SDCRemote.Series {a}' ).format( a = SDCRemote.Series )
                                        print( text )
                                except:
                                        P_TransCmd = 0
                                        print( 'No fetch remotecmd.cfg' )
                        SDCRun = sdcfun.GetParameter( FileStationCfg, SDCCam )
                        if P_TransCmd:
                                if SDCRun.RemoteCMD:
                                        SDCCam.ZoomCentPercX = SDCRemote.ZoomCentPercX
                                        SDCCam.ZoomCentPercY = SDCRemote.ZoomCentPercY
                                        SDCRun.PeriodM = SDCRemote.PeriodM
                                        sdcfun.WriteParameter( FileStationCfg, SDCCam, SDCRun, 0 )
                        if (not( SDCRun.RemoteCMD ) and SDCRun.ZoomMove) or (SDCRun.RemoteCMD and SDCRemote.ZoomMove):
                                SDCCam.AdjustZoomParameterset( time.time() )
                        SDCCam.AdjustParameterset()
                        PeriodS = SDCRun.AdjustPeriod( SDCRun.PeriodM )
                        print( 'Period new: ', PeriodS, 'sec' )

                        #Store camera status and actual image
                        if( (not( SDCRun.RemoteCMD ) and SDCRun.Series ) or ( SDCRun.RemoteCMD and SDCRemote.Series ) ):
                                try:
                                        sdcfun2.LogStatus( time.time(), SDCStatus.CPUTemp, SDCStatus.CamTemp, SDCStatus.OutTemp, str( SDCStatus.IMGBright ) )
                                        if( SDCStatus.Night == 0 ):
                                            ImgPathName = strftime( 'images%j', gmtime( TicksIm ) )
                                            if not os.path.isdir( ImgPathName ):
                                                    os.system( 'sudo mkdir ' + ImgPathName )
                                            ImgFileName = strftime( ImgPathName + '/img%j%H%M%S.jpg', gmtime( TicksIm ) )
                                            os.system( 'sudo cp ' + FileImgTotal + ' ' + ImgFileName )
                                except:
                                        print( 'Store status or copy images failed' )
                                        logging.warning( 'Store status or copy images failed' )

                        #Prepare wait for the next time slot
                        TicksAct = time.time()
                        ActUTC = datetime.utcfromtimestamp( TicksAct )
                        Now = time.localtime( TicksAct )
                        NowS = int( time.strftime( "%S", Now ) ) % 30

#                        ActUTC   = datetime.combine( datetime.today(), datetime.strptime( '11:16:35', '%H:%M:%S').time() )
                        #While near noon (+/-0.25 h) capture/transfer images more frequent
                        noonTicks = NoonUTC.timestamp()
                        nextCapt = datetime.fromtimestamp( ActUTC.timestamp() + PeriodS )
                        quarterHS = 15 * 60
                        noon1UTC = datetime.fromtimestamp( noonTicks - quarterHS )
                        noon2UTC = datetime.fromtimestamp( noonTicks + quarterHS )
                        WaitNearNoonS = NoonUTC.timestamp() - quarterHS - ActUTC.timestamp()
                        if ( nextCapt > noon1UTC and ActUTC < noon2UTC ):
                                if WaitNearNoonS > SDCRun.AdjustPeriod( 0 ):
                                        PeriodS = WaitNearNoonS
                                else:
                                        PeriodS = SDCRun.AdjustPeriod( 0 )

                        #When after sunset prepare finish
                        if ( ActUTC > SunSetUTC and SDCStatus.Night == 1 and P_TransDark == 0 ):
                                AfterSunset = 1
                                print( 'After Sunset' )
                                break
                        else:
                                print( 'Before Sunset' )

                        #Wait until next capture time approaching
                        if ( PeriodS - NowS ) > 10:
                                #print( 'Sleeping ', PeriodS - int( NowS2 / 2 ) - 10, 'sec' )
                                time.sleep( PeriodS - NowS - 10 )

                except KeyboardInterrupt:
                        InPeriod = 0
                pass

        Cam.close()
        ActTime = time.asctime( time.localtime( TicksAct ) )
        if ( AfterSunset ):
                sdcfun2.DoAfterSunset()
                print( 'Finishing by sunset ........', ActTime )
                logging.info( 'End by sunset reached ---------------------' )
                os.system( 'sudo halt' )
        else:
                print( 'Finishing by user <ctrl-C> .', ActTime )
                logging.info( 'End by user <ctrl-C> ----------------------' )

if __name__ == "__main__":
        main( sys.argv[1:] )
