# -*- coding: utf-8 -*-
#!/usr/bin/python

"""
Created on Sat Sep 26 11:22:57 2015
@author: William Herrera

Python 2.7 code to analyze sound and use as interface with ASUS G20 lighting
Tk widgets GUI version

IMPORTANT: run as administrator

"""

import os
import threading
import light_acpi as la
import asus_soundlighting as asl

import Tkinter as tki
import tkFileDialog as tkfd

DLLNAME = 'ACPIWMI.dll'
def correct_dll_path(pathdir):
    """
    check that we have the right path to the dll
    """
    return os.path.isfile(os.path.join(pathdir, DLLNAME))


class SoundLightApp(tki.Frame):
    """
    app for the gui
    """
    def __init__(self, root):

        self.root = root
        tki.Frame.__init__(self, root)
        tki.Label(root, text="ASUS G20aj Audio Lighting Control").pack()

        # choose audio input device via radio button
        num_devices, aud_dict = asl.list_devices(do_print=False)
        self.audio_devnum = tki.IntVar()
        for device_num, device_text in aud_dict.iteritems():
            rbut = tki.Radiobutton(root,
                                   text=device_text,
                                   indicatoron=0,
                                   padx=20,
                                   variable=self.audio_devnum,
                                   command=self.get_audio_source,
                                   value=device_num)
            rbut.pack()
            if device_text.find("Mix"):
                rbut.select()

        # choose directory to the ACPIWMI.dll
        self.path_to_dll = la.DPATH
        self.dir_opts = {}
        self.dir_opts['initialdir'] = la.DPATH
        self.dir_opts['mustexist'] = True
        self.dir_opts['title'] = 'Choose path to ACPIWMI.dll'
        tki.Button(self, text='DLL Path', command=tkfd.askdirectory).pack()

        # choose the lighting color update interval
        self.chunk_exponent = 15
        self.slider = tki.Scale(root,
                                from_=12, to=18,
                                tickinterval=1,
                                orient=tki.HORIZONTAL)
        self.slider.set(0.5)
        self.slider.pack()

        # start app button
        start_button = tki.Button(root,
                                  text="Start", fg="green",
                                  command=self.audio_to_lighting)
        start_button.pack()

        # quit app button
        quit_button = tki.Button(root,
                                 text="QUIT", fg="red",
                                 command=self.quit_app)
        quit_button.pack(side=tki.BOTTOM)

    def choose_dll_path(self):
        """
        choose path to dll
        """
        self.path_to_dll = tkfd.askdirectory(**self.dir_opts)
        return self.path_to_dll

    def get_audio_source(self):
        """
        get number for audio source
        """
        return self.audio_devnum

    def get_update_frequency(self):
        """
        update interval in increments of 0.25 sec
        """
        self.chunk_exponent = self.slider.get()
        return self.chunk_exponent

    def audio_to_lighting(self):
        """
        begin sampling display thread
        """
        def callback():
            """
            threaded function
            """
            asl.asus_soundlight(do_print=False)
        thrd = threading.Thread(target=callback)
        thrd.start()

    def quit_app(self):
        """
        End execution of app
        """
        self.root.destroy()


if __name__ == '__main__':
    ROOT = tki.Tk()
    APP = SoundLightApp(ROOT)
    ROOT.mainloop()

