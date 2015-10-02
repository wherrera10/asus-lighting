# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 23:45:43 2015

@author: William Herrera

IMPORTANT: run as administrator

Color coded clock for G20aj series

"""

import numpy as np
import time
import light_acpi as li

def make60colors():
    """
    60 colors in RGB
    """
    reds = [255, 242, 229, 216, 203, 190, 177, 164, 151, 138,
            126, 113, 100, 87, 74, 61, 48, 35, 21, 8,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 13, 26, 39, 52, 65, 78, 91, 104, 117,
            130, 143, 156, 169, 181, 194, 207, 220, 233, 246]

    greens = [0, 13, 26, 39, 52, 65, 78, 91, 104, 117,
              130, 143, 156, 169, 181, 194, 207, 220, 233, 246,
              255, 242, 229, 216, 203, 190, 177, 164, 151, 138,
              126, 113, 100, 87, 74, 61, 48, 35, 21, 8,
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    blues = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 13, 26, 39, 52, 65, 78, 91, 104, 117,
             130, 143, 156, 169, 181, 194, 207, 220, 233, 246,
             255, 242, 229, 216, 203, 190, 177, 164, 151, 138,
             126, 113, 100, 87, 74, 61, 48, 35, 21, 8]

    colors = np.zeros(60, dtype=np.int32)
    for idx in range(60):
        colors[idx] = blues[idx] + greens[idx] * 0x100 + reds[idx] * 0x10000

    return colors


def make24colors():
    """
    24 colors in RGB
    """
    reds = [255, 224, 192, 160, 128, 96, 64, 32,
            0, 0, 0, 0, 0, 0, 0, 0,
            32, 64, 96, 128, 160, 192, 224, 255]

    greens = [0, 32, 64, 96, 128, 160, 192, 224,
              255, 224, 192, 160, 128, 96, 64, 32,
              0, 0, 0, 0, 0, 0, 0, 0]

    blues = [0, 0, 0, 0, 0, 0, 0, 0,
             32, 64, 96, 128, 160, 192, 224, 255,
             224, 192, 160, 128, 96, 64, 32, 0]

    colors = np.zeros(24, dtype=np.int32)
    for idx in range(24):
        colors[idx] = blues[idx] + greens[idx] * 0x100 + reds[idx] * 0x10000

    return colors


def hrminsec_colors():
    """
    return intervals for hours, minutes, seconds in 24h time
    """
    hours = make24colors()
    minutes = make60colors()
    seconds = minutes
    return hours, minutes, seconds


def localtime_colors(chrs, cmins, csecs):
    """
    get localtime as colors
    """
    sltime = time.localtime()
    hrs = sltime[3]
    mins = sltime[4]
    secs = sltime[5]
    if secs > 59:
        secs = 59
    return chrs[hrs], pulsate_hour(cmins[mins], hrs, secs), csecs[secs]

OFF_SECS = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
def pulsate_hour(colr, hrs, secs):
    """
    modulate color every 30 sec of the minute based on 12 hr cycle clock
    """
    ret = colr
    if secs % 30 in OFF_SECS and int(hrs % 12) * 2 > secs % 30:
        red = int((colr & 0xff) * 0x10000)
        green = int((colr & 0xff0000) / 0x100)
        blue = int((colr & 0xff00) / 0x100)
        ret = red + green + blue
    return ret

if __name__ == '__main__':

    LLI = li.ASUSLighting(li.DPATH, li.LEFT_VERTICAL)
    RLI = li.ASUSLighting(li.DPATH, li.RIGHT_VERTICAL)
    BLI = li.ASUSLighting(li.DPATH, li.BASE_HORIZONTAL)
    CHRS, CMINS, CSECS = hrminsec_colors()

    while True:
        CBASE, CLEFT, CRIGHT = localtime_colors(CHRS, CMINS, CSECS)
        LLI.set_color(CLEFT)
        RLI.set_color(CRIGHT)
        BLI.set_color(CBASE)
        time.sleep(1)

