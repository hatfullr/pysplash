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
from functions.findparticle import FindParticle
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import traceback

class AnnotateParticle(FindParticle,object):
    def __init__(self, gui):
        if globals.debug > 1: print("findparticle.__init__")
        self.gui = gui
        
        # Setup the window
        super(AnnotateParticle,self).__init__(self.gui)
        self.title("Annotate particle")
        self.okbutton.configure(
            text="Annotate (Enter)",
            command=self.annotate,
        )
        self.description.configure(
            text="Enter the zero'th-indexed ID number of a particle you would like to annotate.",
        )
        
    def annotate(self,*args,**kwargs):
        particle = self.find_particle()
        if particle is not None:
            self.gui.interactiveplot.annotate_particle(ID=particle)
            self.close()
