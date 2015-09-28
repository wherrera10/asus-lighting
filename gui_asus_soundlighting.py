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
import ctypes
import threading

import Tkinter as tki
import tkFileDialog as tkfd
import tkMessageBox as mbox

import light_acpi as la
import asus_soundlighting as asl

DLLNAME = 'ACPIWMI.dll'
def correct_dll_path(pathdir):
    """
    check that we have the right path to the dll
    """
    return os.path.isfile(os.path.join(pathdir, DLLNAME))

def terminate_thread(thread):
    """
    Terminates a python thread from another thread.
    :param thread: a threading.Thread instance
    """
    if not thread.isAlive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

class SoundLightApp(tki.Frame):
    """
    app for the gui
    """
    def __init__(self, root):

        self.root = root
        tki.Frame.__init__(self, root)
        tki.Label(root,
                  text="ASUS ROG Desktop Audio Lighting Control",
                  font="Verdana 15 bold").pack()

        # choose audio input device via radio button
        tki.Label(root,
                  text="Audio Device Choices",
                  font="Verdana 12 bold").pack()
        num_devices, aud_dict = asl.list_devices(do_print=False)
        self.audio_devnum = tki.IntVar()
        self.audio_devnum.set(asl.DEVICE_NUMBER)
        for device_num, device_text in aud_dict.iteritems():
            rbut = tki.Radiobutton(root,
                                   text=device_text,
                                   indicatoron=0,
                                   padx=20,
                                   variable=self.audio_devnum,
                                   value=device_num)
            rbut.pack()
            if device_text.find("Mix"):
                rbut.select()

        # choose directory to the ACPIWMI.dll
        self.path_to_dll = la.DPATH
        tki.Label(root,
                  text="Default Path to ACPIWMI.dll is "+self.path_to_dll,
                  font="Verdana 10 bold").pack()
        self.path_to_dll = la.DPATH
        tki.Button(root, text='Change Path to ACPIWMI.dll', command=self.pick_dll_path).pack()

        # choose the lighting color update interval
        tki.Label(root,
                  text="Doubling increment for Update Interval",
                  font="Verdana 12 bold").pack()
        self.chunk_exponent = 15
        self.slider = tki.Scale(root,
                                from_=12, to=18,
                                tickinterval=1,
                                sliderlength=10,
                                orient=tki.HORIZONTAL)
        self.slider.set(15)
        self.slider.pack()

        # start app button
        start_button = tki.Button(root,
                                  text="Start", fg="green",
                                  font="Verdana 14",
                                  command=self.audio_to_lighting)
        start_button.pack()

        # quit app button
        quit_button = tki.Button(root,
                                 text="QUIT", fg="red",
                                 font="Verdana 14",
                                 command=self.quit_app)
        quit_button.pack(side=tki.BOTTOM)

        self.lighting_thread = None

    def pick_dll_path(self):
        """
        choose path to dll
        """
        path_chosen = tkfd.askdirectory(parent=self.root,
                                        initialdir=self.path_to_dll,
                                        title="Path to ACPIWMI.dll")

        if correct_dll_path(path_chosen):
            self.path_to_dll = path_chosen
        else:
            mbox.showwarning(path_chosen,
                             "ACPIWMI.dll not found in this path")
        return self.path_to_dll

    def optional_choose_dll_path(self):
        """
        choose path to dll only if needed, error checked
        """
        if not correct_dll_path(self.path_to_dll):
            self.path_to_dll = tkfd.askdirectory(parent=self.root,
                                                 initialdir=self.path_to_dll,
                                                 title="Path to ACPIWMI.dll")
            if not correct_dll_path(self.path_to_dll):
                mbox.showwarning("Looking for Path to dll",
                                 "ACPIWMI.dll not found in that path")
        return self.path_to_dll

    def get_update_frequency(self):
        """
        update interval in increments of 0.25 sec
        """
        self.chunk_exponent = int(self.slider.get())
        return self.chunk_exponent

    def audio_to_lighting(self):
        """
        begin sampling display thread
        """
        # get and set the audio port number
        asl.DEVICE_NUMBER = self.audio_devnum.get()

        # get and set the dll path directory
        la.DPATH = self.optional_choose_dll_path()

        # get and set the exponent for the chunk size
        asl.CHUNK_EXPONENT = self.get_update_frequency()

        def callback():
            """
            threaded function
            """
            asl.asus_soundlight(do_print=False)

        self.lighting_thread = threading.Thread(target=callback)
        self.lighting_thread.start()

    def quit_app(self):
        """
        End execution of app
        """
        if not self.lighting_thread == None:
            terminate_thread(self.lighting_thread)
        self.root.destroy()


if __name__ == '__main__':
    ROOT = tki.Tk()
    APP = SoundLightApp(ROOT)
    ROOT.mainloop()

