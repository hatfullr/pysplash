from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    import tkFileDialog
else:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.filedialog as tkFileDialog
from widgets.switchbutton import SwitchButton
from widgets.entry import Entry
from widgets.integerentry import IntegerEntry
from widgets.floatentry import FloatEntry
from widgets.progressbar import ProgressBar
from matplotlib.animation import FuncAnimation
from widgets.popupwindow import PopupWindow
from widgets.pathentry import PathEntry
from lib.customaxesimage import CustomAxesImage
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
from functions.setpreference import set_preference
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
            canceltext="Close",
            cancelcommand=self.close,
            name='makemovie',
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

        if not self.gui.interactiveplot.colorbar.visible:
            self.starting_climits_low_entry.configure(state='disabled')
            self.starting_climits_high_entry.configure(state='disabled')
            self.ending_climits_low_entry.configure(state='disabled')
            self.ending_climits_high_entry.configure(state='disabled')
            self.link_climits_button.configure(state='disabled')

        if self.link_xlimits_var.get(): self.link_xlimits()
        if self.link_ylimits_var.get(): self.link_ylimits()
        if self.link_climits_var.get(): self.link_climits()

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
        self.starting_xlimits_low = DoubleVar(self, self.gui.controls.axis_controllers['XAxis'].limits.low.get(), 'starting_xlimits_low')
        self.starting_xlimits_high = DoubleVar(self, self.gui.controls.axis_controllers['XAxis'].limits.high.get(), 'starting_xlimits_high')
        self.starting_ylimits_low = DoubleVar(self, self.gui.controls.axis_controllers['YAxis'].limits.low.get(), 'starting_ylimits_low')
        self.starting_ylimits_high = DoubleVar(self, self.gui.controls.axis_controllers['YAxis'].limits.high.get(), 'starting_ylimits_high')
        self.starting_climits_low = DoubleVar(self, self.gui.controls.axis_controllers['Colorbar'].limits.low.get(), 'starting_climits_low')
        self.starting_climits_high = DoubleVar(self, self.gui.controls.axis_controllers['Colorbar'].limits.high.get(), 'starting_climits_high')
        self.ending_xlimits_low = DoubleVar(self, self.gui.controls.axis_controllers['XAxis'].limits.low.get(), 'ending_xlimits_low')
        self.ending_xlimits_high = DoubleVar(self, self.gui.controls.axis_controllers['XAxis'].limits.high.get(), 'ending_xlimits_high')
        self.ending_ylimits_low = DoubleVar(self, self.gui.controls.axis_controllers['YAxis'].limits.low.get(), 'ending_ylimits_low')
        self.ending_ylimits_high = DoubleVar(self, self.gui.controls.axis_controllers['YAxis'].limits.high.get(), 'ending_ylimits_high')
        self.ending_climits_low = DoubleVar(self, self.gui.controls.axis_controllers['Colorbar'].limits.low.get(), 'ending_climits_low')
        self.ending_climits_high = DoubleVar(self, self.gui.controls.axis_controllers['Colorbar'].limits.high.get(), 'ending_climits_high')
        self.link_xlimits_var = BooleanVar(self, False, 'link_xlimits_var')
        self.link_ylimits_var = BooleanVar(self, False, 'link_ylimits_var')
        self.link_climits_var = BooleanVar(self, False, 'link_climits_var')
        
        
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


        self.limits_frame = tk.LabelFrame(self.contents, text="Limits")
        self.starting_limits_frame = tk.LabelFrame(self.limits_frame, text="Start")
        self.ending_limits_frame = tk.LabelFrame(self.limits_frame, text="Stop")
        self.starting_xlimits_frame = tk.Frame(self.starting_limits_frame)
        self.starting_xlimits_label = ttk.Label(self.starting_xlimits_frame, text="x")
        self.starting_xlimits_low_entry = FloatEntry(self.starting_xlimits_frame, variable=self.starting_xlimits_low, allowblank=False)
        self.starting_xlimits_high_entry = FloatEntry(self.starting_xlimits_frame, variable=self.starting_xlimits_high, allowblank=False)
        self.starting_ylimits_frame = tk.Frame(self.starting_limits_frame)
        self.starting_ylimits_label = ttk.Label(self.starting_ylimits_frame, text="y")
        self.starting_ylimits_low_entry = FloatEntry(self.starting_ylimits_frame, variable=self.starting_ylimits_low, allowblank=False)
        self.starting_ylimits_high_entry = FloatEntry(self.starting_ylimits_frame, variable=self.starting_ylimits_high, allowblank=False)
        self.starting_climits_frame = tk.Frame(self.starting_limits_frame)
        self.starting_climits_label = ttk.Label(self.starting_climits_frame, text="c")
        self.starting_climits_low_entry = FloatEntry(self.starting_climits_frame, variable=self.starting_climits_low, allowblank=False)
        self.starting_climits_high_entry = FloatEntry(self.starting_climits_frame, variable=self.starting_climits_high, allowblank=False)

        self.link_limits_frame = tk.LabelFrame(self.limits_frame,text=" ")
        self.link_xlimits_button = SwitchButton(self.link_limits_frame, text="L", width=1, command=(self.link_xlimits, self.unlink_xlimits), variable=self.link_xlimits_var)
        self.link_ylimits_button = SwitchButton(self.link_limits_frame, text="L", width=1, command=(self.link_ylimits, self.unlink_ylimits), variable=self.link_ylimits_var)
        self.link_climits_button = SwitchButton(self.link_limits_frame, text="L", width=1, command=(self.link_climits, self.unlink_climits), variable=self.link_climits_var)
        
        self.ending_xlimits_frame = tk.Frame(self.ending_limits_frame)
        self.ending_xlimits_label = ttk.Label(self.ending_xlimits_frame, text="x")
        self.ending_xlimits_low_entry = FloatEntry(self.ending_xlimits_frame, variable=self.ending_xlimits_low, allowblank=False)
        self.ending_xlimits_high_entry = FloatEntry(self.ending_xlimits_frame, variable=self.ending_xlimits_high, allowblank=False)
        self.ending_ylimits_frame = tk.Frame(self.ending_limits_frame)
        self.ending_ylimits_label = ttk.Label(self.ending_ylimits_frame, text="y")
        self.ending_ylimits_low_entry = FloatEntry(self.ending_ylimits_frame, variable=self.ending_ylimits_low, allowblank=False)
        self.ending_ylimits_high_entry = FloatEntry(self.ending_ylimits_frame, variable=self.ending_ylimits_high, allowblank=False)
        self.ending_climits_frame = tk.Frame(self.ending_limits_frame)
        self.ending_climits_label = ttk.Label(self.ending_climits_frame, text="c")
        self.ending_climits_low_entry = FloatEntry(self.ending_climits_frame, variable=self.ending_climits_low, allowblank=False)
        self.ending_climits_high_entry = FloatEntry(self.ending_climits_frame, variable=self.ending_climits_high, allowblank=False)
        
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


        self.starting_xlimits_label.pack(side='left',padx=(0,5))
        self.starting_xlimits_low_entry.pack(side='left', fill='both',expand=True)
        self.starting_xlimits_high_entry.pack(side='left', fill='both', expand=True)
        self.starting_xlimits_frame.pack(side='top',fill='both',expand=True)

        self.starting_ylimits_label.pack(side='left',padx=(0, 5))
        self.starting_ylimits_low_entry.pack(side='left', fill='both',expand=True)
        self.starting_ylimits_high_entry.pack(side='left', fill='both', expand=True)
        self.starting_ylimits_frame.pack(side='top',fill='both',expand=True)

        self.starting_climits_label.pack(side='left', padx=(0, 5))
        self.starting_climits_low_entry.pack(side='left', fill='both',expand=True)
        self.starting_climits_high_entry.pack(side='left', fill='both', expand=True)
        self.starting_climits_frame.pack(side='top',fill='both',expand=True)
        
        self.starting_limits_frame.pack(side='left',fill='both',expand=True)

        self.link_xlimits_button.pack(side='top',padx=5,pady=1)
        self.link_ylimits_button.pack(side='top',padx=5)
        self.link_climits_button.pack(side='top',padx=5)
        self.link_limits_frame.pack(side='left')

        self.ending_xlimits_label.pack(side='left',padx=(0, 5))
        self.ending_xlimits_low_entry.pack(side='left', fill='both',expand=True)
        self.ending_xlimits_high_entry.pack(side='left', fill='both', expand=True)
        self.ending_xlimits_frame.pack(side='top', fill='both', expand=True)

        self.ending_ylimits_label.pack(side='left',padx=(0, 5))
        self.ending_ylimits_low_entry.pack(side='left', fill='both',expand=True)
        self.ending_ylimits_high_entry.pack(side='left', fill='both', expand=True)
        self.ending_ylimits_frame.pack(side='top', fill='both', expand=True)

        self.ending_climits_label.pack(side='left',padx=(0, 5))
        self.ending_climits_low_entry.pack(side='left', fill='both',expand=True)
        self.ending_climits_high_entry.pack(side='left', fill='both', expand=True)
        self.ending_climits_frame.pack(side='top', fill='both', expand=True)
        
        self.ending_limits_frame.pack(side='left',fill='both',expand=True)
        
        self.limits_frame.pack(side='top', fill='both', expand=True)
        
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

        self.gui.interactiveplot.making_movie = True

        self.okbutton.configure(state='disabled')
        self.cancelbutton.configure(state='disabled')
        self.path_entry.configure(state='disabled')
        self.delay_entry.configure(state='disabled')
        self.step_entry.configure(state='disabled')
        self.start_combobox.configure(state='disabled')
        self.stop_combobox.configure(state='disabled')
        self.starting_xlimits_low_entry.configure(state='disabled')
        self.starting_xlimits_high_entry.configure(state='disabled')
        self.starting_ylimits_low_entry.configure(state='disabled')
        self.starting_ylimits_high_entry.configure(state='disabled')
        self.starting_climits_low_entry.configure(state='disabled')
        self.starting_climits_high_entry.configure(state='disabled')
        self.ending_xlimits_low_entry.configure(state='disabled')
        self.ending_xlimits_high_entry.configure(state='disabled')
        self.ending_ylimits_low_entry.configure(state='disabled')
        self.ending_ylimits_high_entry.configure(state='disabled')
        self.ending_climits_low_entry.configure(state='disabled')
        self.ending_climits_high_entry.configure(state='disabled')
        self.link_xlimits_button.configure(state='disabled')
        self.link_ylimits_button.configure(state='disabled')
        self.link_climits_button.configure(state='disabled')
        
        self.gui.set_user_controlled(False)
        
        start = self.gui.filenames.index(self.startfile.get())
        stop = self.gui.filenames.index(self.stopfile.get())
        step = self.step.get()

        filenames = self.gui.filenames[start:stop+1:step]
        
        nframes = len(filenames)
        
        self.progressbar.configure(value=0)

        self.already_did_it = False

        xlow_start = self.starting_xlimits_low.get()
        xhigh_start = self.starting_xlimits_high.get()
        ylow_start = self.starting_ylimits_low.get()
        yhigh_start = self.starting_ylimits_high.get()
        xlow_stop = self.ending_xlimits_low.get()
        xhigh_stop = self.ending_xlimits_high.get()
        ylow_stop = self.ending_ylimits_low.get()
        yhigh_stop = self.ending_ylimits_high.get()
        clow_start = self.starting_climits_low.get()
        chigh_start = self.starting_climits_high.get()
        clow_stop = self.ending_climits_low.get()
        chigh_stop = self.ending_climits_high.get()

        dx_low = (xlow_stop - xlow_start) / float(nframes)
        dx_high = (xhigh_stop - xhigh_start) / float(nframes)
        dy_low = (ylow_stop - ylow_start) / float(nframes)
        dy_high = (yhigh_stop - yhigh_start) / float(nframes)
        dc_low = (clow_stop - clow_start) / float(nframes)
        dc_high = (chigh_stop - chigh_start) / float(nframes)

        self.ready_to_advance = False
        def skip_to_next(*args, **kwargs):
            self.ready_to_advance = True
        
        bid = self.gui.bind("<<AfterPlotUpdate>>", skip_to_next, add="+")
        
        self._progress_step = 1./float(nframes) * 100
        self._progress = 0
        
        def update(i):
            if not self.already_did_it: self.already_did_it = i == nframes-1
            if self.already_did_it: return None,
            self.gui.filecontrols.current_file.set(filenames[i])
            
            self.gui.controls.axis_controllers['XAxis'].limits.low.set(xlow_start + dx_low*i)
            self.gui.controls.axis_controllers['XAxis'].limits.high.set(xhigh_start + dx_high*i)
            self.gui.controls.axis_controllers['YAxis'].limits.low.set(ylow_start + dy_low*i)
            self.gui.controls.axis_controllers['YAxis'].limits.high.set(yhigh_start + dy_high*i)
            if self.gui.interactiveplot.colorbar.visible:
                self.gui.controls.axis_controllers['Colorbar'].limits.low.set(clow_start + dc_low*i)
                self.gui.controls.axis_controllers['Colorbar'].limits.high.set(chigh_start + dc_high*i)
            
            self.gui.controls.update_button.invoke()

            #while not self.ready_to_advance:
            #    self.gui.update_idletasks()
            #self.ready_to_advance = False

            #if isinstance(self.gui.interactiveplot.drawn_object, CustomAxesImage):
            #    while self.gui.interactiveplot.drawn_object.calculating:
            #        self.gui.update()

            self._progress += self._progress_step
            self.progressbar.set_text("Creating movie... (%3.2f%%)" % self._progress)
            self.progressbar.configure(value = self._progress)
            
            self.gui.interactiveplot.draw() # Make sure we can see the image properly before moving to the next frame
            return self.gui.interactiveplot.drawn_object,

        self.anim = FuncAnimation(
            self.gui.interactiveplot.fig,
            update,
            frames=range(len(filenames)),
            interval=self.delay.get(),
            blit=False,
        )
        
        self.anim.save(self.path.get())
        self.progressbar.set_text("Done")
        self.progressbar.configure(value=0)
        
        self.gui.set_user_controlled(True)
        self.gui.unbind("<<AfterPlotUpdate>>", bid)

        self.okbutton.configure(state='normal')
        self.cancelbutton.configure(state='normal')
        self.path_entry.configure(state='normal')
        self.delay_entry.configure(state='normal')
        self.step_entry.configure(state='normal')
        self.start_combobox.configure(state='readonly')
        self.stop_combobox.configure(state='readonly')
        self.starting_xlimits_low_entry.configure(state='normal')
        self.starting_xlimits_high_entry.configure(state='normal')
        self.starting_ylimits_low_entry.configure(state='normal')
        self.starting_ylimits_high_entry.configure(state='normal')
        self.ending_xlimits_low_entry.configure(state='normal')
        self.ending_xlimits_high_entry.configure(state='normal')
        self.ending_ylimits_low_entry.configure(state='normal')
        self.ending_ylimits_high_entry.configure(state='normal')
        self.link_xlimits_button.configure(state='normal')
        self.link_ylimits_button.configure(state='normal')
        
        if self.gui.interactiveplot.colorbar.visible:
            self.starting_climits_low_entry.configure(state='normal')
            self.starting_climits_high_entry.configure(state='normal')
            self.ending_climits_low_entry.configure(state='normal')
            self.ending_climits_high_entry.configure(state='normal')
            self.link_climits_button.configure(state='normal')
        
        self.gui.interactiveplot.making_movie = False
        
        
    def close(self,*args,**kwargs):
        if self.gui.interactiveplot.making_movie: return
        pairs = [
            ['path', self.path],
            ['startfile', self.startfile],
            ['stopfile', self.stopfile],
            ['step', self.step],
            ['delay', self.delay],
            ['starting_xlimits_low', self.starting_xlimits_low],
            ['starting_xlimits_high', self.starting_xlimits_high],
            ['starting_ylimits_low', self.starting_ylimits_low],
            ['starting_ylimits_high', self.starting_ylimits_high],
            ['starting_climits_low', self.starting_climits_low],
            ['starting_climits_high', self.starting_climits_high],
            ['ending_xlimits_low', self.ending_xlimits_low],
            ['ending_xlimits_high', self.ending_xlimits_high],
            ['ending_ylimits_low', self.ending_ylimits_low],
            ['ending_ylimits_high', self.ending_ylimits_high],
            ['ending_climits_low', self.ending_climits_low],
            ['ending_climits_high', self.ending_climits_high],
            ['link_xlimits_var', self.link_xlimits_var],
            ['link_ylimits_var', self.link_ylimits_var],
            ['link_climits_var', self.link_climits_var],
        ]

        for pair in pairs:
            set_preference(self, pair[0], pair[1].get())
        
        super(MakeMovie, self).close(*args, **kwargs)

    def link_xlimits(self, *args, **kwargs):
        self.ending_xlimits_low_entry.configure(state='disabled')
        self.ending_xlimits_high_entry.configure(state='disabled')
        self.ending_xlimits_low.set(self.starting_xlimits_low.get())
        self.ending_xlimits_high.set(self.starting_xlimits_high.get())

        self._bid_xlow = self.starting_xlimits_low_entry.bind("<<ValidateSuccess>>", lambda *args, **kwargs: self.ending_xlimits_low.set(self.starting_xlimits_low.get()), add="+")
        self._bid_xhigh = self.starting_xlimits_high_entry.bind("<<ValidateSuccess>>", lambda *args, **kwargs: self.ending_xlimits_high.set(self.starting_xlimits_high.get()), add="+")
    
    def unlink_xlimits(self, *args, **kwargs):
        self.ending_xlimits_low_entry.configure(state='normal')
        self.ending_xlimits_high_entry.configure(state='normal')

        if hasattr(self, "_bid_xlow") and self._bid_xlow is not None:
            self.starting_xlimits_low_entry.unbind("<<ValidateSuccess>>", self._bid_xlow)
            self._bid_xlow = None
        if hasattr(self, "_bid_xhigh") and self._bid_xhigh is not None:
            self.starting_xlimits_high_entry.unbind("<<ValidateSuccess>>", self._bid_xhigh)
            self._bid_xhigh = None
        

    def link_ylimits(self, *args, **kwargs):
        self.ending_ylimits_low_entry.configure(state='disabled')
        self.ending_ylimits_high_entry.configure(state='disabled')
        self.ending_ylimits_low.set(self.starting_ylimits_low.get())
        self.ending_ylimits_high.set(self.starting_ylimits_high.get())

        self._bid_ylow = self.starting_ylimits_low_entry.bind("<<ValidateSuccess>>", lambda *args, **kwargs: self.ending_ylimits_low.set(self.starting_ylimits_low.get()), add="+")
        self._bid_yhigh = self.starting_ylimits_high_entry.bind("<<ValidateSuccess>>", lambda *args, **kwargs: self.ending_ylimits_high.set(self.starting_ylimits_high.get()), add="+")
    
        
    def unlink_ylimits(self, *args, **kwargs):
        self.ending_ylimits_low_entry.configure(state='normal')
        self.ending_ylimits_high_entry.configure(state='normal')

        if hasattr(self, "_bid_ylow") and self._bid_ylow is not None:
            self.starting_ylimits_low_entry.unbind("<<ValidateSuccess>>", self._bid_ylow)
            self._bid_ylow = None
        if hasattr(self, "_bid_yhigh") and self._bid_yhigh is not None:
            self.starting_ylimits_high_entry.unbind("<<ValidateSuccess>>", self._bid_yhigh)
            self._bid_yhigh = None

    def link_climits(self, *args, **kwargs):
        self.ending_climits_low_entry.configure(state='disabled')
        self.ending_climits_high_entry.configure(state='disabled')
        self.ending_climits_low.set(self.starting_climits_low.get())
        self.ending_climits_high.set(self.starting_climits_high.get())

        self._bid_clow = self.starting_climits_low_entry.bind("<<ValidateSuccess>>", lambda *args, **kwargs: self.ending_climits_low.set(self.starting_climits_low.get()), add="+")
        self._bid_chigh = self.starting_climits_high_entry.bind("<<ValidateSuccess>>", lambda *args, **kwargs: self.ending_climits_high.set(self.starting_climits_high.get()), add="+")
    
        
    def unlink_climits(self, *args, **kwargs):
        self.ending_climits_low_entry.configure(state='normal')
        self.ending_climits_high_entry.configure(state='normal')

        if hasattr(self, "_bid_clow") and self._bid_ylow is not None:
            self.starting_climits_low_entry.unbind("<<ValidateSuccess>>", self._bid_clow)
            self._bid_ylow = None
        if hasattr(self, "_bid_chigh") and self._bid_chigh is not None:
            self.starting_climits_high_entry.unbind("<<ValidateSuccess>>", self._bid_chigh)
            self._bid_chigh = None
