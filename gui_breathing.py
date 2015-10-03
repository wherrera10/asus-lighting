# -*- coding: utf-8 -*-
"""
Created on Fri Oct 02 22:27:03 2015

@author: William Herrera

IMPORTANT: run as administrator

Color breathing gui program for G20aj series PC

"""

import os
import ctypes
import threading

import Tkinter as tki
import ttk
from tkColorChooser import askcolor
import tkFileDialog as tkfd
import tkMessageBox as mbox

import light_acpi as la
import hyperventilate as hv

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

class BreathingApp(tki.Frame): #pylint: disable-msg=R0902
    """
    app for the gui
    """
    def __init__(self, root):

        self.root = root
        tki.Frame.__init__(self, root)
        tki.Label(root,
                  text="ASUS ROG Desktop Breathing Lighting Control",
                  font="Verdana 15 bold").pack()

        ttk.Separator(root, orient=tki.HORIZONTAL).pack(fill=tki.BOTH, expand=1)

        # choose colors via radio button
        self.leftcolor = 0xff0000
        self.rightcolor = 0x0000ff
        self.basecolor = 0x00ff00
        tki.Label(root,
                  text="Choose Colors",
                  font="Verdana 12 bold").pack()
        tki.Button(text='Select Left Color', command=self.get_left_color).pack()
        tki.Button(text='Select Right Color', command=self.get_right_color).pack()
        tki.Button(text='Select Base Color', command=self.get_base_color).pack()

        ttk.Separator(root, orient=tki.HORIZONTAL).pack(fill=tki.BOTH, expand=1)

        # choose directory to the ACPIWMI.dll
        self.path_to_dll = la.DPATH
        tki.Label(root,
                  text="Default Path to ACPIWMI.dll is "+self.path_to_dll,
                  font="Verdana 10 bold").pack()
        self.path_to_dll = la.DPATH
        tki.Button(root, text='Change Path to ACPIWMI.dll', command=self.pick_dll_path).pack()

        ttk.Separator(root, orient=tki.HORIZONTAL).pack(fill=tki.BOTH, expand=1)

        # choose the breathing rate update interval
        self.resp_rate = 15
        tki.Label(root,
                  text="Breathing Rate (bpm)",
                  font="Verdana 12 bold").pack()
        self.slider = tki.Scale(root, from_=6, to=24, tickinterval=1,
                                sliderlength=5, orient=tki.HORIZONTAL)
        self.slider.set(15)
        self.slider.pack(fill=tki.BOTH, expand=1)

        ttk.Separator(root, orient=tki.HORIZONTAL).pack(fill=tki.BOTH, expand=1)

        # start app button
        tki.Button(root, text="Start", fg="green", font="Verdana 14",
                   command=self.breathe).pack()

        # quit app button
        tki.Button(root, text="QUIT", fg="red", font="Verdana 14",
                   command=self.quit_app).pack(side=tki.BOTTOM)

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

    def get_left_color(self):
        """
        get a color
        """
        lst = list(askcolor()[0])
        self.leftcolor = hv.make_rgb(lst[0], lst[1], lst[2])

    def get_right_color(self):
        """
        get a color
        """
        lst = list(askcolor()[0])
        self.rightcolor = hv.make_rgb(lst[0], lst[1], lst[2])

    def get_base_color(self):
        """
        get a color
        """
        lst = list(askcolor()[0])
        self.basecolor = hv.make_rgb(lst[0], lst[1], lst[2])

    def get_resp_rate(self):
        """
        get breathing rate
        """
        self.resp_rate = int(self.slider.get())
        return self.resp_rate

    def breathe(self):
        """
        begin sampling display thread
        """
        if not self.lighting_thread == None:
            terminate_thread(self.lighting_thread)

        # get and set the dll path directory
        la.DPATH = self.optional_choose_dll_path()

        # get breathing rate sleep/update time interval for frames
        tinterval = 2.0 / self.get_resp_rate()
        fnum = 30

        # get colors
        colors = [self.leftcolor, self.rightcolor, self.basecolor]

        def callback():
            """
            threaded function
            """
            hv.all_cycle(colors, frames=fnum, sleepinterval=tinterval)

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
    APP = BreathingApp(ROOT)
    ROOT.mainloop()


