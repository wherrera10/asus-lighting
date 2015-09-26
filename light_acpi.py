# IMPORTANT:  run as administrator

from ctypes import windll, create_string_buffer
from enum import Enum
import os
from time import sleep

# A convenient directory context management from stack overflow posting
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
        
"""
The byte code for each light on the ASUS G20 desktop's LED lighting:
left vertical light:   0xc00e0000
right vertical light:  0xc00d0000
base horizontal light: 0xc00f0000
"""

RIGHT_VERTICAL  = 0xc00d0000
LEFT_VERTICAL   = 0xc00e0000
BASE_HORIZONTAL = 0xc00c0000

"""
The position of color in second argument 4 byte integer:
red   0x00ff0000
green 0x0000ff00
blue  0x000000ff
Note that other colors use a mix of this type of RGB color coding.
"""

# might not always be this
dpath = '/Program Files (x86)/ASUS/ASUS Manager/Lighting'

class ASUS_ACPI_lighting(object):
	def __init__(self, dll_path, light_position):
		self.dll_path = dll_path
		self.lpos = light_position
		self.color = self.get_color()

	def get_color(self):
		with cd(self.dll_path):
			dh = windll.ACPIWMI.AsWMI_Open()
			buf = create_string_buffer('abcdefg')
			result = windll.ACPIWMI.AsWMI_GetDeviceStatus(dh, repr(buf.raw))
			print buf.raw
	
	def set_color(self, color):
		with cd(self.dll_path):
			result = windll.ACPIWMI.AsWMI_DeviceControl(self.lpos, color)
	
	def set_rgb(self, reds, greens, blues):
		rgb_color = blues + (greens * 0x100) + (reds * 0x10000)
		self.set_color(rgb_color)


if __name__ == '__main__':
	r_lighting = ASUS_ACPI_lighting(dpath, RIGHT_VERTICAL)
	l_lighting = ASUS_ACPI_lighting(dpath, LEFT_VERTICAL)
	b_lighting = ASUS_ACPI_lighting(dpath, BASE_HORIZONTAL)

	print "Changing left vertical LED's to red"
	l_lighting.set_rgb(255, 0, 0)
	sleep(2)

	print "Changing right vertical LED's to white"
	r_lighting.set_rgb(255, 255, 255)
	sleep(2)

	print "Changing base horizontal LED's to blue"
	b_lighting.set_rgb(0, 0, 255)
