# Case

A simple ply wood case for the **Kaffeekasse**

## Required Hardware

* [Raspberry Pi 3](https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus/)) (or later), ~40 Euro
* Touch-Display, e.g. [Waveshare 10.1inch](https://www.waveshare.com/10.1inch-HDMI-LCD-B-with-case.htm), ~100 Euro
* *optional:* Barcode Scanner, ~30 Euro
* *optional:* NFC Reader, e.g. [ACR122U](https://www.acs.com.hk/en/products/3/acr122u-usb-nfc-reader/), ~30 Euro
* Power Supply (5V / 5A)


## Case Construction

There exist two lasercut plans in *Scalable Vector Graphics*-Format for the Hardware mentioned above, using 4mm ply wood:

* [Case for wall mount](case-lastercut.svg)
* [Case with stand](case-lastercut.svg)


## Assembly

Since the display does not support a software solution to disable the backround LED, a transistor controlled via RPi GPIOs replaces the LED switch on the background.


## Software

* [Raspbian (Buster) Lite](https://www.raspberrypi.org/downloads/raspbian/) as base, boot it and update all packages
	```
	sudo apt update
	sudo apt dist-upgrade
	```
* Setup HDMI Display according to the [Waveshare Wiki](https://www.waveshare.com/wiki/10.1inch_HDMI_LCD_(B)_(with_case)): Add the following lines to `/boot/config.txt`
	```
	hdmi_group=2
	hdmi_mode=87
	hdmi_cvt 1280 800 60 6 0 0 0
	hdmi_drive=1
	display_rotate=2
	```
* For faster startup, change/add following lines in `/boot/config.txt`
	```
	disable_splash=1
	boot_delay=0
	dtoverlay=pi3-disable-bt
	```
* Install the [Chromium Browser](https://www.chromium.org/) and [LightDM](https://github.com/canonical/lightdm)
	```
	sudo apt install chromium-browser lightdm
	```
* Enable autostart of the browser in kiosk mode by copying the provided file [Xsession](Xsession) to `/home/pi/.Xsession` (mind the dot). Adjust the URL and monitor timeouts (30s) to your needs.
* To rotate touch input, copy the file [40-libinput.conf](40-libinput.conf) (originated from `/usr/share/X11/xorg.conf.d/40-libinput.conf`) to `/etc/X11/xorg.conf.d/40-libinput.conf`
* Setup booting directly into X via `sudo raspi-config` and establish your network connection
* Copy the provided files [backlight.sh](backlight.sh) to `/opt/backlight.sh` and [backlight.service](backlight.serivce) to `/etc/systemd/system/backlight.serivce`, reload *systemd* and enable the service to support LED backlight disabling during power saving
	```
	sudo systemctl daemon-reload 
	sudo systemctl enable backlight.service 
	sudo systemctl start backlight.service 
	```
* Reboot. You are good to go.