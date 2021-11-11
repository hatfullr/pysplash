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
from globals import compact_support
from widgets.menubar import MenuBar
from functions.make_rotation_movie import make_rotation_movie

class GUI(tk.Frame,object):
    def __init__(self,window,fontname='TkDefaultFont',fontsize=12):
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

        self.controls.rotation_x.trace('w',self.on_rotation_entered)
        self.controls.rotation_y.trace('w',self.on_rotation_entered)
        self.controls.rotation_z.trace('w',self.on_rotation_entered)

        self.controls.caxis_adaptive_limits.trace('w',self.interactiveplot.toggle_clim_adaptive)

        self.rotation_after_id = None
        
        self.initialize_xy_controls()
        
    def initialize_xy_controls(self):
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
        self.message_text = tk.StringVar()
        
    def create_widgets(self):
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
        self.interactiveplot.grid(row=0,column=0,sticky='news',padx=5,pady=5)
        self.controls.grid(row=0,column=1,sticky='ns',padx=5,pady=5)
        self.message_label.place(rely=1,relx=1,anchor="se")
        self.pack(fill='both',expand=True)

        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

    def message(self,text,*args,**kwargs):
        # Display a message on the bottom-right hand corner of the window
        self.message_text.set(text)
    def clear_message(self,*args,**kwargs):
        self.message_text.set("")

    def set_user_controlled(self,value):
        if value:
            self.controls.enable('all')
            self.interactiveplot.plotcontrols.enable('all')
        else:
            self.controls.disable('all')
            self.interactiveplot.plotcontrols.disable('all')
        self.user_controlled = value
    def get_user_controlled(self): return self.user_controlled

    def do_after(self,amount,todo,trigger,args=[],kwargs={}):
        if not trigger():
            self.after(amount,lambda amt=amount,td=todo,trig=trigger,arrgs=args,kwarrgs=kwargs: self.do_after(amt,td,trig,arrgs,kwarrgs))
        else:
            todo(*args,**kwargs)

    def read(self,*args,**kwargs):
        self.data = Data(
            read_file(self.interactiveplot.plotcontrols.current_file.get()),
            rotations=(self.controls.rotation_x.get(),self.controls.rotation_y.get(),self.controls.rotation_z.get()),
        )
        self.controls.update_axis_comboboxes(self.data)
        self.do_after(100,self.interactiveplot.update,lambda: self.controls.x.get() and self.controls.y.get())

    def get_data(self,key):
        data = self.data['data'][key]
        if key == 'h': return data*compact_support
        else: return data

    def get_display_units(self,key):
        return self.data['display_units'][key]
    def get_physical_units(self,key):
        return self.data['physical_units'][key]

    def get_display_data(self,key):
        return self.get_data(key)*self.get_display_units(key)
    def get_physical_data(self,key):
        return self.get_data(key)*self.get_physical_units(key)
    
    def next_file(self,*args,**kwargs):
        skip_amount = int(self.interactiveplot.plotcontrols.skip_amount.get())
        filenames = sys.argv[1:]

        idx = filenames.index(self.interactiveplot.plotcontrols.current_file.get())
        nextidx = min(idx+skip_amount,len(filenames)-1)
        if nextidx == len(filenames)-1: self.interactiveplot.plotcontrols.skip_amount.set(1)
        
        if filenames[nextidx] != self.interactiveplot.plotcontrols.current_file.get():
            self.interactiveplot.plotcontrols.current_file.set(filenames[nextidx])

    def previous_file(self,*args,**kwargs):
        skip_amount = int(self.interactiveplot.plotcontrols.skip_amount.get())
        filenames = sys.argv[1:]
        
        idx = filenames.index(self.interactiveplot.plotcontrols.current_file.get())
        nextidx = max(idx-skip_amount,0)
        if nextidx == 0: self.interactiveplot.plotcontrols.skip_amount.set(1)
        
        if filenames[nextidx] != self.interactiveplot.plotcontrols.current_file.get():
            self.interactiveplot.plotcontrols.current_file.set(filenames[nextidx])
            
    def on_rotation_entered(self,*args,**kwargs):
        if self.get_user_controlled():
            if self.rotation_after_id is not None:
                self.after_cancel(self.rotation_after_id)
            self.rotation_after_id = self.after(
                500,
                self.do_rotation,
            )

    def do_rotation(self,redraw=True):
        self.data.rotate(
            self.controls.rotation_x.get(),
            self.controls.rotation_y.get(),
            self.controls.rotation_z.get(),
        )
        if redraw: self.interactiveplot.update()

    def reset_rotation(self,redraw=True):
        is_user_controlled = self.get_user_controlled()
        if is_user_controlled: self.set_user_controlled(False)
        self.data.reset()
        self.controls.rotation_x.set(0)
        self.controls.rotation_y.set(0)
        self.controls.rotation_z.set(0)
        self.do_rotation(redraw=redraw)
        if is_user_controlled: self.set_user_controlled(True)

    def make_rotation_movie(self,*args,**kwargs):
        make_rotation_movie(self)
