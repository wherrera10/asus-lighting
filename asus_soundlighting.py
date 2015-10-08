# -*- coding: utf-8 -*-
#!/usr/bin/python

"""
Created on Sat Sep 26 11:22:57 2015
@author: William Herrera

Python 2.7 code to analyze sound and use as interface with ASUS G20 lighting

IMPORTANT: run as administrator

Acknowledgements:

This file's code structure owes greatly to the following project:
    Juliana Pena's Arduino code at
    http://julip.co/2012/05/arduino-python-soundlight-spectrum/

"""

import pyaudio
import numpy
import matplotlib.mlab
import struct

import light_acpi as lacpi

MAX = 0
SEGMENTS = 9
CHUNK_EXPONENT = 15
DEVICE_NUMBER = 2

def list_devices(do_print=True):
    """
    List all audio input devices
    """
    paud = pyaudio.PyAudio()
    text = "Audio Device Options:\n"
    devs = {}
    i = 0
    ndev = paud.get_device_count()
    while i < ndev:
        dev = paud.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            dev_line = str(i) + '. ' + dev['name']
            devs[i] = dev_line
            text = text + dev_line + "\n"
        i += 1
    if do_print:
        print text
    return ndev, devs

def asus_soundlight(do_print=True):
    """
    Get sound samples and adjust LED light color accordingly
    """
    # Change chunk if too fast/slow, never less than 2**13
    chunk = 2**CHUNK_EXPONENT
    samplerate = 44100

    # CHANGE THIS TO CORRECT INPUT DEVICE
    # Look at recording devices and right click to show hidden devices,
    # and enable the mixing device. Enabling stereo mixing in your
    # sound card will make your sound output an input.
    # Use list_devices() to list all your input devices
    # and choose the mixed device as input device below
    device = DEVICE_NUMBER

    paud = pyaudio.PyAudio()
    stream = paud.open(format=pyaudio.paInt16,
                       channels=2,
                       rate=samplerate,
                       input=True,
                       frames_per_buffer=chunk,
                       input_device_index=device)

    if do_print:
        print "Starting, use Ctrl+C to stop"
    try:
        l_lighting = lacpi.ASUSLighting(lacpi.DPATH, lacpi.LEFT_VERTICAL)
        r_lighting = lacpi.ASUSLighting(lacpi.DPATH, lacpi.RIGHT_VERTICAL)
        b_lighting = lacpi.ASUSLighting(lacpi.DPATH, lacpi.BASE_HORIZONTAL)

        while True:
            try:
                data = stream.read(chunk)
            except IOError:
                pass
            # Do FFT
            levels = get_cutouts(data, samplerate)

            # Make all levels to be <= 255
            l_max = max(levels)
            for idx in range(0, SEGMENTS):
                levels[idx] = int(round(levels[idx] * 255.0 / l_max))

            saturate_color(levels)

            # set ASUS G20aj lighting colors
            b_lighting.set_rgb(levels[0], levels[1], levels[2])
            r_lighting.set_rgb(levels[3], levels[4], levels[5])
            l_lighting.set_rgb(levels[6], levels[7], levels[8])


    except KeyboardInterrupt:
        pass

    finally:
        if do_print:
            print "\nStopping"
        stream.close()
        paud.terminate()

def sat_trip(cred, cgreen, cblue):
    """
    saturate rgb color
    """
    mult = 255.0 / (float(max(cred, cgreen, cblue))**4)
    return int(mult * float(cred) ** 4), \
           int(mult * float(cgreen) ** 4), \
           int(mult * float(cblue) ** 4)

def saturate_color(col):
    """
    saturate the colrs representing sound levels
    """
    if len(col) == 9:
        col[0], col[1], col[2] = sat_trip(col[0], col[1], col[2])
        col[3], col[4], col[5] = sat_trip(col[3], col[4], col[5])
        col[6], col[7], col[8] = sat_trip(col[6], col[7], col[8])
    return col

def equalize(levels, within_factor=3.0):
    """
    makes levels all within a factor of within of each other
    """
    new_levels = []
    largest = 0.0
    for idx in range(len(levels)):
        new_levels.append(numpy.abs(levels[idx]))
        if new_levels[idx] < 0.0001:
            new_levels[idx] = 0.0001
        largest = max(largest, new_levels[idx])

    least_allowed = largest / within_factor
    loops = 0
    for idx in range(len(new_levels)):
        while new_levels[idx] < least_allowed and loops < 100:
            loops += 1
            new_levels[idx] *= 2.0
    return new_levels


def get_cutouts(chunkdata, srate, nfft=512): #pylint: disable-msg=R0914
    """
    get a summed amplitude of power spectrum between low_cut and high-cut
    normalize this, then get amplitudes of specific frequency ranges
    that correspond to 3 intervals each in bass, midrange, and treble:

    20 Hz - 80 Hz = Low Bass
    80 Hz-160 Hz = Bass
    160 Hz - 320 Hz = Hi Bass
    320 Hz - 640 Hz = Low Mid Range
    640 Hz - 1280 Hz = Mid Mid range
    1280 Hz - 2560 Hz = High Midrange
    2560 Hz - 5120 Hz = Low Treble
    5120 Hz - 10240 Hz = Mid treble
    10240 Hz- 20480 Hz = High Treble
    """
    # Convert raw sound data to Numpy array
    fmt = "%dH"%(len(chunkdata)/2)
    unpackdata = struct.unpack(fmt, chunkdata)
    np_chunk = numpy.array(unpackdata, dtype='h')

    # normalize epoch and then psd
    sum_chunk = np_chunk.sum()
    if sum_chunk != 0:
        norm_chunk = np_chunk / sum_chunk
    else:
        norm_chunk = np_chunk
    pxx, freqs = matplotlib.mlab.psd(norm_chunk, NFFT=nfft, Fs=srate)

    lowbass = pxx[numpy.logical_and(freqs <= 80, freqs >= 20)]
    midbass = pxx[numpy.logical_and(freqs <= 160, freqs >= 80)]
    higbass = pxx[numpy.logical_and(freqs <= 320, freqs >= 160)]
    lowmidr = pxx[numpy.logical_and(freqs <= 640, freqs >= 320)]
    midmidr = pxx[numpy.logical_and(freqs <= 1280, freqs >= 640)]
    higmidr = pxx[numpy.logical_and(freqs <= 2560, freqs >= 1280)]
    lowtreb = pxx[numpy.logical_and(freqs <= 5120, freqs >= 2560)]
    midtreb = pxx[numpy.logical_and(freqs <= 10240, freqs >= 5120)]
    higtreb = pxx[numpy.logical_and(freqs <= 20480, freqs >= 10240)]

    sound_levels = [sum(lowbass), sum(midbass), sum(higbass),
                    sum(lowmidr), sum(midmidr), sum(higmidr),
                    sum(lowtreb), sum(midtreb), sum(higtreb)]

    return equalize(sound_levels)


if __name__ == '__main__':
    list_devices()
    asus_soundlight(do_print=True)

