# -*- coding: utf-8 -*-
#!/usr/bin/python
# Python 2.7 code to analyze sound and interface with ASUS G20

"""
Created on Sat Sep 26 11:22:57 2015
@author: William Herrera

IMPORTANT: run as administrator

Module for calls to the ASUS G20aj ACPIWMI.dll library to manipulate
the G20aj LEG lighting displays.

The ASUS ACPI and dll's were analyzed by William Hererra, 2015
"""

from ctypes import windll, create_string_buffer
import os
from time import sleep

# A convenient directory context management from stack overflow posting
class ChangeDir(object): #pylint: disable-msg=C0103, R0903
    """
    Context manager for changing the current working directory
    """
    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)
        self.saved_path = "."

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)

##########################################################################
#   The byte code for each light on the ASUS G20 desktop's LED lighting:
#   left vertical light:   0xc00e0000
#   right vertical light:  0xc00d0000
#   base horizontal light: 0xc00f0000
##########################################################################

RIGHT_VERTICAL = 0xc00d0000
LEFT_VERTICAL = 0xc00e0000
BASE_HORIZONTAL = 0xc00c0000

"""
The position of color in second argument 4 byte integer:
red   0x00ff0000
green 0x0000ff00
blue  0x000000ff
Note that other colors use a mix of this type of RGB color coding.
"""

# might not always be this
DPATH = '/Program Files (x86)/ASUS/ASUS Manager/Lighting'

class ASUSLighting(object): #pylint: disable-msg=C0103
    """
    Class to set ASUS G20aj lighting colors
    """
    def __init__(self, dll_path, light_position):
        self.dll_path = dll_path
        self.lpos = light_position
        self.color = self.get_color()

    def get_color(self):
        """
        Get current color of the LED light
        FIXME-- not working atm
        """
        with ChangeDir(self.dll_path):
            dhand = windll.ACPIWMI.AsWMI_Open()
            buf = create_string_buffer('abcdefg')
            windll.ACPIWMI.AsWMI_GetDeviceStatus(dhand, repr(buf.raw))

    def set_color(self, color):
        """
        Set color of the LED light as a 4-byte integer
        The color is of form hex 0x00rrggbb, where rr id red, gg green,
          and bb the blue values of an RGB coded color
        Black is 0, white is 0x00ffffff
        """
        with ChangeDir(self.dll_path):
            windll.ACPIWMI.AsWMI_DeviceControl(self.lpos, color)

    def set_rgb(self, reds, greens, blues):
        """
        Set RGB color as separate red, green, and blue values
        """
        rgb_color = blues + (greens * 0x100) + (reds * 0x10000)
        self.set_color(rgb_color)


if __name__ == '__main__':
    RLIGHT = ASUSLighting(DPATH, RIGHT_VERTICAL)
    LLIGHT = ASUSLighting(DPATH, LEFT_VERTICAL)
    BLIGHT = ASUSLighting(DPATH, BASE_HORIZONTAL)

    print "Changing left vertical LED's to red"
    LLIGHT.set_rgb(255, 0, 0)
    sleep(2)

    print "Changing right vertical LED's to white"
    RLIGHT.set_rgb(255, 255, 255)
    sleep(2)

    print "Changing base horizontal LED's to blue"
    BLIGHT.set_rgb(0, 0, 255)
