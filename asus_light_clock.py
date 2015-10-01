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

def sixty_colors(ncolors=60):
    """
    get 60 evenly spaced rbg colors
    """
    rgbs = np.zeros(ncolors, dtype=np.int32)
    idx = 0
    for colr in xrange(0, 0xffffff, int(0xffffff / ncolors)):
        rgbs[idx] = int(abs(colr))
        idx = idx + 1
        if idx >= ncolors:
            break
    return rgbs

def hrminsec_colors():
    """
    return intervals for hours, minutes, seconds in 24h time
    """
    hours = sixty_colors(24)
    minutes = sixty_colors(60)
    seconds = minutes
    return hours, minutes, seconds

def rotate_color_120_240(colr):
    """
    return color with two colors at 120 and 240 degrees from it on color wheel
    """
    bcol = colr & 0xff
    gcol = (colr / 0x100) & 0xff
    rcol = (colr / 0x10000) & 0xff
    col120 = (gcol * 0x10000) + (bcol * 0x100) + rcol
    col240 = (bcol * 0x10000) + (rcol * 0x100) + gcol
    return col120, col240

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
    return chrs[hrs], cmins[mins], csecs[secs]

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



