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
from functions.setwidgetstatepermanent import set_widget_state_permanent
from functions.getpreference import get_preference
from lib.threadedtask import ThreadedTask
from lib.hotkeys import Hotkeys
from hotkeyslist import hotkeyslist
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
from widgets.autosizelabel import AutoSizeLabel
from widgets.message import Message

from gui.guiwidgetcontroller import GUIWidgetController

from read_file import read_file
import globals
import kernel
import copy
import os.path
import json
import os
import numpy as np
import collections


class GUI(tk.Frame,object):
    def __init__(self,window,fontname='TkDefaultFont',fontsize=12):
        if globals.debug > 1: print("gui.__init__")

        self.filenames = []
        if len(sys.argv) > 1:
            self.filenames = sys.argv[1:]

        self.window = window
        
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
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.widget_controller = GUIWidgetController(self)

        self.controls.axis_controllers['Colorbar'].combobox.configure(values=[],extra=[''])

        # When the user clicks on widgets etc, those widgets should acquire
        # the application focus... (why isn't this default?!)
        self.window.bind("<Button-1>", self.on_button1)
        
        self.create_hotkeys()

        #self.message_after_id = None

        if not globals.time_mode: self.time_mode.set(False)

        self.previous_file = None
        self.time_mode.trace('w',self.toggle_time_mode)

        self.compact_support_set = False
        
        #self.xy_controls_initialized = False
        self.initialize(first=True)
        self.controls.connect()

    @property
    def data(self): return self._data
    @data.setter
    def data(self,value):
        if not isinstance(value, (dict, type(None))):
            raise TypeError("can only set data to type 'dict' or 'None', not '"+type(value).__name__+"'")

        previous_data = self._data
        mask = None
        if previous_data is not None and not previous_data.is_image:
            mask = previous_data._mask
        
        # Don't apply a mask in time mode (for now)
        if self.time_mode.get(): mask = None
        
        if value is None:
            self.menubar.data.disable()
            self.menubar.particle.disable()
            self.menubar.functions.disable()
        else:
            value = Data(value,mask=mask)
            self.menubar.data.enable()
            self.menubar.particle.enable()
            self.menubar.functions.enable()

        self.has_data.set(value is not None)
        self.data_is_image.set(value.is_image)
            
        self._data = value
        self.event_generate("<<DataChanged>>")

    def on_button1(self, event):
        if globals.debug > 1: print("gui.on_button1")
        widget = event.widget
        # Clicking on the menubar gives a strange event.widget
        if isinstance(widget, str):
            widget = self.window.nametowidget(widget.replace("#",""))
        widget.focus()

    def initialize(self, first=False, *args, **kwargs):
        if globals.debug > 1: print("gui.initialize")
        
        if first:
            # Setup the limits on the interactive plot using user's preferences
            self.interactiveplot.ax.set_xlim(self.controls.axis_controllers['XAxis'].limits.get())
            self.interactiveplot.ax.set_ylim(self.controls.axis_controllers['YAxis'].limits.get())
            self.interactiveplot.colorbar.set_clim(self.controls.axis_controllers['Colorbar'].limits.get())

            if self.interactiveplot.tracking:
                for name in ['XAxis','YAxis']:
                    set_widget_state_permanent(self.controls.axis_controllers[name].limits.adaptive_button, ['disabled'])

            self.interactiveplot.colorbar.update_cmap(self.controls.colorbar_cmap.get())
            self.controls.colorbar_cmap_combobox.bind("<<ComboboxSelected>>", lambda *args, **kwargs: self.interactiveplot.colorbar.update_cmap(self.controls.colorbar_cmap.get()), add="+")
            self.controls.colorbar_cmap.set(self.interactiveplot.colorbar.cmap.name)
        
        if len(self.filenames) > 0:
            currentfile = self.filecontrols.current_file.get()
            currentfile_is_in_list = currentfile in self.filenames
            if currentfile_is_in_list:
                self.filecontrols.current_file.set(currentfile)
            else:
                self.filecontrols.current_file.set(self.filenames[0])

            #if globals.time_mode: self.read_time_mode()
            #else: self.read()

            self.read(first=first)
            
            # Don't allow the axis controllers to start out in time mode (for now)
            for axis_controller in self.controls.axis_controllers.values():
                values = axis_controller.combobox['values']
                if values[axis_controller.combobox.current()] in ['t','time','Time']:
                    axis_controller.combobox.next()
                    axis_controller.combobox.event_generate("<<ComboboxSelected>>")
                    #axis_controller.value.set(axis_controller.combobox['values'][axis_controller.combobox.current()])
                    # Set the label too, if the user hasn't typed their own label
                    #if axis_controller.label.get() in values: axis_controller.label.set(v)
                    # Make sure the colorbar is no longer Point Density
                    if self.controls.axis_controllers['Colorbar'].value.get() == "Point Density":
                        self.controls.axis_controllers['Colorbar'].combobox.set("")
                    #for v in values:
                    #    if v not in ['t','time','Time']:
                    #        axis_controller.value.set(v)
                    #        #axis_controller.combobox.set(v)
                            
                            
                    #        break

            if not self.data.is_image:
                if currentfile_is_in_list:
                    colors = get_preference(self.interactiveplot, "colors")
                    if colors is not None:
                        uniq = np.unique(colors)
                        for uniq in np.unique(colors):
                            particles = np.where(colors == uniq)
                            self.interactiveplot.color_particles(None, particles=np.where(colors==uniq), index=uniq, update=False)
            
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

            if self.interactiveplot.tracking and self.data.is_image:
                self.interactiveplot.clear_tracking()
                    
            self.interactiveplot.update()

            self.controls.update_colorbar_controller()
        else:
            self.filecontrols.current_file.set("")
            self.interactiveplot.reset()
            
            # Clear the comboboxes, as there's no data to use here
            for controller in self.controls.axis_controllers.values():
                controller.combobox.textvariable.set("")
                controller.label.set("")
        
        self.controls.update_xaxis_controller()
        self.controls.update_yaxis_controller()

        #print(self.controls.axis_controllers['XAxis'].combobox.get())

        #if len(self.filenames) > 0:
            

        # Show the orientation arrows if the user's preferences have them set on
        if self.controls.plotcontrols.show_orientation.get():
            self.interactiveplot.orientation.switch_on()

        if first:
            # Connect the colorbar to its axis controller
            self.interactiveplot.colorbar.connect_controller(self.controls.axis_controllers['Colorbar'])


    def create_variables(self):
        if globals.debug > 1: print("gui.create_variables")
        #self.message_text = tk.StringVar()
        self.time_mode = BooleanVar(self,globals.time_mode,"time mode")
        self.has_data = tk.BooleanVar(value=False)
        self.data_is_image = tk.BooleanVar(value=False)
        
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
        self.message = Message(self,"se",bg='white')

    def place_widgets(self):
        if globals.debug > 1: print("gui.place_widgets")

        self.plottoolbar.pack(side='left',fill='both')
        self.filecontrols.pack(side='left',fill='both',expand=True,padx=3,pady=3)
        self.under_plot_frame.pack(side='bottom',fill='both')

        self.interactiveplot.pack(fill='both',expand=True)
        self.interactiveplotframe.pack(side='top',fill='both',expand=True)
        
        self.controls.pack(side='right',fill='both')
        self.left_frame.pack(side='right',fill='both',expand=True)

        self.pack(fill='both',expand=True)

        # Make the controls have a fixed width
        self.controls.pack_propagate(False)

    def create_hotkeys(self, *args, **kwargs):
        if globals.debug > 1: print("gui.create_hotkeys")
        self.hotkeys = Hotkeys(self.window)
        self.hotkeys.bind("update plot", lambda *args,**kwargs: self.controls.update_button.invoke())
        
    def set_user_controlled(self,value):
        if globals.debug > 1: print("gui.set_user_controlled")
        if value:
            #self.controls.enable()
            self.filecontrols.enable('all')
            self.plottoolbar.enable()
        else:
            #self.controls.disable(temporarily=True)
            self.filecontrols.disable('all')
            self.plottoolbar.disable()
        self.user_controlled = value
    def get_user_controlled(self):
        if globals.debug > 1: print("gui.get_user_controlled")
        return self.user_controlled

    def read(self,*args,**kwargs):
        if globals.debug > 1: print("gui.read")
        
        if globals.time_mode:
            raise Exception("gui.read is not allowed in time mode. This should never happen.")
        
        previous_data_length = 0
        if self.data is not None and not self.data.is_image:
            if sys.version_info.major >= 3:
                previous_data_length = len(self.data['data'][next(iter(self.data['data']))])
            else:
                previous_data_length = len(self.data['data'][iter(self.data['data']).next()])
        
        current_file = self.filecontrols.current_file.get()
        self._temp = None
        def get_data(*args,**kwargs):
            self._temp = read_file(current_file)
        
        self.message("Reading data",duration=None)
        thread = ThreadedTask(target=get_data)
        root = self.winfo_toplevel()
        while thread.isAlive():
            root.update()
        thread.stop()
        self.message.clear(check="Reading data")
        
        # We can't update the data property of this class from the spawned thread,
        # so instead we obtain self._data and then assign self.data to that.
        self.data = self._temp

        if self.data.is_image:
            self.controls.axis_controllers['XAxis'].value.set("")
            self.controls.axis_controllers['YAxis'].value.set("")
            self.controls.axis_controllers['Colorbar'].value.set("")
            return

        
        if sys.version_info.major >= 3:
            new_data_length = len(self.data['data'][next(iter(self.data['data']))])
        else:
            new_data_length = len(self.data['data'][iter(self.data['data']).next()])
        if new_data_length != previous_data_length and not kwargs.get('first',False):
            self.interactiveplot.reset_colors()
            self.interactiveplot.clear_particle_annotations()

        
        
        # Make sure the data has the required keys for scatter plots
        data_keys = self.data['data'].keys()
        if self.data.has_variables('x','y','z'):
            rotationx = self.controls.plotcontrols.rotation_x.get()
            rotationy = self.controls.plotcontrols.rotation_y.get()
            rotationz = self.controls.plotcontrols.rotation_z.get()
            if rotationx != 0 or rotationy != 0 or rotationz != 0:
                # Perform whatever rotation is needed from us for the display data
                self.data.rotate(rotationx,rotationy,rotationz)

        if sys.version_info.major >= 3:
            data_length = len(self.data['data'][next(iter(self.data['data']))])
        else:
            data_length = len(self.data['data'][iter(self.data['data']).next()])
        keys = []
        for key,val in self.data['data'].items():
            if hasattr(val,"__len__"):
                if len(val) == data_length: keys.append(key)

        extra = []
        if 't' in self.data['data'].keys(): extra.append('t')
        elif 'time' in self.data['data'].keys(): extra.append('time')
        
        colorbar_values = [
            'Point Density',
        ]
        
        self.controls.axis_controllers['Colorbar'].combobox.configure(values=colorbar_values)
        
        # Update the axis controllers
        self.controls.axis_controllers['XAxis'].combobox.configure(values=keys, extra=extra)
        self.controls.axis_controllers['YAxis'].combobox.configure(values=keys)
        
        # Update the time text in the plot, if time data is available
        if not globals.time_mode:
            for name in ['t','time','Time']:
                time = self.get_data(name)
                if time is not None:
                    self.interactiveplot.time.set(time*self.get_display_units(name))
                break

    """
    def read_time_mode(self,*args,**kwargs):
        if globals.debug > 1: print("gui.read_time_mode")
        
        # Make the data contain *all* the input data values
        data = {
            'data' : collections.OrderedDict({}),
            'display_units' : collections.OrderedDict({}),
            'physical_units' : collections.OrderedDict({}),
        }

        self._temp = None

        def get_data(*args,**kwargs):
            total = len(self.filenames)
            for i,filename in enumerate(self.filenames):
                self.message("Reading data (%3d%%)..." % int(i/total*100), duration=None)
                d = read_file(filename)

                if 'compact_support' in data.keys():
                    if d.get('compact_support',data['compact_support']) != data['compact_support']:
                        raise ValueError("compact_support value mismatch")
                elif 'compact_support' in d.keys():
                    if 'compact_support' not in data.keys():
                        data['compact_support'] = d['compact_support']
                
                # Figure out how long the data is
                length = 0
                for key,val in d['data'].items():
                    if key not in ['t','time','Time']:
                        length = len(val)
                        break
                if length == 0: raise Exception("data file '"+filename+"' either only contains time data, or has no data at all")

                for key,val in d['data'].items():
                    if key in ['t','time','Time']: val = np.repeat(val,length)
                    if key not in data['data'].keys(): data['data'][key] = [val]
                    else: data['data'][key] += [val]

                    if key not in data['display_units'].keys():
                        data['display_units'][key] = d['display_units'][key]
                    elif data['display_units'][key] != d['display_units'][key]:
                        raise Exception("the input files have inconsistent data structures. For key '"+key+"', we previously found display units of '"+data['display_units'][key]+"', but file '"+filename+"' has display units of '"+d['display_units'][key]+"' for this key.")

                    if key not in data['physical_units'].keys():
                        data['physical_units'][key] = d['physical_units'][key]
                    elif data['physical_units'][key] != d['physical_units'][key]:
                        raise Exception("the input files have inconsistent data structures. For key '"+key+"', we previously found physical units of '"+data['display_units'][key]+"', but file '"+filename+"' has physical units of '"+d['display_units'][key]+"' for this key.")

            total = len(data['data'].keys())
            for i,(key, val) in enumerate(data['data'].items()):
                self.message("Flattening data arrays (%3d%%)..." % int(i/total*100), duration=None)
                data['data'][key] = np.array(val).flatten()
            self._temp = data
            
            self.message("Setting up display data arrays...", duration=None)

        self.set_user_controlled(False)

        thread = ThreadedTask(target=get_data)
        root = self.winfo_toplevel()
        while thread.isAlive():
            root.update()
        
        # We can't update the data property of this class from the spawned thread,
        # so instead we obtain self._data and then assign self.data to that.
        self.data = self._temp
        
        self.set_user_controlled(True)
        self.message.clear(check="Setting up display data arrays...")
    """
    
    def get_data(self,key):
        if globals.debug > 1: print("gui.get_data")
        if self.data is None: return None
        if self.data.is_image: return self.data
        return self.data['data'][key]

    def get_display_units(self,key):
        if globals.debug > 1: print("gui.get_display_units")
        return self.data['display_units'][key]
    
    def get_physical_units(self,key):
        if globals.debug > 1: print("gui.get_physical_units")
        return self.data['physical_units'][key]

    def get_physical_data(self, key):
        if globals.debug > 1: print("gui.get_physical_data")
        return self.get_data(key) * self.get_physical_units(key)

    def get_display_data(self,key,raw=False,identifier=None,scaled=True):
        if globals.debug > 1: print("gui.get_display_data")

        if raw: return self.get_data(key) * self.get_display_units(key)
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
                    if scale == 'linear': return self.get_data(key) * self.get_display_units(key) / units
                    elif scale == 'log10': return np.log10(self.get_data(key) * self.get_display_units(key) / units)
                    elif scale == '10^': return 10**(self.get_data(key) * self.get_display_units(key) / units)
                    else:
                        raise RuntimeError("The AxisController '"+controller+"' has scale '"+scale+"', which is not one of 'linear', 'log10', or '10^'")
                else: return self.get_data(key) * self.get_display_units(key) / units
            return self.get_data(key) * self.get_display_units(key)

    def make_movie(self, *args, **kwargs):
        if globals.debug > 1: print("gui.make_movie")
        make_movie(self)
            
    def make_rotation_movie(self,*args,**kwargs):
        if globals.debug > 1: print("gui.make_rotation_movie")
        make_rotation_movie(self)

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

        time_mode = self.time_mode.get()

        if not globals.time_mode and time_mode: self.enable_time_mode(*args,**kwargs)
        elif globals.time_mode and not time_mode: self.disable_time_mode(*args,**kwargs)
        else: return
    
    def enable_time_mode(self, *args, **kwargs):
        if globals.debug > 1: print("gui.enable_time_mode")

        globals.time_mode = True
        
        # Setup the controls
        self.controls.axis_controllers['Colorbar'].combobox.textvariable.set("Point Density")
        self.menubar.particle.disable()
        
        if self.filecontrols.current_file in globals.state_variables:
            globals.state_variables.remove(self.filecontrols.current_file)
        self.previous_file = self.filecontrols.current_file.get()
        self.filecontrols.current_file.set("Time Mode")

        self.interactiveplot.clear_tracking()
        self.interactiveplot.clear_particle_annotations()
        if 'time' in self.interactiveplot.plot_annotations.keys():
            self.interactiveplot.plot_annotations.remove('time')

        # Stale the axis controllers so that we obtain the correct data
        # (the shape of the data has changed now)
        for controller in self.controls.axis_controllers.values():
            controller.stale = True

        self.event_generate("<<TimeModeEnabled>>")

    def disable_time_mode(self, *args, **kwargs):
        if globals.debug > 1: print("gui.disable_time_mode")

        globals.time_mode = False

        self.menubar.particle.enable()

        if self.previous_file is not None:
            self.filecontrols.current_file.set(self.previous_file)
            self.previous_file = None

        if self.filecontrols.current_file not in globals.state_variables:
            globals.state_variables.append(self.filecontrols.current_file)

        # Stale the axis controllers so that we obtain the correct data
        # (the shape of the data has changed now)
        for controller in self.controls.axis_controllers.values():
            controller.stale = True

        self.event_generate("<<TimeModeDisabled>>")

