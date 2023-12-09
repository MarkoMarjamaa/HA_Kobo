# HA_Kobo
Kobo Touch N905B running as Home Assistant Dashboard

## 1. Prevent direct internet access because otherwise Kobo is pushing new firmware
I removed my router from internet, booted Kobo and gave it Wifi access. Then gave it fixed IP and blocked it from internet. Then connected router back. Kobo now has access only in my home network. ( Do not plug the internet back before you are certain Kobo is blocked from it) 

## 2. Install KoboWM image

```
Image file: https://www.dropbox.com/s/2hql5f651xhz8cx/kobowm.zip?dl=1
Github: https://github.com/pasqu4le/kobowm
```
At first, take backup from your current internal Kobo SD card. 
Open KoboWM image with hex editor like HxD and copy the part 000080000 - 00008006F from your Kobo image to KoboWM image. That part tells what kind of hardware your Kobo has. 
KoboWM image was created for N905C but it works with other versions, like my B905B, when that part is copied. 
Write new image to SD. The SD should be at least 16GB. 

## 3. Setting wifi
Ýou can't set wifi if you don't have internet access, because Kobo wants to have access to it's site. 
So I mounted SD to my PC via usb reader, started Ubuntu in Virtualbox, mounted USB reader to VirtualBox and mounted the disks to linux. 
```
vi /debian/etc/wpa_supplicant/wpa_supplicant.conf
```
```
ctrl_interface=/var/run/wpa_supplicant
update_config=1

network={
        ssid="MyWifi"
        psk="MyWifiPassword"
}
```

Of course, change MyWifi and MyWifiPassword.
You can hash the password with 
```
wpa_passphrase YOUR_SSID YOUR_PASSWORD
```
and add the result without quotes to psk. 

## 4. Boot Kobo and select KoboWM from start screen( the left icon).
Press wifi button in KoboWM and you should have working Wifi and SSH. 
User is marek, password abc123 by default.

## 5. Setting up proxy http server
Because Kobo does not have direct internet access, you have to set up http proxy in another server.
I used Privoxy. 
```
vi /etc/privoxy/config
```
```
listen-address  your_proxy:8118
```
your_proxy is the ip of the server you installed Privoxy. You can test if the proxy works with for instance Firefox. 

## 6. Update repositories
Repositories are now archived, so update sources file.
```
sudo vi /etc/apt/sources.list
```
```
deb http://archive.debian.org/debian/ jessie main non-free contrib
#deb http://ftp.us.debian.org/debian jessie main
```

Update the repositories through proxy:
```
sudo http_proxy=http://your_proxy:8118 apt-get update
```
Now you can update and install software for instance:
```
sudo http_proxy=http://your_proxy:8118 apt-get install sofware-package
```
or with pip/pip3:
```
sudo pip3 --proxy your_proxy:8118 install paho-mqtt
```

( You could also set http_proxy in .profile but I'm paranoid and don't want any other software to use proxy ) 

## 7. Updating the clock
My Kobo's clock returns always back to year 2011 when rebooted, and NTP only works when Wifi is on.

At first I set the right timezone
```
sudo ln -s /usr/share/zoneinfo/Europe/Helsinki /etc/localtime
```

Install ntpdate
```
sudo http_proxy=http://your_proxy:8118 apt-get install ntpdate
```

I can use my home automation server as time server.
```
sudo ntpdate homeautomation
```
This should update datetime manually. Every linux running NTP can be used as time server. 
I allow my network user my home automation server as NTP server by setting in it's ntp.conf.
```
restrict 192.168.1.0 mask 255.255.255.0
```

Set it to run every time wifi is started. 
```
vi /home/marek/scripts/wifi/start
```
end of file: 
```
    python /home/marek/kobowm/notifzmq.py "Wifi" "IP: $(sudo ifconfig eth0 | grep -o -E '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1)" 5000
    sudo ntpdate your_ntp_server  <-- insert this line with your NTP server
    exit
```

## 8. Install HA_Kobo
copy HA_Kobo directory under /home/marek.

Install apt&python packages.
```
sudo http_proxy=http://your_proxy:8118 apt-get install python3-tk
sudo pip3 --proxy your_proxy:8118 install paho-mqtt
```

( you might need some more so sorry...can't remember what I installed )

Test run: 
```
cd /home/marek/HA_Kobo
python3 HA_Kobo.py
```

Because you have no data in MQTT yet, only decent data you get is datetimes. 

Always close the program with KoboWMs button X !

## 9. Integrate HA_Kobo to KoboWM

We'll hijack the sdcard button for HA_Kobo

```
mv /home/marek/scripts/sdcard/toggle /home/marek/scripts/sdcard/toggle.old
cp /home/marek/HA_Kobo/sdcard_toggle /home/marek/scripts/sdcard/toggle
chmod 755 /home/marek/scripts/sdcard/toggle

mv /home/marek/kobowm/icons/media-floppy-symbolic.symbolic.png /home/marek/kobowm/icons/media-floppy-symbolic.symbolic.png.old
cp /home/marek/HA_Kobo/ha_icon.png /home/marek/kobowm/icons/media-floppy-symbolic.symbolic.png
```

Now reboot and you'll have new HA button to start HA_Kobo. 
