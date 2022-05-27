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
import traceback

def findparticle(gui):
    FindParticle(gui)


class FindParticle(PopupWindow,object):
    def __init__(self, gui):
        if globals.debug > 1: print("findparticle.__init__")
        self.gui = gui
        
        # Setup the window
        super(FindParticle,self).__init__(
            self.gui,
            title="Find particle",
            oktext="Find (Enter)",
            okcommand=self.find,
            show=True,
        )

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.entry.bind("<Return>", lambda *args, **kwargs: self.okbutton.invoke(), add="+")
        self.entry.focus()
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("findparticle.create_variables")
        # Gather the preferences
        preference = self.gui.get_preference("findparticle")
        if preference is None: preference = {'particle':0}
        self.particle = tk.IntVar(value=preference['particle'])

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("findparticle.create_widgets")
        self.description = ttk.Label(
            self.contents,
            text="Enter the ID number of a particle you would like to locate on the current plot. Tracking will then be turned on for that particle and an annotation will be placed next to it as though you had pressed "+hotkeys_to_string("track and annotate particle")+" with your mouse over it. To stop tracking the particle, press "+hotkeys_to_string("track and annotate particle")+" anywhere outside the plot.",
            wraplength=self.width-2*self.cget('padx'),
            justify='left',
        )
        self.entry = IntegerEntry(
            self.contents,
            variable=self.particle,
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("findparticle.place_widgets")
        self.description.pack(side='top',fill='both')
        self.entry.pack(side='top',fill='x')

    def find(self,*args,**kwargs):
        if globals.debug > 1: print("findparticle.find")

        # See if the particle ID is in the data set
        data = self.gui.data

        # Make extra sure the variable is properly set
        self.entry.validatecommand(self.entry.get())
        value = self.entry.variable.get()
        
        if (data is not None and
            value in np.arange(len(data['data'][list(data['data'].keys())[0]]))):
            # Save the preferences
            self.gui.set_preference("findparticle",{"particle":value})
            
            # We should only get here if check_id has returned True
            self.gui.interactiveplot.track_particle(index=value)
            self.gui.interactiveplot.annotate_tracked_particle()
            self.gui.interactiveplot.track_and_annotate = True
            self.close()
        else:
            self.gui.message("Failed to find particle "+str(value),duration=5000)
            self.entry.event_generate("<<ValidateFail>>")
