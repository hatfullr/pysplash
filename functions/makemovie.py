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
from widgets.progressbar import ProgressBar
from matplotlib.animation import FuncAnimation
import numpy as np
import globals
import os

def make_movie(gui):
    MakeMovie(gui)

class MakeMovie(tk.Toplevel, object):
    def __init__(self, gui):
        if globals.debug > 1: print("makemovie.__init__")

        super(MakeMovie, self).__init__(gui)

        self.gui = gui
        self.root = self.gui.window

        aspect = self.root.winfo_screenheight()/self.root.winfo_screenwidth()
        self.width = int(self.root.winfo_screenwidth() / 6)
        height = self.width*aspect
        self.pad = 5

        self.withdraw()
        
        self.protocol("WM_DELETE_WINDOW",self.close)
        self.resizable(False,False)
        self.title("Make movie")
        self.configure(width=self.width,height=height)

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.validate()

        # Show the window
        self.tk.eval('tk::PlaceWindow '+str(self)+' center')

        self.path.trace("w", self.validate)
        self.start_combobox.bind("<<ComboboxSelected>>", self.validate)
        self.stop_combobox.bind("<<ComboboxSelected>>", self.validate)
        self.step.trace("w", self.validate)
        self.delay.trace("w", self.validate)


    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.create_variables")
        self.path = tk.StringVar(value=os.path.join(os.getcwd(),"movie.gif"))
        startvalue=""
        stopvalue=""
        if len(self.gui.filenames) > 0:
            startvalue = self.gui.filenames[0]
            stopvalue = self.gui.filenames[-1]
        self.startfile = tk.StringVar(value=startvalue)
        self.stopfile = tk.StringVar(value=stopvalue)
        self.step = tk.IntVar(value=1)
        self.delay = tk.IntVar(value=100)

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.create_widgets")
        self.description = ttk.Label(
            self,
            text="Choose where you would like to save the movie, then specify the starting and stopping file and the step size to take between them. Each frame will be a snapshot of the plot using the controls currently set in the controls panel.",
            wraplength = self.width -2*self.pad,
            justify='left',
        )

        self.path_frame = tk.Frame(self)
        self.path_entry = Entry(self.path_frame,textvariable=self.path)
        self.browse_button = Button(self.path_frame,text="Browse",command=self.browse)

        self.controls_frame = tk.Frame(self)
        self.start_combobox_frame = tk.LabelFrame(self.controls_frame,text="Start")
        self.start_combobox = ttk.Combobox(self.start_combobox_frame,state='readonly',textvariable=self.startfile,values=self.gui.filenames)
        self.stop_combobox_frame = tk.LabelFrame(self.controls_frame,text="Stop")
        self.stop_combobox = ttk.Combobox(self.stop_combobox_frame,state='readonly',textvariable=self.stopfile,values=self.gui.filenames)
        self.step_frame = tk.LabelFrame(self.controls_frame,text="Step")
        self.step_entry = IntegerEntry(self.step_frame,variable=self.step,allowblank=False,extra_validatecommands=[lambda newtext: int(newtext) != 0])
        self.delay_frame = tk.LabelFrame(self.controls_frame,text="Delay (ms)")
        self.delay_entry = IntegerEntry(self.delay_frame,variable=self.delay,allowblank=False)
        
        self.bottom_frame = tk.Frame(self)
        self.progressbar = ProgressBar(self.bottom_frame,maximum=100)
        self.create_button = Button(self.bottom_frame, text="Create", command=self.create, state='disabled')
        self.cancel_button = Button(self.bottom_frame, text="Cancel", command=self.cancel)
        
    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.place_widgets")

        self.description.pack(side='top',fill='both',expand=True,padx=self.pad,pady=self.pad)
        
        self.path_entry.pack(side='left',fill='both',expand=True,padx=(self.pad,0))
        self.browse_button.pack(side='left',padx=self.pad)
        self.path_frame.pack(side='top',fill='both')
        
        self.start_combobox.pack(fill='both',expand=True)
        self.start_combobox_frame.pack(side='left',fill='both',expand=True)
        self.stop_combobox.pack(fill='both',expand=True)
        self.stop_combobox_frame.pack(side='left',fill='both',expand=True)
        self.step_entry.pack(fill='both',expand=True)
        self.step_frame.pack(side='left',fill='both',expand=True)
        self.delay_entry.pack(fill='both',expand=True)
        self.delay_frame.pack(side='left',fill='both',expand=True)
        self.controls_frame.pack(side='top',fill='both',padx=self.pad,pady=(self.pad,0))

        self.progressbar.pack(side='left',fill='both',expand=True,padx=self.pad)
        self.create_button.pack(side='left')
        self.cancel_button.pack(side='left',padx=self.pad)
        self.bottom_frame.pack(side='top',anchor='e',fill='both',expand=True,pady=self.pad)

    def browse(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.browse")
        path = tkFileDialog.asksaveasfilename(initialfile="movie.gif")
        if path: self.path.set(path)

    def validate(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.validate")

        start = 0
        stop = 0
        if self.startfile.get() in self.gui.filenames:
            start = self.gui.filenames.index(self.startfile.get())
        if self.stopfile.get() in self.gui.filenames:
            stop = self.gui.filenames.index(self.stopfile.get())
        
        if (os.path.isdir(os.path.dirname(self.path.get())) and # The given directory exists
            (os.path.isfile(self.startfile.get()) and os.path.isfile(self.stopfile.get())) and # Both the start and stop files exist
            self.step.get() != 0 and # The step size is not zero
            all([os.path.isfile(f) for f in self.gui.filenames[start:stop:self.step.get()]]) and # All the files in between exist
            self.delay.get() >= 0): # The delay is a reasonable value
            self.create_button.state(['!disabled'])
        else:
            self.create_button.state(['disabled'])

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

    def cancel(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.cancel")
        self.close()

    def close(self, *args, **kwargs):
        if globals.debug > 1: print("makemovie.close")
        self.gui.clear_message()
        self.gui.set_user_controlled(True)
        self.grab_release()
        self.destroy()
        
