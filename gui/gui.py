import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    from tkFont import Font as tkFont
    from interactiveplot import InteractivePlot
    from controls import Controls
else:
    import tkinter as tk
    import tkinter.font as tkFont
    from gui.interactiveplot import InteractivePlot
    from gui.controls import Controls

from lib.data import Data
from read_file import read_file
import globals
from widgets.menubar import MenuBar
from functions.make_rotation_movie import make_rotation_movie
import copy

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
        if len(sys.argv[1:]) == 0:
            raise RuntimeError("No filenames provided")
        
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
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.interactiveplot.plotcontrols.next_button.configure(command=self.next_file)
        self.interactiveplot.plotcontrols.back_button.configure(command=self.previous_file)
        
        self.interactiveplot.plotcontrols.current_file.trace("w",self.read)
        self.interactiveplot.plotcontrols.current_file.set(sys.argv[1])


        self.rotation_after_id = None
        
        self.initialize_xy_controls()

        self.controls.save_state()
        
    def initialize_xy_controls(self):
        if globals.debug > 1: print("gui.initialize_xy_controls")
        N = len(self.get_data('x'))
        found_first = False
        for key,val in self.data['data'].items():
            if hasattr(val,"__len__"):
                if len(val) == N:
                    if not found_first:
                        self.controls.x.set(key)
                        found_first = True
                    else:
                        self.controls.y.set(key)
                        break
    
    def create_variables(self):
        if globals.debug > 1: print("gui.create_variables")
        self.message_text = tk.StringVar()
        
    def create_widgets(self):
        if globals.debug > 1: print("gui.create_widgets")
        self.menubar = MenuBar(self.window,self)
        self.controls = Controls(
            self,
            width=2*self.dpi, # pixels = inches * dpi
        ) 
        self.interactiveplot = InteractivePlot(
            self,
        )
        self.message_label = tk.Label(self,textvariable=self.message_text,bg='white')
        
    def place_widgets(self):
        if globals.debug > 1: print("gui.place_widgets")
        self.interactiveplot.grid(row=0,column=0,sticky='news',padx=5,pady=5)
        self.controls.grid(row=0,column=1,sticky='ns',padx=5,pady=5)
        self.message_label.place(rely=1,relx=1,anchor="se")
        self.pack(fill='both',expand=True)

        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

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
            self.controls.enable('all')
            self.interactiveplot.plotcontrols.enable('all')
        else:
            self.controls.disable('all',temporarily=True)
            self.interactiveplot.plotcontrols.disable('all')
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
            read_file(self.interactiveplot.plotcontrols.current_file.get()),
            rotations=(self.controls.rotation_x.get(),self.controls.rotation_y.get(),self.controls.rotation_z.get()),
        )
        # Check for requisite keys for certain types of plots
        values = ['None']
        keys = self.data['data'].keys()
        for key in ['x','y','m','h','rho']:
            if key not in keys: break
        else: values.append("Column density")
        for key in ['x','y','m','h','rho','opacity']:
            if key not in keys: break
        else: values.append("Optical depth")

        self.controls.caxis_combobox.configure(values=values)
        
        self.controls.update_axis_comboboxes(self.data)
        self.do_after(100,self.interactiveplot.update,lambda: self.controls.x.get() and self.controls.y.get())

    def get_data(self,key):
        if globals.debug > 1: print("gui.get_data")
        data = copy.copy(self.data['data'][key])
        if key == 'h': return data*globals.compact_support
        else: return data

    def get_display_units(self,key):
        if globals.debug > 1: print("gui.get_display_units")
        return self.data['display_units'][key]
    def get_physical_units(self,key):
        if globals.debug > 1: print("gui.get_physical_units")
        return self.data['physical_units'][key]

    def get_display_data(self,key):
        if globals.debug > 1: print("gui.get_display_data")
        return self.get_data(key)*self.get_display_units(key)
    def get_physical_data(self,key):
        if globals.debug > 1: print("gui.get_physical_data")
        return self.get_data(key)*self.get_physical_units(key)
    
    def next_file(self,*args,**kwargs):
        if globals.debug > 1: print("gui.next_file")
        skip_amount = int(self.interactiveplot.plotcontrols.skip_amount.get())
        filenames = sys.argv[1:]

        idx = filenames.index(self.interactiveplot.plotcontrols.current_file.get())
        nextidx = min(idx+skip_amount,len(filenames)-1)
        if nextidx == len(filenames)-1: self.interactiveplot.plotcontrols.skip_amount.set(1)
        
        if filenames[nextidx] != self.interactiveplot.plotcontrols.current_file.get():
            self.interactiveplot.plotcontrols.current_file.set(filenames[nextidx])

    def previous_file(self,*args,**kwargs):
        if globals.debug > 1: print("gui.previous_file")
        skip_amount = int(self.interactiveplot.plotcontrols.skip_amount.get())
        filenames = sys.argv[1:]
        
        idx = filenames.index(self.interactiveplot.plotcontrols.current_file.get())
        nextidx = max(idx-skip_amount,0)
        if nextidx == 0: self.interactiveplot.plotcontrols.skip_amount.set(1)
        
        if filenames[nextidx] != self.interactiveplot.plotcontrols.current_file.get():
            self.interactiveplot.plotcontrols.current_file.set(filenames[nextidx])
    
    def make_rotation_movie(self,*args,**kwargs):
        if globals.debug > 1: print("gui.make_rotation_movie")
        make_rotation_movie(self)
