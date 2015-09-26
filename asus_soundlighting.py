# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 11:22:57 2015

@author: William
"""
#!/usr/bin/python
# Python 2.7 code to analyze sound and interface with ASUS G20

# IMPORTANT: run as administrator

import pyaudio
import numpy
import struct

import light_acpi as lacpi

MAX = 0
SEGMENTS = 9

def list_devices():
    """
    List all audio input devices
    """
    paud = pyaudio.PyAudio()
    i = 0
    ndev = paud.get_device_count()
    while i < ndev:
        dev = paud.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print str(i)+'. '+dev['name']
        i += 1

def asus_soundlight():
    """
    Get sound samples and adjust LED light color accordingly
    """
    # Change chunk if too fast/slow, never less than 2**13
    chunk = 2**15
    samplerate = 44100

    # CHANGE THIS TO CORRECT INPUT DEVICE
    # Look at recording devices and right click to show hidden devices,
    # and enable the mixing device. Enabling stereo mixing in your
    # sound card will make your sound output an input.
    # Use list_devices() to list all your input devices
    # and choose the mixed device as input device below
    device = 2

    paud = pyaudio.PyAudio()
    stream = paud.open(format=pyaudio.paInt16,
                       channels=2,
                       rate=samplerate,
                       input=True,
                       frames_per_buffer=chunk,
                       input_device_index=device)

    print "Starting, use Ctrl+C to stop"
    try:
        l_lighting = lacpi.ASUS_ACPI_lighting(lacpi.dpath, lacpi.LEFT_VERTICAL)
        r_lighting = lacpi.ASUS_ACPI_lighting(lacpi.dpath, lacpi.RIGHT_VERTICAL)
        b_lighting = lacpi.ASUS_ACPI_lighting(lacpi.dpath, lacpi.BASE_HORIZONTAL)

        while True:
            try:
                data = stream.read(chunk)
            except IOError:
                pass
            # Do FFT
            levels = calculate_levels(data, samplerate)
            # Make all levels to be between 0 and 255
            l_max = max(levels)
            l_min = min(levels)
            mult = 255 / (l_max - l_min)
            for idx in range(0, SEGMENTS):
                levels[idx] = int(round((levels[idx] - l_min) * mult))

            # set ASUS G20aj lighting colors
            b_lighting.set_rgb(levels[0], levels[1], levels[2])
            r_lighting.set_rgb(levels[3], levels[4], levels[5])
            l_lighting.set_rgb(levels[6], levels[7], levels[8])


    except KeyboardInterrupt:
        pass

    finally:
        print "\nStopping"
        stream.close()
        paud.terminate()

def smooth_window(fftx, ffty, degree=10):
    """
    Smooth the fft data
    """
    lxdata, lydata = fftx[degree:-degree], []
    for i in range(degree, len(ffty)-degree):
        lydata.append(sum(ffty[i-degree:i+degree]))
    return [lxdata, lydata]

def detrend(fftx, ffty, degree=10):
    """
    Detrend the fft data
    """
    lxdata, lydata = fftx[degree:-degree], []
    for i in range(degree, len(ffty)-degree):
        lydata.append(ffty[i] - sum(ffty[i-degree:i+degree])/(degree*2))
    return [lxdata, lydata]

def calculate_levels(data, samplerate):
    """
    Use FFT to calculate volume for each frequency range segment
    """

    # Convert raw sound data to Numpy array
    fmt = "%dH"%(len(data)/2)
    data2 = struct.unpack(fmt, data)
    data2 = numpy.array(data2, dtype='h')

    # Apply FFT
    fourier = numpy.fft.fft(data2)
    ffty = numpy.abs(fourier[0:len(fourier)/2])/1000
    fftx = numpy.fft.rfftfreq(len(data)/2, 1.0/samplerate)
    fftx = fftx[0:len(fftx)/4]
    ffty1 = ffty[:len(ffty)/2]
    ffty2 = ffty[len(ffty)/2::]+2
    ffty2 = ffty2[::-1]
    ffty = ffty1+ffty2
    ffty = numpy.log(ffty)-2

    fftx, ffty = detrend(fftx, ffty, 30)
    fftx, ffty = smooth_window(fftx, ffty, 10)
    fftx, ffty = detrend(fftx, ffty, 10)

    fourier = list(ffty)[4:-4]
    fourier = fourier[:len(fourier)/2]

    size = len(fourier)

    # Add up for SEGMENTS light codes
    levels = [sum(fourier[i:(i+size/SEGMENTS)]) for i in xrange(0, size, size/SEGMENTS)][:SEGMENTS]
    return levels

if __name__ == '__main__':
    list_devices()
    asus_soundlight()

