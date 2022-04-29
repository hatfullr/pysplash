import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    from tkFont import Font as tkFont
    from filecontrols import FileControls
    from interactiveplot import InteractivePlot
    from controls import Controls
else:
    import tkinter as tk
    import tkinter.font as tkFont
    from gui.filecontrols import FileControls
    from gui.interactiveplot import InteractivePlot
    from gui.controls import Controls

from lib.data import Data
from read_file import read_file
import globals
from gui.customtoolbar import CustomToolbar
from widgets.menubar import MenuBar
from gui.menubar.functionsmenubar import FunctionsMenuBar
from gui.menubar.datamenubar import DataMenuBar
from functions.make_rotation_movie import make_rotation_movie
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
        
        self.preferences = {}
        self.preferences_file = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"preferences.json")

        self.load_preferences()
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        

        #self.plottoolbar.toolbar.set_message = lambda text: self.interactiveplot.xycoords.set(text)
        
        self.filecontrols.next_button.configure(command=self.next_file)
        self.filecontrols.back_button.configure(command=self.previous_file)

        all_mapped = False
        while not all_mapped:
            self.update()
            for child in self.get_all_children():
                if child.winfo_exists() == 0:
                    break
            else:
                all_mapped = True

        
        
        #self.filecontrols.current_file.trace("w",self.read)
        if len(sys.argv) > 1:
            self.filenames = sys.argv[1:]
            self.filecontrols.current_file.set(sys.argv[1])
            self.read()
            
            # Set the x and y limits
            xmargin, ymargin = self.interactiveplot.ax.margins()
            xlim = self.data.xlim()
            ylim = self.data.ylim()
            dx = (xlim[1]-xlim[0])*xmargin
            dy = (ylim[1]-ylim[0])*ymargin
            self.interactiveplot.ax.set_xlim(xlim[0]-dx,xlim[1]+dx)
            self.interactiveplot.ax.set_ylim(ylim[0]-dy,ylim[1]+dy)
            
            self.interactiveplot.update()
        else:
            self.filenames = []

        self.controls.connect()

        # Turn on adaptive limits in x and y initially
        #for name in self.controls.axis_names[:2]:
        #    self.controls.axis_controllers[name].limits.adaptive_on()
        
        self.controls.save_state()
        
    def initialize_xy_controls(self):
        if globals.debug > 1: print("gui.initialize_xy_controls")

        self.controls.disconnect_state_listeners()
        
        N = len(self.get_data('x'))
        found_first = False
        for key,val in self.data['data'].items():
            if hasattr(val,"__len__"):
                if len(val) == N:
                    if not found_first:
                        self.controls.axis_controllers['XAxis'].value.set(key)
                        found_first = True
                    else:
                        self.controls.axis_controllers['YAxis'].value.set(key)
                        break
        self.controls.update()
        self.controls.connect_state_listeners()

    def create_variables(self):
        if globals.debug > 1: print("gui.create_variables")
        self.message_text = tk.StringVar()
        
    def create_widgets(self):
        if globals.debug > 1: print("gui.create_widgets")
        self.menubar = MenuBar(self.window,self)
        self.menubar.add_cascade(
            label="Functions",
            menu=FunctionsMenuBar(self.menubar,self),
        )
        self.menubar.add_cascade(
            label="Data",
            menu=DataMenuBar(self.menubar,self),
        )
        
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
            self.interactiveplot.canvas,
            bg='white',
            relief='sunken',
            bd=1,
        )
        self.controls = Controls(
            self,
            width=2*self.dpi, # pixels = inches * dpi
            bd=1,
            relief='sunken',
            padx=5,
            pady=5,
        )
        
        self.message_label = tk.Label(self,textvariable=self.message_text,bg='white')
        
    def place_widgets(self):
        if globals.debug > 1: print("gui.place_widgets")

        self.plottoolbar.pack(side='left',fill='x')
        self.filecontrols.pack(side='left',fill='x',expand=True)
        self.under_plot_frame.pack(side='bottom',fill='both',expand=True)

        self.interactiveplot.pack(side='top',fill='both',expand=True)

        self.controls.pack(side='right',fill='both')
        self.left_frame.pack(side='right',fill='both',expand=True)

        self.message_label.place(rely=1,relx=1,anchor="se")
        self.pack(fill='both',expand=True)

    def message(self,text,*args,**kwargs):
        if globals.debug > 1: print("gui.message")
        # Display a message on the bottom-right hand corner of the window
        self.message_text.set(text)
    def clear_message(self,*args,**kwargs):
        if globals.debug > 1: print("gui.clear_message")
        self.message_text.set("")

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

    def do_after(self,amount,todo,trigger,args=[],kwargs={}):
        if globals.debug > 1: print("gui.do_after")
        if not trigger():
            self.after(amount,lambda amt=amount,td=todo,trig=trigger,arrgs=args,kwarrgs=kwargs: self.do_after(amt,td,trig,arrgs,kwarrgs))
        else:
            todo(*args,**kwargs)

    def read(self,*args,**kwargs):
        if globals.debug > 1: print("gui.read")
        self.data = Data(
            read_file(self.filecontrols.current_file.get()),
            #rotations=(self.controls.rotation_x.get(),self.controls.rotation_y.get(),self.controls.rotation_z.get()),
        )

        if self.data.is_image:
            return

        
        # Make sure the data has the required keys for scatter plots
        data_keys = self.data['data'].keys()
        for data_key in ['x','y','z']:
            if data_key not in data_keys:
                raise ValueError("Could not find required key '"+data_key+"' in the data from read_file")

        keys = []
        N = len(self.data['data']['x'])
        for key,val in self.data['data'].items():
            if hasattr(val,"__len__"):
                if len(val) == N: keys.append(key)
        
        # Check for requisite keys for colorbar plots
        values = ['None']
        ckeys = self.data['data'].keys()
        for key in ['x','y','m','h','rho']:
            if key not in ckeys: break
        else: values.append("Column density")
        for key in ['x','y','m','h','rho','opacity']:
            if key not in ckeys: break
        else: values.append("Optical depth")

        # Update the axis controllers
        for axis_name, axis_controller in self.controls.axis_controllers.items():
            if axis_name != 'Colorbar':
                axis_controller.combobox.configure(values=keys)
        self.controls.axis_controllers['Colorbar'].combobox.configure(values=values)

        self.initialize_xy_controls()

    def get_data(self,key):
        if globals.debug > 1: print("gui.get_data")
        if self.data is None:
            return None
        else:
            if self.data.is_image:
                return self.data
            data = copy.copy(self.data['data'][key])
            if key == 'h': return data*globals.compact_support
            else: return data

    def get_display_units(self,key):
        if globals.debug > 1: print("gui.get_display_units")
        return self.data['display_units'][key]
    
    def get_physical_units(self,key):
        if globals.debug > 1: print("gui.get_physical_units")
        return self.data['physical_units'][key]

    def get_display_data(self,key,scaled=True):
        if globals.debug > 1: print("gui.get_display_data")
        d = self.get_data(key)*self.get_display_units(key)
        if scaled:
            # Check to see if the key matches
            xaxis = self.controls.axis_controllers['XAxis'].value.get()
            yaxis = self.controls.axis_controllers['YAxis'].value.get()
            controller = None
            if key == xaxis:
                controller = self.controls.axis_controllers['XAxis']
            elif key == yaxis:
                controller = self.controls.axis_controllers['YAxis']
            if controller:
                scale = controller.scale.get()
                if scale == 'log10': d = np.log10(d)
                elif scale == '^10': d = 10**d
        return d
    
    def get_physical_data(self,key):
        if globals.debug > 1: print("gui.get_physical_data")
        return self.get_data(key)*self.get_physical_units(key)
    
    def next_file(self,*args,**kwargs):
        if globals.debug > 1: print("gui.next_file")
        skip_amount = int(self.filecontrols.skip_amount.get())
        #filenames = sys.argv[1:]

        idx = self.filenames.index(self.filecontrols.current_file.get())
        nextidx = min(idx+skip_amount,len(self.filenames)-1)
        if nextidx == len(self.filenames)-1: self.filecontrols.skip_amount.set(1)
        
        if self.filenames[nextidx] != self.filecontrols.current_file.get():
            self.filecontrols.current_file.set(self.filenames[nextidx])

    def previous_file(self,*args,**kwargs):
        if globals.debug > 1: print("gui.previous_file")
        skip_amount = int(self.filecontrols.skip_amount.get())
        #filenames = sys.argv[1:]
        
        idx = self.filenames.index(self.filecontrols.current_file.get())
        nextidx = max(idx-skip_amount,0)
        if nextidx == 0: self.filecontrols.skip_amount.set(1)
        
        if self.filenames[nextidx] != self.filecontrols.current_file.get():
            self.filecontrols.current_file.set(self.filenames[nextidx])
    
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

        for filename in os.listdir(tmp_path):
            if filename not in self.filenames:
                self.filenames.append(os.path.join(tmp_path,filename))
        
            
                         
    def get_all_children(self, finList=[], wid=None):
        #if globals.debug > 1: print("gui.get_all_children")
        if wid is None: _list = self.winfo_children()
        else: _list = wid.winfo_children()        
        for item in _list:
            finList.append(item)
            self.get_all_children(finList=finList,wid=item)
        return finList
