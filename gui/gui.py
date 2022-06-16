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
from functions.importdata import importdata
from functions.findparticle import findparticle
from functions.rotate import rotate
from lib.threadedtask import ThreadedTask
from lib.hotkeys import Hotkeys
from hotkeyslist import hotkeyslist

from read_file import read_file
import globals
import copy
import os.path
import json
import os
import numpy as np

class GUI(tk.Frame,object):
    def __init__(self,window,fontname='TkDefaultFont',fontsize=12):
        if globals.debug > 1: print("gui.__init__")
        self.window = window
        self.fontname = fontname
        self.fontsize = fontsize

        # Turn this on and off to indicate that edits are being
        # made from the code rather than from the user
        self.user_controlled = True

        # Capture the filenames from the execution arguments
        #if len(sys.argv[1:]) == 0:
        #    raise RuntimeError("No filenames provided")
        
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
        
        self.data = None
        self.display_data = None
        
        self.preferences = {}
        self.preferences_file = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"preferences.json")

        self.load_preferences()

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        # When the user clicks on widgets etc, those widgets should acquire
        # the application focus... (why isn't this default?!)
        self.window.bind("<Button-1>", self.on_button1)
        
        self.create_hotkeys()

        self.filenames = []
        self.message_after_id = None
        
        #self.xy_controls_initialized = False
        self.initialize(first=True)
        self.controls.connect()

    def on_button1(self, event):
        if globals.debug > 1: print("gui.on_button1")
        widget = event.widget
        # Clicking on the menubar gives a strange event.widget
        if isinstance(widget, str):
            widget = self.window.nametowidget(widget.replace("#",""))
        widget.focus()

    def initialize(self, first=False, *args, **kwargs):
        if globals.debug > 1: print("gui.initialize")

        if first and len(sys.argv) > 1:
            self.filenames = sys.argv[1:]

        if len(self.filenames) > 0:
            currentfile = self.filecontrols.current_file.get()
            if currentfile in self.filenames:
                self.filecontrols.current_file.set(currentfile)
            else:
                self.filecontrols.current_file.set(self.filenames[0])
            
            self.read()

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
                self.interactiveplot.ax.set_xlim(xlimits.get())
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
        self.message_text = tk.StringVar()
        
    def create_widgets(self):
        if globals.debug > 1: print("gui.create_widgets")
        
        
        self.left_frame = tk.Frame(self)
        self.interactiveplot = InteractivePlot(
            self.left_frame,
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

        self.interactiveplot.pack(side='top',fill='both',expand=True)

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
        self.hotkeys.bind("import data", lambda *args,**kwargs: importdata(self))
        self.hotkeys.bind("save", lambda *args,**kwargs: self.plottoolbar.save_figure())
        self.hotkeys.bind("find particle", lambda *args,**kwargs: findparticle(self))

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
        else:
            self.controls.disable(temporarily=True)
            self.filecontrols.disable('all')
        self.user_controlled = value
    def get_user_controlled(self):
        if globals.debug > 1: print("gui.get_user_controlled")
        return self.user_controlled

    def read(self,*args,**kwargs):
        if globals.debug > 1: print("gui.read")
        previous_data_length = 0
        if self.data is not None:
            if sys.version_info.major >= 3:
                previous_data_length = len(self.data['data'][next(iter(self.data['data']))])
            else:
                previous_data_length = len(self.data['data'][iter(self.data['data']).next()])

        current_file = self.filecontrols.current_file.get()
        def get_data(*args,**kwargs):
            self.data = Data(read_file(current_file))
        
        self.message("Reading data")
        thread = ThreadedTask(target=get_data)
        root = self.winfo_toplevel()
        while thread.isAlive():
            root.update()
        self.clear_message()
        
        self.display_data = {
            key : self.get_data(key)*self.get_display_units(key) for key in self.data['data'].keys()
        }
        self.physical_data = {
            key : self.get_data(key)*self.get_physical_units(key) for key in self.data['data'].keys()
        }

        if sys.version_info.major >= 3:
            new_data_length = len(self.data['data'][next(iter(self.data['data']))])
        else:
            new_data_length = len(self.data['data'][iter(self.data['data']).next()])
        if new_data_length != previous_data_length:
            self.interactiveplot.reset_colors()
        
        # Enable the colorbar
        self.controls.axis_controllers['Colorbar'].enable()
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
        
        # Check for requisite keys for colorbar plots
        values = ['']
        ckeys = self.data['data'].keys()
        for key in ['x','y','m','h','rho']:
            if key not in ckeys:
                # Disable the colorbar controls if we are missing any of these
                self.controls.axis_controllers['Colorbar'].disable()
                break

        # Update the axis controllers
        for axis_name, axis_controller in self.controls.axis_controllers.items():
            if axis_name != 'Colorbar':
                axis_controller.combobox.configure(values=keys)
                if axis_controller.value.get() == "":
                    exclude = []
                    for ac in self.controls.axis_controllers.values():
                        if ac is not axis_controller and ac.value.get() != "":
                            exclude.append(ac.value.get())
                    for value in axis_controller.combobox.cget('values'):
                        if value not in exclude:
                            axis_controller.value.set(value)
                            break

        # Update the time text in the plot, if time data is available
        for name in ['t','time']:
            if name in ckeys:
                time = self.get_data(name)
                if time is not None:
                    self.interactiveplot.time.set(time*self.get_display_units(name))
                break

    def get_data(self,key):
        if globals.debug > 1: print("gui.get_data")
        if self.data is None: return None
        elif self.data.is_image: return self.data
        else:
            #data = copy.copy(self.data['data'][key])
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

    def set_preference(self,key,value):
        if globals.debug > 1: print("gui.set_preference")
        self.preferences[key] = value

    def get_preference(self,key):
        if globals.debug > 1: print("gui.get_preference")
        if key in self.preferences.keys():
            return self.preferences[key]
        else:
            return None
        
    def save_preferences(self,*args,**kwargs):
        if globals.debug > 1: print("gui.save_preferences")
        with open(self.preferences_file,'w') as f:
            json.dump(self.preferences, f, indent=4)

    def load_preferences(self,*args,**kwargs):
        if globals.debug > 1: print("gui.load_preferences")
        if not os.path.isfile(self.preferences_file): return
        with open(self.preferences_file,'r') as f:
            f.seek(0,2)
            filesize = f.tell()
            f.seek(0)
            if filesize == 0: self.preferences = {}
            else: self.preferences = json.load(f)

    def update_filenames(self,*args,**kwargs):
        if globals.debug > 1: print("gui.update_filenames")
        tmp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"tmp")
        if not os.path.isdir(tmp_path): os.mkdir(tmp_path)
        for filename in sorted(os.listdir(tmp_path)):
            if filename not in self.filenames:
                self.filenames.append(os.path.join(tmp_path,filename))

