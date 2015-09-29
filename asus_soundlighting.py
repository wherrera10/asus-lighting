# -*- coding: utf-8 -*-
#!/usr/bin/python

"""
Created on Sat Sep 26 11:22:57 2015
@author: William Herrera

Python 2.7 code to analyze sound and use as interface with ASUS G20 lighting

IMPORTANT: run as administrator

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

            # Make all levels to be between 0 and 255
            l_max = max(levels)
            l_min = min(levels)
            if l_min != l_max:
                mult = 255 / (l_max - l_min)
            else:
                mult = 1
            for idx in range(0, SEGMENTS):
                levels[idx] = int(round((levels[idx] - l_min) * mult))

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

SSET = [0.00075, 2.1, 27, 18, 12, 5.6, 3.0, 1.5, 0.8]

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
    norm_chunk = np_chunk / np_chunk.sum()
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


    # the numbers below are based on average music. Could be adjusted
    return [sum(abs(lowbass)) + SSET[0], sum(abs(midbass)) * SSET[1],
            sum(abs(higbass)) * SSET[2], sum(abs(lowmidr)) * SSET[3],
            sum(abs(midmidr)) * SSET[4], sum(abs(higmidr)) * SSET[5],
            sum(abs(lowtreb)) * SSET[6], sum(abs(midtreb)) * SSET[7],
            sum(abs(higtreb)) * SSET[8]]


if __name__ == '__main__':
    list_devices()
    asus_soundlight(do_print=True)

