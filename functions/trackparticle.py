from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
import os
import globals
import numpy as np
from widgets.popupwindow import PopupWindow
from widgets.integerentry import IntegerEntry
from functions.hotkeystostring import hotkeys_to_string
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import traceback

class TrackParticle(PopupWindow,object):
    def __init__(self, gui):
        if globals.debug > 1: print("trackparticle.__init__")
        self.gui = gui
        
        # Setup the window
        super(TrackParticle,self).__init__(
            self.gui,
            title="Track particle",
            oktext="Track (Enter)",
            okcommand=self.track,
            show=True,
            name='trackparticle',
        )

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.entry.bind("<Return>", lambda *args, **kwargs: self.okbutton.invoke(), add="+")
        self.entry.focus()
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("trackparticle.create_variables")
        self.particle = IntVar(self,0,'particle')

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("trackparticle.create_widgets")
        self.description = ttk.Label(
            self.contents,
            text="Enter the zero'th-indexed ID number of a particle you would like to locate on the current plot. Tracking will then be turned on for that particle and an annotation will be placed next to it as though you had pressed "+hotkeys_to_string("track and annotate particle")+" with your mouse over it. To stop tracking the particle, press "+hotkeys_to_string("track and annotate particle")+" anywhere outside the plot.",
            wraplength=self.width-2*self.cget('padx'),
            justify='left',
        )
        self.entry = IntegerEntry(
            self.contents,
            variable=self.particle,
            allowblank=False,
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("trackparticle.place_widgets")
        self.description.pack(side='top',fill='both')
        self.entry.pack(side='top',fill='x')

    def track_particle(self, *args, **kwargs):
        if globals.debug > 1: print("trackparticle.track_particle")
        # See if the particle ID is in the data set
        data = self.gui.data

        # Make extra sure the variable is properly set
        validated = self.entry.validatecommand(self.entry.get())
        if not validated: return None
        value = self.entry.variable.get()
        
        if (data is not None and
            value in np.arange(len(data['data'][list(data['data'].keys())[0]]))):
            return value
        else:
            self.gui.message("Failed to track particle "+str(value),duration=5000)
            self.entry.event_generate("<<ValidateFail>>")
            return None

    def track(self,*args,**kwargs):
        if globals.debug > 1: print("trackparticle.track")

        particle = self.track_particle()
        if particle is not None and particle != self.gui.interactiveplot.track_id.get():
            self.close()
            # We should only get here if check_id has returned True
            self.gui.interactiveplot.track_particle(index=particle)
            self.gui.interactiveplot.annotate_tracked_particle()
            self.gui.interactiveplot.track_and_annotate = True
        
        
        
