#!/usr/bin/python

###
###  @brief  Script for accessing the display's backlight
###

import RPi.GPIO as GPIO

# Configuration
backlight_channel = 16

# Function for accessing the backlight
def init():
        # Adviced by the library...
        GPIO.setwarnings( False )

        GPIO.setmode( GPIO.BCM )
        GPIO.setup( backlight_channel, GPIO.OUT )

def enable():
        init()
        GPIO.output( backlight_channel, GPIO.HIGH )

def disable():
        init()
        GPIO.output( backlight_channel, GPIO.LOW )

# If the script is executed directly...
if __name__ == '__main__':
        import sys

        en = None
        if len(sys.argv) == 2:
                if sys.argv[1] == 'on':
                        en = True
                elif sys.argv[1] == 'off':
                        en = False

        if en is None:
                print( 'Usage: %s <state>' )
                print( '' )
                print( 'Parameters:' )
                print( '  state: Either "on" or "off" to enable/disable the backlight' )
                print( '' )
                sys.exit( 1 )

        if en:
                enable()
        else:
                disable()
