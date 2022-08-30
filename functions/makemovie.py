from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    import tkFileDialog
else:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.filedialog as tkFileDialog
from widgets.button import Button
from widgets.entry import Entry
from widgets.integerentry import IntegerEntry
from widgets.floatentry import FloatEntry
from widgets.progressbar import ProgressBar
from matplotlib.animation import FuncAnimation
from widgets.popupwindow import PopupWindow
from widgets.pathentry import PathEntry
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import numpy as np
import globals
import os

def make_movie(gui):
    MakeMovie(gui)

class MakeMovie(PopupWindow, object):
    def __init__(self, gui):
        if globals.debug > 1: print("makemovie.__init__")

        super(MakeMovie, self).__init__(
            gui,
            title="Make movie",
            oktext="Save",
            okcommand=self.create,
        )

        self.gui = gui
        self.root = self.gui.window
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.path_entry.bind("<<ValidateFail>>", self.validate, add = "+")
        self.path_entry.bind("<<ValidateSuccess>>", self.validate, add = "+")
        self.start_combobox.bind("<<ComboboxSelected>>", self.validate, add = "+")
        self.stop_combobox.bind("<<ComboboxSelected>>", self.validate, add = "+")

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.create_variables")
        self.path = StringVar(self,os.path.join(os.getcwd(),"movie.gif"),'path')
        startvalue=""
        stopvalue=""
        if len(self.gui.filenames) > 0:
            startvalue = self.gui.filenames[0]
            stopvalue = self.gui.filenames[-1]
        self.startfile = StringVar(self,startvalue,'startfile')
        self.stopfile = StringVar(self,stopvalue,'stopfile')
        self.step = IntVar(self,1,'step')
        self.delay = DoubleVar(self,100,'delay')

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.create_widgets")
        self.description = ttk.Label(
            self.contents,
            text="Choose where you would like to save the movie, then specify the starting and stopping file and the step size to take between them. Each frame will be a snapshot of the plot using the controls currently set in the controls panel.",
            wraplength = self.width -2*self.cget('padx'),
            justify='left',
        )

        self.path_entry = PathEntry(self.contents,"save as filename",textvariable=self.path)

        self.controls_frame = tk.Frame(self.contents)
        self.start_combobox_frame = tk.LabelFrame(self.controls_frame,text="Start")
        self.start_combobox = ttk.Combobox(self.start_combobox_frame,state='readonly',textvariable=self.startfile,values=self.gui.filenames)
        self.stop_combobox_frame = tk.LabelFrame(self.controls_frame,text="Stop")
        self.stop_combobox = ttk.Combobox(self.stop_combobox_frame,state='readonly',textvariable=self.stopfile,values=self.gui.filenames)
        self.step_frame = tk.LabelFrame(self.controls_frame,text="Step")
        self.step_entry = IntegerEntry(self.step_frame,variable=self.step,allowblank=False,disallowed_values=[0])#extra_validatecommands=[lambda newtext: int(newtext) != 0])
        self.delay_frame = tk.LabelFrame(self.controls_frame,text="Delay (ms)")
        self.delay_entry = FloatEntry(self.delay_frame,variable=self.delay,allowblank=False,clamp=(0,None))
        
        self.progressbar = ProgressBar(self.buttons_frame,maximum=100)
        
    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.place_widgets")

        self.description.pack(side='top',fill='both',expand=True)
        self.path_entry.pack(side='top',fill='both',expand=True,pady=5)
        
        self.start_combobox.pack(fill='both',expand=True)
        self.start_combobox_frame.pack(side='left',fill='both',expand=True)
        self.stop_combobox.pack(fill='both',expand=True)
        self.stop_combobox_frame.pack(side='left',fill='both',expand=True)
        self.step_entry.pack(fill='both',expand=True)
        self.step_frame.pack(side='left',fill='both',expand=True)
        self.delay_entry.pack(fill='both',expand=True)
        self.delay_frame.pack(side='left',fill='both',expand=True)
        self.controls_frame.pack(side='top',fill='both')
        
        self.progressbar.pack(side='left',fill='both',expand=True,padx=(0,5))

    def validate(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.validate")
        
        # No empty start/stop comboboxes
        if ((self.startfile.get().strip() and self.startfile.get().strip() != "") and
            (self.stopfile.get().strip() and self.stopfile.get().strip() != "")):
            self.okbutton.configure(state='normal')
        else: self.okbutton.configure(state='disabled')
        
    def create(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.create")
        self.gui.set_user_controlled(False)
        
        start = self.gui.filenames.index(self.startfile.get())
        stop = self.gui.filenames.index(self.stopfile.get())
        step = self.step.get()

        filenames = self.gui.filenames[start:stop+1:step]
        
        nframes = len(filenames)
        
        self.progressbar.configure(value=0)
        
        def update(i):
            self.gui.filecontrols.current_file.set(filenames[i])
            #self.gui.controls.on_update_button_pressed()
            self.gui.controls.update_button.invoke()
            
            # We need to wait until the plot has finished calculating
            while self.gui.interactiveplot.drawn_object.calculating:
                self.gui.update()

            progress = float(i)/float(nframes) * 100
            self.progressbar.set_text("Creating movie... (%3.2f%%)" % progress)
            self.progressbar.configure(value = progress)
            
            return self.gui.interactiveplot.drawn_object,

        anim = FuncAnimation(
            self.gui.interactiveplot.fig,
            update,
            frames=nframes,
            interval=self.delay.get(),
            blit=True,
        )
        
        anim.save(self.path.get())

        self.progressbar.set_text("Done")
        self.progressbar.configure(value=0)

        
