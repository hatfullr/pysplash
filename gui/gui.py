import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    from tkFont import Font as tkFont
    from interactiveplot import InteractivePlot
    from controls import Controls
    from customtoolbar import CustomToolbar
    from filecontrols import FileControls
    from menubar.menubar import MenuBar
else:
    import tkinter as tk
    import tkinter.font as tkFont
    from gui.interactiveplot import InteractivePlot
    from gui.controls import Controls
    from gui.customtoolbar import CustomToolbar
    from gui.filecontrols import FileControls
    from gui.menubar.menubar import MenuBar

from lib.data import Data
from functions.makemovie import make_movie
from functions.makerotationmovie import make_rotation_movie
from functions.getallchildren import get_all_children
from functions.importdata import ImportData
from functions.findparticle import FindParticle
from functions.rotate import rotate
from lib.threadedtask import ThreadedTask
from lib.hotkeys import Hotkeys
from hotkeyslist import hotkeyslist
from lib.tkvariable import save, StringVar, IntVar, DoubleVar, BooleanVar

from read_file import read_file
import globals
import copy
import os.path
import json
import os
import numpy as np
import collections


class GUI(tk.Frame,object):
    def __init__(self,window,fontname='TkDefaultFont',fontsize=12):
        if globals.debug > 1: print("gui.__init__")
        
        self.window = window

        #self.preferences = Preferences(self)
        # Save the preferences when the window closes
        self.window.on_close['save preferences'] = {'method' : save}
        #self.window.on_close['save preferences'] = {'method' : self.preferences.save}
        
        self.fontname = fontname
        self.fontsize = fontsize

        # Turn this on and off to indicate that edits are being
        # made from the code rather than from the user
        self.user_controlled = True
        
        if sys.version_info.major < 3:
            self.default_font = tkFont(name=self.fontname,exists=True)
        else:
            self.default_font = tkFont.nametofont(self.fontname)
        # Make sure the font is at least size fontsize_pt
        if abs(self.default_font.actual()['size']) < self.fontsize:
            self.default_font.configure(size=self.fontsize)
        self.fontsize_px = self.default_font.metrics()['ascent'] + self.default_font.metrics()['descent']

        self.window.option_add("*Font",self.default_font)
        
        # Detect proper dpi scaling
        self.dpi = self.window.winfo_fpixels('1i')

        super(GUI,self).__init__(self.window)
        
        self._data = None
        self._data_time_mode = None
        self._display_data = None
        self._display_data_time_mode = None

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        # When the user clicks on widgets etc, those widgets should acquire
        # the application focus... (why isn't this default?!)
        self.window.bind("<Button-1>", self.on_button1)
        
        self.create_hotkeys()

        self.filenames = []
        self.message_after_id = None

        self.previous_file = None
        self.time_mode.trace('w',self.toggle_time_mode)
        
        #self.xy_controls_initialized = False
        self.initialize(first=True)
        self.controls.connect()

    @property
    def data(self): return self._data_time_mode if self.time_mode.get() else self._data
    @data.setter
    def data(self,value):
        if self.time_mode.get(): self._data_time_mode = value
        else: self._data = value

    @property
    def display_data(self): return self._display_data_time_mode if self.time_mode.get() else self._display_data
    @display_data.setter
    def display_data(self,value):
        if self.time_mode.get(): self._display_data_time_mode = value
        else: self._display_data = value

    def on_button1(self, event):
        if globals.debug > 1: print("gui.on_button1")
        widget = event.widget
        # Clicking on the menubar gives a strange event.widget
        if isinstance(widget, str):
            widget = self.window.nametowidget(widget.replace("#",""))
        widget.focus()

    def initialize(self, first=False, *args, **kwargs):
        if globals.debug > 1: print("gui.initialize")

        # Disable the colorbar axis for now because it isn't working right now
        #self.controls.axis_controllers['Colorbar'].disable()

        if first and len(sys.argv) > 1:
            self.filenames = sys.argv[1:]
            
        if len(self.filenames) > 0:
            currentfile = self.filecontrols.current_file.get()
            if currentfile in self.filenames:
                self.filecontrols.current_file.set(currentfile)
            else:
                self.filecontrols.current_file.set(self.filenames[0])

            if globals.time_mode: self.read_time_mode()
            else: self.read()

            if not self.controls.initialized: self.controls.initialize()
            xlimits = self.controls.axis_controllers['XAxis'].limits
            ylimits = self.controls.axis_controllers['YAxis'].limits
            
            xadaptive = xlimits.adaptive.get()
            yadaptive = ylimits.adaptive.get()
            if xadaptive and yadaptive:
                self.interactiveplot.reset_xylim(which='both')
            elif xadaptive and not yadaptive:
                self.interactiveplot.reset_xylim(which='xlim')
            elif not xadaptive and yadaptive:
                self.interactiveplot.reset_xylim(which='ylim')
            else:
                xlim, ylim = xlimits.get(), ylimits.get()
                if all(np.isfinite(xlim)):
                    self.interactiveplot.ax.set_xlim(xlimits.get())
                if all(np.isfinite(ylim)):
                    self.interactiveplot.ax.set_ylim(ylimits.get())
            #print(self.controls.axis_controllers['XAxis'].limits.get())
            
            # Set the x and y limits
            #self.interactiveplot.reset_xylim()
            if self.interactiveplot.drawn_object is None:
                self.interactiveplot.update()
            else:
                self.controls.update_button.invoke()
        else:
            self.filecontrols.current_file.set("")
            self.interactiveplot.reset()
            self.interactiveplot.canvas.draw()

        if not globals.time_mode:
            # Make sure none of the axiscontrollers have 't' or 'time' selected
            for controller in self.controls.axis_controllers.values():
                if controller.combobox.textvariable.get() in ['t' or 'time']:
                    for value in controller.combobox['values']:
                        if value not in ['t','time']:
                            controller.combobox.textvariable.set(value)
                            break
        # Allow only linear colorbars for now
        self.controls.axis_controllers['Colorbar'].scale.set('linear')
        self.controls.axis_controllers['Colorbar'].scale.disable()
                        
    """
    def initialize_xy_controls(self):
        if globals.debug > 1: print("gui.initialize_xy_controls")
     
        N = len(self.get_data('x'))
        found_first = False
        for key,val in self.data['data'].items():
            if hasattr(val,"__len__"):
                if len(val) == N:
                    if not found_first:
                        self.controls.axis_controllers['XAxis'].value.set(key)
                        self.controls.axis_controllers['XAxis'].label.set(key)
                        found_first = True
                    else:
                        self.controls.axis_controllers['YAxis'].value.set(key)
                        self.controls.axis_controllers['YAxis'].label.set(key)
                        break
        self.controls.update()
        #self.xy_controls_initialized = True
    """
    def create_variables(self):
        if globals.debug > 1: print("gui.create_variables")
        self.message_text = StringVar(self,None,'message text')
        self.time_mode = BooleanVar(self,globals.time_mode,'time mode')
        
    def create_widgets(self):
        if globals.debug > 1: print("gui.create_widgets")
        
        
        self.left_frame = tk.Frame(self)
        self.interactiveplotframe = tk.Frame(self.left_frame)
        self.interactiveplot = InteractivePlot(
            self.interactiveplotframe,
            self,
            relief='sunken',
            bd=1,
        )
        # Wait until the plot becomes visible to proceed
        self.update_idletasks()
        self.update()

        self.under_plot_frame = tk.Frame(self.left_frame,relief='sunken',bd=1)
        self.plottoolbar = CustomToolbar(self.under_plot_frame,self,self.interactiveplot.canvas)
        
        self.filecontrols = FileControls(
            self.under_plot_frame,
            self,
            self.interactiveplot.canvas,
            bg='white',
            relief='sunken',
            bd=1,
        )
        self.controls = Controls(
            self,
            width=self.interactiveplot.winfo_reqwidth()*0.5,#2.25*self.dpi, # pixels = inches * dpi
            bd=1,
            relief='sunken',
        )

        self.menubar = MenuBar(self.window,self)
        self.message_label = tk.Label(self,textvariable=self.message_text,bg='white')
        
    def place_widgets(self):
        if globals.debug > 1: print("gui.place_widgets")

        self.plottoolbar.pack(side='left',fill='both')
        self.filecontrols.pack(side='left',fill='both',expand=True,padx=3,pady=3)
        self.under_plot_frame.pack(side='bottom',fill='both')

        self.interactiveplot.pack(fill='both',expand=True)
        self.interactiveplotframe.pack(side='top',fill='both',expand=True)
        
        self.controls.pack(side='right',fill='both')
        self.left_frame.pack(side='right',fill='both',expand=True)

        self.message_label.place(rely=1,relx=1,anchor="se")
        self.pack(fill='both',expand=True)

        # Make the controls have a fixed width
        self.controls.pack_propagate(False)

    def create_hotkeys(self, *args, **kwargs):
        if globals.debug > 1: print("gui.create_hotkeys")
        self.hotkeys = Hotkeys(self.window)
        self.hotkeys.bind("update plot", lambda *args,**kwargs: self.controls.update_button.invoke())
        self.hotkeys.bind("import data", lambda *args,**kwargs: ImportData(self))
        self.hotkeys.bind("save", lambda *args,**kwargs: self.plottoolbar.save_figure())
        self.hotkeys.bind("find particle", lambda *args,**kwargs: FindParticle(self))

    def destroy(self, *args, **kwargs):
        if hasattr(self, "message_after_id") and self.message_after_id is not None:
            self.after_cancel(self.message_after_id)
        self.message_after_id = None
        super(GUI,self).destroy(*args, **kwargs)
        
    def message(self,text,duration=2000):
        if globals.debug > 1: print("gui.message")
        # Display a message on the bottom-right hand corner of the window
        # If duration is None then the message will persist forever
        self.message_text.set(text)
        #if duration is not None:
        if self.message_after_id is not None:
            self.after_cancel(self.message_after_id)
        self.message_after_id = self.after(duration, self.clear_message)
    def clear_message(self,*args,**kwargs):
        if globals.debug > 1: print("gui.clear_message")
        self.message_text.set("")
        if self.message_after_id is not None:
            self.after_cancel(self.message_after_id)
        self.message_after_id = None

    def set_user_controlled(self,value):
        if globals.debug > 1: print("gui.set_user_controlled")
        if value:
            self.controls.enable()
            self.filecontrols.enable('all')
            self.plottoolbar.enable()
        else:
            self.controls.disable(temporarily=True)
            self.filecontrols.disable('all')
            self.plottoolbar.disable()
        self.user_controlled = value
    def get_user_controlled(self):
        if globals.debug > 1: print("gui.get_user_controlled")
        return self.user_controlled

    def read(self,*args,**kwargs):
        if globals.debug > 1: print("gui.read")

        if self.time_mode.get():
            raise Exception("gui.read is not allowed in time mode. This should never happen.")
        
        previous_data_length = 0
        if self.data is not None:
            if sys.version_info.major >= 3:
                previous_data_length = len(self.data['data'][next(iter(self.data['data']))])
            else:
                previous_data_length = len(self.data['data'][iter(self.data['data']).next()])

        current_file = self.filecontrols.current_file.get()
        def get_data(*args,**kwargs):
            self._data = Data(read_file(current_file))
        
        self.message("Reading data")
        thread = ThreadedTask(target=get_data)
        root = self.winfo_toplevel()
        while thread.isAlive():
            root.update()
        self.clear_message()
        
        self.display_data = {
            key : self.get_data(key)*self.get_display_units(key) for key in self.data['data'].keys()
        }

        if sys.version_info.major >= 3:
            new_data_length = len(self.data['data'][next(iter(self.data['data']))])
        else:
            new_data_length = len(self.data['data'][iter(self.data['data']).next()])
        if new_data_length != previous_data_length:
            self.interactiveplot.reset_colors()
        
        if self.data.is_image:
            return

        
        # Make sure the data has the required keys for scatter plots
        data_keys = self.data['data'].keys()
        for data_key in ['x','y','z']:
            if data_key not in data_keys:
                break
                #raise ValueError("Could not find required key '"+data_key+"' in the data from read_file")
        else: # If we have all the 'x', 'y', and 'z' keys
            # Perform whatever rotation is needed from us for the display data
            self.rotate()
            
        keys = []
        for key,val in self.data['data'].items():
            if hasattr(val,"__len__"):
                if len(val) == new_data_length: keys.append(key)
                

        if 't' in self.data['data'].keys(): keys.append('t')
        elif 'time' in self.data['data'].keys(): keys.append('time')
                
        colorbar_values = [
            'None',
            'rho',
        ]
        colorbar_extra = [
            'Point Density',
        ]
                
        # Check for requisite keys for colorbar plots
        values = ['']
        ckeys = self.data['data'].keys()
        # All these conditions are required to do integrations through space
        if not (sum([int(key in ckeys) for key in ['x','y','z']]) >= 2 and
            'm' in ckeys and
            'h' in ckeys and
            'rho' in ckeys):
            colorbar_values.pop('rho')
        if len(colorbar_values) == 0:
            # Disable the colorbar controls if we have no values
            self.controls.axis_controllers['Colorbar'].disable()
        else:
            self.controls.axis_controllers['Colorbar'].combobox.configure(values=colorbar_values,extra=colorbar_extra)

        # Update the axis controllers
        for axis_name, axis_controller in self.controls.axis_controllers.items():
            if axis_name != 'Colorbar':
                axis_controller.combobox.configure(values=keys)
                #if axis_controller.value.get() == "":
                #    exclude = []
                #    for ac in self.controls.axis_controllers.values():
                #        if ac is not axis_controller and ac.value.get() != "":
                #            exclude.append(ac.value.get())
                    #axis_controller.value.set(axis_controller.value.get())
                    #for value in axis_controller.combobox.cget('values'):
                        #if value not in exclude:
                        #    axis_controller.value.set(value)
                        #    break

        # Update the time text in the plot, if time data is available
        for name in ['t','time']:
            if name in ckeys:
                time = self.get_data(name)
                if time is not None:
                    self.interactiveplot.time.set(time*self.get_display_units(name))
                break
            
    def read_time_mode(self,*args,**kwargs):
        # Make the data contain *all* the input data values
        self._data_time_mode = {
            'data' : collections.OrderedDict({}),
            'display_units' : collections.OrderedDict({}),
            'physical_units' : collections.OrderedDict({}),
        }

        def get_data(*args,**kwargs):
            total = len(self.filenames)
            for i,filename in enumerate(self.filenames):
                self.message_text.set("Reading data (%3d%%)..." % int(i/total*100))
                d = read_file(filename)

                # Figure out how long the data is
                length = 0
                for key,val in d['data'].items():
                    if key not in ['t','time']:
                        length = len(val)
                        break
                if length == 0: raise Exception("data file '"+filename+"' either only contains time data, or has no data at all")


                for key,val in d['data'].items():
                    if key in ['t','time']: val = np.repeat(val,length)
                    if key not in self._data_time_mode['data'].keys(): self._data_time_mode['data'][key] = [val]
                    else: self._data_time_mode['data'][key] += [val]

                    if key not in self._data_time_mode['display_units'].keys():
                        self._data_time_mode['display_units'][key] = d['display_units'][key]
                    elif self._data_time_mode['display_units'][key] != d['display_units'][key]:
                        raise Exception("the input files have inconsistent data structures. For key '"+key+"', we previously found display units of '"+self._data_time_mode['display_units'][key]+"', but file '"+filename+"' has display units of '"+d['display_units'][key]+"' for this key.")

                    if key not in self._data_time_mode['physical_units'].keys():
                        self._data_time_mode['physical_units'][key] = d['physical_units'][key]
                    elif self._data_time_mode['physical_units'][key] != d['physical_units'][key]:
                        raise Exception("the input files have inconsistent data structures. For key '"+key+"', we previously found physical units of '"+self._data_time_mode['display_units'][key]+"', but file '"+filename+"' has physical units of '"+d['display_units'][key]+"' for this key.")

            total = len(self._data_time_mode['data'].keys())
            for i,(key, val) in enumerate(self._data_time_mode['data'].items()):
                self.message_text.set("Flattening data arrays (%3d%%)..." % int(i/total*100))
                self._data_time_mode['data'][key] = np.array(val).flatten()
            self._data_time_mode = Data(self._data_time_mode)

            self.message_text.set("Setting up display data arrays...")
            self._display_data_time_mode = {
                key : self.get_data(key)*self.get_display_units(key) for key in self._data_time_mode['data'].keys()
            }

        self.set_user_controlled(False)
        #self.message_text.set("Reading all input data...")
        thread = ThreadedTask(target=get_data)
        root = self.winfo_toplevel()
        while thread.isAlive():
            root.update()
        self.clear_message()
        self.set_user_controlled(True)

    def get_data(self,key):
        if globals.debug > 1: print("gui.get_data")
        if self.data is None: return None
        elif self.data.is_image: return self.data
        else:
            data = self.data['data'][key]
            if key == 'h': return data*globals.compact_support
            else: return data

    def get_display_units(self,key):
        if globals.debug > 1: print("gui.get_display_units")
        return self.data['display_units'][key]
    
    def get_physical_units(self,key):
        if globals.debug > 1: print("gui.get_physical_units")
        return self.data['physical_units'][key]

    def get_display_data(self,key,raw=False,identifier=None,scaled=True):
        if globals.debug > 1: print("gui.get_display_data")

        if raw: return self.display_data[key]
        else: # Apply the axis scale and units to the data
            # Check to see if the key matches
            xaxis = self.controls.axis_controllers['XAxis'].value.get()
            yaxis = self.controls.axis_controllers['YAxis'].value.get()
            caxis = self.controls.axis_controllers['Colorbar'].value.get()
            controller = None
            if identifier is None: identifier = key
            if identifier == xaxis: controller = self.controls.axis_controllers['XAxis']
            elif identifier == yaxis: controller = self.controls.axis_controllers['YAxis']
            elif identifier == caxis: controller = self.controls.axis_controllers['Colorbar']
            if controller is not None:
                units = controller.units.value.get()
                if scaled:
                    scale = controller.scale.get()
                    if scale == 'linear': return self.display_data[key]/units
                    elif scale == 'log10': return np.log10(self.display_data[key]/units)
                    elif scale == '^10': return 10**(self.display_data[key]/units)
                    else:
                        raise RuntimeError("The AxisController '"+controller+"' has scale '"+scale+"', which is not one of 'linear', 'log10', or '^10'")
                else: return self.display_data[key]/units
            return self.display_data[key]

    def rotate(self,anglexdeg=None,angleydeg=None,anglezdeg=None):
        if globals.debug > 1: print("gui.rotate")
        if self.data.is_image:
            print("Cannot perform rotations on data that have been identified as an image with is_image = True")
            return

        # Perform the rotation specified in the plot controls
        if anglexdeg is None: anglexdeg = self.controls.plotcontrols.rotation_x.get()
        if angleydeg is None: angleydeg = self.controls.plotcontrols.rotation_y.get()
        if anglezdeg is None: anglezdeg = self.controls.plotcontrols.rotation_z.get()

        # We just need to rotate the display data
        if self.display_data is not None:
            keys = self.display_data.keys()
            if 'x' in keys and 'y' in keys and 'z' in keys:
                x = self.data._original['data']['x']
                y = self.data._original['data']['y']
                z = self.data._original['data']['z']
                self.display_data['x'],self.display_data['y'],self.display_data['z'] = rotate(x,y,z,anglexdeg,angleydeg,anglezdeg)
            else:
                print("Cannot perform rotations on data that do not contain all fields 'x', 'y', and 'z'")

    def make_movie(self, *args, **kwargs):
        if globals.debug > 1: print("gui.make_movie")
        make_movie(self)
            
    def make_rotation_movie(self,*args,**kwargs):
        if globals.debug > 1: print("gui.make_rotation_movie")
        make_rotation_movie(self)

    #def set_preference(self,key,value):
    #    if globals.debug > 1: print("gui.set_preference")
    #    self.preferences[key] = value

    #def get_preference(self,key):
    #    if globals.debug > 1: print("gui.get_preference")
    #    if key in self.preferences.keys():
    #        return self.preferences[key]
    #    else:
    #        return None
        
    #def save_preferences(self,*args,**kwargs):
    #    if globals.debug > 1: print("gui.save_preferences")
    #    with open(self.preferences_path,'w') as f:
    #        json.dump(self.preferences, f, indent=4)

    #def load_preferences(self,*args,**kwargs):
    #    if globals.debug > 1: print("gui.load_preferences")
    #    if not os.path.isfile(self.preferences_path): return
    #    with open(self.preferences_path,'r') as f:
    #        f.seek(0,2)
    #        filesize = f.tell()
    #        f.seek(0)
    #        if filesize == 0: self.preferences = {}
    #        else: self.preferences = json.load(f)

    def update_filenames(self,*args,**kwargs):
        if globals.debug > 1: print("gui.update_filenames")
        tmp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"tmp")
        if not os.path.isdir(tmp_path): os.mkdir(tmp_path)
        for filename in sorted(os.listdir(tmp_path)):
            if filename not in self.filenames:
                self.filenames.append(os.path.join(tmp_path,filename))

    # When 't' (time) is selected on one of the axes, change global behavior
    # to show only Point Density plots
    def toggle_time_mode(self, *args, **kwargs):
        if globals.debug > 1: print("gui.toggle_time_mode")
        globals.time_mode = self.time_mode.get()
        if self.time_mode.get(): self.enable_time_mode()
        else: self.disable_time_mode()
        # Stale the axis controllers so that we obtain the correct data
        # (the shape of the data has changed now)
        for controller in self.controls.axis_controllers.values():
            controller.stale = True
    
    def enable_time_mode(self, *args, **kwargs):
        if globals.debug > 1: print("gui.enable_time_mode")
        # Setup the controls
        self.controls.axis_controllers['Colorbar'].combobox.textvariable.set("Point Density")
        self.controls.axis_controllers['Colorbar'].combobox.configure(state='disabled')

        if self.filecontrols.current_file in globals.state_variables:
            globals.state_variables.remove(self.filecontrols.current_file)
        
        self.filecontrols.disable('all')
        self.previous_file = self.filecontrols.current_file.get()
        self.filecontrols.current_file.set("Time Mode")

        self.interactiveplot.clear_tracking()
        
        if self._data_time_mode is None or self._display_data_time_mode is None: self.read_time_mode()
        self.interactiveplot.reset()

    def disable_time_mode(self, *args, **kwargs):
        if globals.debug > 1: print("gui.disable_time_mode")
        self.controls.axis_controllers['Colorbar'].combobox.configure(state='enabled')
        self.filecontrols.enable('all')

        if self.previous_file is not None:
            self.filecontrols.current_file.set(self.previous_file)
            self.previous_file = None

        if self.filecontrols.current_file not in globals.state_variables:
            globals.state_variables.append(self.filecontrols.current_file)

