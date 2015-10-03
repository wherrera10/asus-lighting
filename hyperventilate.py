# -*- coding: utf-8 -*-
"""
Created on Fri Oct 02 14:39:39 2015

@author: William Herrera

IMPORTANT: run as administrator

Color breathing package for G20aj series PC

"""

import light_acpi as la
from time import sleep

def make_rgb(cred, cgreen, cblue):
    """
    make rgb for components
    """
    redval = int(round(cred))
    greenval = int(round(cgreen))
    blueval = int(round(cblue))
    ret = int(redval * 0x10000 + greenval * 0x100 + blueval)
    if ret < 0:
        ret = 0
    if ret > 0x00ffffff:
        ret = 0x00ffffff
    return ret

def split_rgb(color):
    """
    split rgb into red, green, blue
    """
    red = (color & 0xff0000) / 0x10000
    green = (color & 0xff00) / 0x100
    blue = color & 0xff
    return red, green, blue

def make_ratios(cred, cgreen, cblue):
    """
    get ratios of colors
    """
    maxcolor = max(cred, cgreen, cblue)
    return float(cred)/float(maxcolor), \
           float(cgreen)/float(maxcolor), \
           float(cblue)/float(maxcolor)

def make_gamut(color):
    """
    make a sequence of 256 colors
    """
    sequence256 = []
    cred, cgreen, cblue = split_rgb(color)
    rred, rgreen, rblue = make_ratios(cred, cgreen, cblue)
    for step in range(256):
        tred = float(step) * rred
        tgreen = float(step) * rgreen
        tblue = float(step) * rblue
        sequence256.append(make_rgb(tred, tgreen, tblue))

    return sequence256, sequence256.index(color)


def dim_up_down_up_sequence(gamut, idex, frames):
    """
    up color intensity to full
    """
    # initial compiled list is size 512
    cseq = gamut[idex:] + gamut[::-1] + gamut[0:idex]
    # adjust size
    reframed = []
    ratio = 512.0 / frames
    for frameidx in range(frames):
        gamut_pos = int(round(frameidx * ratio))
        reframed.append(cseq[gamut_pos])
    return reframed


def run_color_sequence(lighting, colors, sleepinterval):
    """
    run a breathing type change sequence through once
    sleepinterval is in seconds or fractions of seconds
    """
    for colr in colors:
        lighting.set_color(colr)
        sleep(sleepinterval)

def continuous_cycle(lighti, startcolor, frames=32, sleepinterval=0.1):
    """
    breathe in color saturation
    """
    gam, orig_idx = make_gamut(startcolor)
    seq = dim_up_down_up_sequence(gam, orig_idx, frames)
    while True:
        run_color_sequence(lighti, seq, sleepinterval)

def run_triple_sequence(lightlist, colorlist, sleeptime):
    """
    do all 3 lights given list of all 3
    """
    lli = lightlist[0]
    rli = lightlist[1]
    bli = lightlist[2]
    lcol = colorlist[0]
    rcol = colorlist[1]
    bcol = colorlist[2]

    for idx in range(len(lcol)):
        lli.set_color(lcol[idx])
        rli.set_color(rcol[idx])
        bli.set_color(bcol[idx])
        sleep(sleeptime)


def all_cycle(scolors, frames=32, sleepinterval=0.1):
    """
    all LED lighting do continuous cycle breathing
    """
    # make light and color lists
    lights = [la.ASUSLighting(la.DPATH, la.LEFT_VERTICAL), \
              la.ASUSLighting(la.DPATH, la.RIGHT_VERTICAL), \
              la.ASUSLighting(la.DPATH, la.BASE_HORIZONTAL)]
    clists = []
    for idx in range(len(lights)):
        gam, orig_idx = make_gamut(scolors[idx])
        seq = dim_up_down_up_sequence(gam, orig_idx, frames)
        clists.append(seq)

    while True:
        run_triple_sequence(lights, clists, sleepinterval)



if __name__ == '__main__':
    SCOL = 0x1111ff
    LLIGHT = la.ASUSLighting(la.DPATH, la.LEFT_VERTICAL)
    continuous_cycle(LLIGHT, SCOL)




