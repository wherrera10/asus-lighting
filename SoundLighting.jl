# -*- coding: utf-8 -*-

#=
Created on Sat Sep 26 11:22:57 2015
@author: William Herrera

Julia v0.4 code to analyze sound and use as interface with ASUS G20 lighting

IMPORTANT: run as administrator

=#

using AudioIO
using DSP

include("LightACPI.jl")
using .LightACPI

MAX = 0
SEGMENTS = 9
CHUNK_EXPONENT = 15
LIGHT_ROTATION_INTERVAL = 0
DEVICE_NUMBER = 2

function list_devices(do_print=true)
    #=
    List all audio input devices
    =#
    devices = get_audio_devices()
    text = "Audio Device Options:\n"
    i = 1
    ndev = length(devices)
    devs = Array{ASCIIString}(ndev)
    for aud in devices
        if aud.max_input_channels > 0
                dev_line = string(i, ". ", aud.name)
            devs[i] = dev_line
            text = string(text, dev_line, "\n")
        end
        i += 1
    end
    if do_print
        print(text)
    end
    return ndev, devices
end


function asus_soundlight(do_print=true)
    #=
    Get sound samples and adjust LED light color accordingly
    =#
    # Change chunk if too fast/slow, never less than 2**13
    chunk = 2 ^ CHUNK_EXPONENT
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

    if do_print
        print("Starting, use Ctrl+C to stop")
    end
    l_lighting = lacpi.ASUSLighting(lacpi.DPATH, lacpi.LEFT_VERTICAL)
    r_lighting = lacpi.ASUSLighting(lacpi.DPATH, lacpi.RIGHT_VERTICAL)
    b_lighting = lacpi.ASUSLighting(lacpi.DPATH, lacpi.BASE_HORIZONTAL)

    do_rotate_interval = LIGHT_ROTATION_INTERVAL
    rotate_state = 0
    try
    while true
        data = stream.read(chunk)
        levels = summed_spectra(data, samplerate)

        # Make all levels to be <= 255
        l_max = max(levels)
        for idx in 1:SEGMENTS
            levels[idx] = int(round(levels[idx] * 255.0 / l_max))
        end
        if do_rotate_interval == 1
            rotate_state += 1
            rotate_state %= 3
            do_rotate_interval = LIGHT_ROTATION_INTERVAL
        end
        if do_rotate_interval > 0
            do_rotate_interval -= 1
            rotate_levels!(levels, rotate_state)
        end
        saturate_color!(levels)
        # set ASUS G20aj lighting colors
        b_lighting.set_rgb(levels[0], levels[1], levels[2])
        r_lighting.set_rgb(levels[3], levels[4], levels[5])
        l_lighting.set_rgb(levels[6], levels[7], levels[8])
    end
    finally
        if do_print
            print("\nStopping")
        end
        stream.close()
        paud.terminate()
    end
end

function rotate_levels!(seq, rtype)
    #=
    rotate around light postions colors
    =#
    if rtype == 1
        saveseq = seq[1:3]
        seq[1:3] = seq[6:9]
        seq[6:9] = seq[3:6]
        seq[3:6] = saveseq
    elseif rtype == 2
        saveseq = seq[1:3]
        seq[1:3] = seq[3:6]
        seq[3:6] = seq[6:9]
        seq[6:9] = saveseq
    end
    seq
end


function sat_trip(cred, cgreen, cblue)
    #=
    saturate rgb color
    =#
    mult = 255.0 / (float(max(cred, cgreen, cblue)) ^ 4)
    return int(mult * float(cred) ^ 4),
           int(mult * float(cgreen) ^ 4),
           int(mult * float(cblue) ^ 4)
end


function saturate_color!(col)
    #=
    saturate the colrs representing sound levels
    =#
    if len(col) == 9
        col[0], col[1], col[2] = sat_trip(col[0], col[1], col[2])
        col[3], col[4], col[5] = sat_trip(col[3], col[4], col[5])
        col[6], col[7], col[8] = sat_trip(col[6], col[7], col[8])
    end
    return col
end


function equalize(levels, within_factor=3.0)
    #=
    makes levels all within a factor of within of each other
    =#
    new_levels = deepcopy(levels)
    largest = 0.0
    for idx in 1:length(new_levels)
        if new_levels[idx] < 0.0001
            new_levels[idx] = 0.0001
        end
        largest = max(largest, new_levels[idx])
    end
    least_allowed = largest / within_factor
    loops = 0
    for idx in 1:length(new_levels)
        while new_levels[idx] < least_allowed && loops < 100
            loops += 1
            new_levels[idx] *= 2.0
        end
    end
    new_levels
end

function summed_spectra(chunkdata, srate, nfft=2048)
    #=
    from summed amplitude of power spectrum between low_cut and high-cut
    get amplitudes of specific frequency ranges that correspond to 
    3 intervals each in bass, midrange, and treble:

    20 Hz - 80 Hz = Low Bass
    80 Hz-160 Hz = Bass
    160 Hz - 320 Hz = Hi Bass
    320 Hz - 640 Hz = Low Mid Range
    640 Hz - 1280 Hz = Mid Mid range
    1280 Hz - 2560 Hz = High Midrange
    2560 Hz - 5120 Hz = Low Treble
    5120 Hz - 10240 Hz = Mid treble
    10240 Hz- 20480 Hz = High Treble
    =#
    # Convert raw sound data to doubles
    dchunk = unpack(chunkdata, T(length(chunkdata)/2, 
                                 align_packed, :NativeEndian))
    # normalize epoch and then psd
    sum_chunk = sum(dchunk)
    if sum_chunk != 0.0
        dchunk /= sum_chunk
    end
    pxx, freqs = welch_pgram(dchunk, onesided=true, nfft=nfft, fs=srate)
    # the low and mid bass is contaminated by psd edge artifact, so use
    # portions of high bass instead.
    lowbass = pxx[freqs <= 200 && freqs > 100]
    midbass = pxx[freqs <= 300 && freqs > 200]
    higbass = pxx[freqs <= 400 && freqs > 300]
    lowmidr = pxx[freqs <= 640 && freqs > 400]
    midmidr = pxx[freqs <= 1280 && freqs > 640]
    higmidr = pxx[freqs <= 2560 && freqs > 1280]
    # tweak to treble bands for better color changes during vocals
    lowtreb = pxx[freqs <= 7000 && freqs > 2560]
    midtreb = pxx[freqs <= 10240 && freqs > 7000]
    higtreb = pxx[freqs <= 20480 && freqs > 10240]

    sound_levels = [sum(lowbass), sum(midbass), sum(higbass),
                    sum(lowmidr), sum(midmidr), sum(higmidr),
                    sum(lowtreb), sum(midtreb), sum(higtreb)]

    return equalize(sound_levels)
end


list_devices()
asus_soundlight(true)

