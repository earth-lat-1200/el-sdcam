The subdirectory `/script` contains the source- and examples of configuration-files running the Raspi (Zero, Pi 3, Pi 4) with Cam and T-sensors.

**See also:** The document `Sdcam/Setup_Sdcam_Raspi_V6.pdf` within the root directory for further details. This document describes the setup of the *ready to go Raspi* (delivery status, components, WLAN-setup, modification of parameters). Especially the meaning and values of all parameters are given.

## Preconditions for proper usage of these Python scripts:
You may use your Raspi:
1) headless via WLAN (you have to know the name/IP of the Raspi and it has to be connected via proper SSID/password), using PuTTY or WinSCP, or VNC, or
2) with keyboard/HDMI-monitor attached.
### *Later on here there will be hints about the tested Raspian OS*
### Python3, picamera- and PIL-libraries (Cam V1 or V2 or similar)
```
  sudo apt-get install python3-picamera
  sudo apt-get install python3-pil
```
### W1Thermsensor (DS 1822)
```
sudo apt-get install python3-w1thermsensor
```
### Mount a RAM-disk
make a new directory
```
sudo mkdir /mnt/ramdisk
```
edit fstab-table at the end:
```
sudo nano /etc/fstab
  tmpfs /mnt/ramdisk tmpfs nodev,nosuid,size=50M 0 0
```
reboot and check for success
```
sudo reboot
df -h
```
### Store the scripts to the working directory
```
e.g. /home/pi/Sdcam
sundial.py, sdfun.py, sdfun2.py
```
## Now you can operate Sdcam manually
```
e.g. /home/pi/Sdcam
sudo python3 sundial.py
```
* New parameter files will be created with dummy values
* You will get error messages if preconditions fail
* The running sundialcam.py script is stopped by `ctrl-c`
* You can check new .log files at the working directory
* Modify parameter files with your data (e.g. FTP access, crop/zoom positions/sizes, etc.)
If everything looks OK continue for automated startup as followes:
### Create launcher file to start Sdcam after boot
At the same working directory create `launcher.sh`
```
e.g. /home/pi/Sdcam
sudo nano launcher.sh
```
Entering this code
```
  #!/bin/sh
  # launcher.sh
  cd /
  cd home/pi/Sdcam
  sudo python3 sundialcam.py &
```
Make the launcher file executable
```
sudo chmod 755 launcher.sh
```
### Make crontab usage
```
sudo chmod 755 launcher.sh
```
Create a log-file directory at the working directory for the crontab output
```
sudo mkdir log
```
Create a crontab entry for automatic running sdcam-launcher after boot
```
cd /
sudo crontab -e
```
Entering this statement at the end of the crontab file
```
  @reboot sh /home/pi/Sdcam/launcher.sh >/home/pi/Sdcam/log/cronlog 2>&1
```
## Finally check the operation with reboot
* See what happens
* Check crontab log
* Check Sdcam.log.
