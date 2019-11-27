#!/bin/bash

export XAUTHORITY=/home/pi/.Xauthority
export DISPLAY=:0
MONITOR_ACTIVE=false

while true; do
	if xset -q | grep "Monitor is On" >/dev/null 2>&1 ; then
		if [ "$MONITOR_ACTIVE" != true ]; then
			MONITOR_ACTIVE=true
			#echo Monitor just switched on
			xset led named "Scroll Lock"
		fi
	else
		if [ "$MONITOR_ACTIVE" = true ]; then
			MONITOR_ACTIVE=false
			#echo Monitor just switched off
			xset -led named "Scroll Lock"
		fi
	fi
	sleep 1
done
