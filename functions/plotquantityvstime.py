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
from widgets.popoutaxis import PopoutAxis
from widgets.integerentry import IntegerEntry
from widgets.mathcombobox import MathCombobox
from widgets.progressbar import ProgressBar
from functions.hotkeystostring import hotkeys_to_string
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import lib.tkvariable as tkvariable
import traceback
import matplotlib.patches
import collections
from read_file import read_file

class PlotQuantityVsTime(PopupWindow,object):
    def __init__(self, gui):
        if globals.debug > 1: print("plotquantityvstime.__init__")
        self.gui = gui
        
        # Setup the window
        super(PlotQuantityVsTime,self).__init__(
            self.gui,
            title="Plot quantity vs time",
            oktext="Plot (Enter)",
            okcommand=self.on_ok_button,
            show=True,
            name='plotquantityvstime',
        )

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.entry.bind("<Return>", lambda *args, **kwargs: self.okbutton.invoke(), add="+")
        self.entry.focus()
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("plotquantityvstime.create_variables")
        self.particle = IntVar(self,0,'particle')
        self.yaxis = StringVar(self,self.gui.controls.axis_controllers['YAxis'].value.get(), 'yaxis')

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("plotquantityvstime.create_widgets")
        self.description = ttk.Label(
            self.contents,
            text="Enter the zero'th-indexed ID number of a particle you would like to plot a quantity for, then select the quantity to plot.",
            wraplength=self.width-2*self.cget('padx'),
            justify='left',
        )

        self.entry = IntegerEntry(
            self.contents,
            variable=self.particle,
            allowblank=False,
        )

        self.yaxis_frame = tk.Frame(self.contents)
        self.yaxis_label = ttk.Label(self.yaxis_frame,text="y axis")
        self.yaxis_combobox = MathCombobox(
            self.yaxis_frame,
            self.gui,
            width=0,
            values=self.gui.controls.axis_controllers['YAxis'].combobox.values,
            textvariable=self.yaxis,
            where='top',
        )

        self.progressbar = ProgressBar(
            self.buttons_frame,
            maximum=100,
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("plotquantityvstime.place_widgets")
        self.description.pack(side='top',fill='both')
        self.entry.pack(side='left',fill='x', expand=True)

        self.yaxis_label.pack(side='left',padx=(0,5))
        self.yaxis_combobox.pack(side='left',fill='x',expand=True)
        self.yaxis_frame.pack(side='left',fill='x',expand=True)
        self.progressbar.pack(anchor='center',side='left',fill='both',expand=True,padx=(0,5))

    def find_particle(self, *args, **kwargs):
        if globals.debug > 1: print("findparticle.find_particle")
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
            self.gui.message("Failed to find particle "+str(value),duration=5000)
            self.entry.event_generate("<<ValidateFail>>")
            return None

    def on_ok_button(self,*args,**kwargs):
        if globals.debug > 1: print("plotquantityvstime.on_okay_button")
        tkvariable.save()
        particle = self.find_particle() # Do validations
        if particle is not None:
            time, data = self.get_data(particle)
            y, y_display_units, y_physical_units = self.yaxis_combobox.get(
                data=data,
                get_display_data_method = lambda key: data['data'][key] * data['display_units'][key],
                get_display_units_method = lambda key: np.array([data['display_units'][key]]),
                get_physical_units_method = lambda key: np.array([data['physical_units'][key]]),
            )

            # Plot the data
            self.progressbar.set_text("Plotting data...")

            self.ax = PopoutAxis(self.gui)
            self.ax.plot(time, y)
            
            self.close()

    def get_data(self, particle):
        if globals.debug > 1: print("plotquantityvstime.get_data")
        
        startprogress = 0
        endprogress = 80
        message = "Reading data files... (%3.2f%%)"
        self.progressbar.set_text(message % startprogress)
        self.progressbar.configure(value=startprogress)

        nfiles = len(self.gui.filenames)

        data = {
            'data' : collections.OrderedDict({}),
            'display_units' : collections.OrderedDict({}),
            'physical_units' : collections.OrderedDict({}),
        }
        
        time = []
        
        ystring = self.yaxis.get()
        print(ystring)
        compact_support = None
        datalength = None
        for i,filename in enumerate(self.gui.filenames):
            d = read_file(filename)

            # Check for inconsistent data
            if compact_support is None:
                compact_support = d.get('compact_support',None)
            else:
                if 'compact_support' in d.keys():
                    if d['compact_support'] != compact_support:
                        raise ValueError("compact_support value mismatch")
                else:
                    raise ValueError("compact_support value mismatch")

            length = 0
            for key,val in d['data'].items():
                if key not in ['t','time','Time']:
                    length = len(val)
                    break
            if length == 0: raise Exception("data file '"+filename+"' either only contains time data, or has no data at all")
            
            for key, val in d['data'].items():
                if key in ['t','time','Time']: time.append(val)
                else:
                    if key in ystring:
                        if key not in data['data'].keys(): data['data'][key] = [val[particle]]
                        else: data['data'][key] += [val[particle]]

                if key not in data['display_units'].keys():
                    data['display_units'][key] = d['display_units'][key]
                elif data['display_units'][key] != d['display_units'][key]:
                    raise Exception("the input files have inconsistent data structures. For key '"+key+"', we previously found display units of '"+data['display_units'][key]+"', but file '"+filename+"' has display units of '"+d['display_units'][key]+"' for this key.")

                if key not in data['physical_units'].keys():
                    data['physical_units'][key] = d['physical_units'][key]
                elif data['physical_units'][key] != d['physical_units'][key]:
                    raise Exception("the input files have inconsistent data structures. For key '"+key+"', we previously found physical units of '"+data['display_units'][key]+"', but file '"+filename+"' has physical units of '"+d['display_units'][key]+"' for this key.")

            progress = startprogress + (endprogress - startprogress) * float(i)/float(nfiles)
            self.progressbar.configure(value=progress)
            self.progressbar.set_text(message % progress)
            self.update()

        startprogress = 80
        endprogress = 100
        message = "Flattening data arrays... (%3.2f%%)"
        n = len(data['data'].keys())
        self.progressbar.set_text(message % startprogress)
        for i,(key, val) in enumerate(data['data'].items()):
            data['data'][key] = np.array(val).flatten()
            progress = startprogress + (endprogress - startprogress) * float(i)/float(n)
            self.progressbar.configure(value=progress)
            self.progressbar.set_text(message % progress)
            self.update()
        
        self.progressbar.configure(value=endprogress)
        self.progressbar.set_text("")

        return np.array(time), data
