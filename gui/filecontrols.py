import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    import ttk
    from tkFont import Font as tkFont
else:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.font as tkFont
import globals
from widgets.integerentry import IntegerEntry
from widgets.button import Button
from widgets.tooltip import ToolTip
from widgets.autosizelabel import AutoSizeLabel
from functions.getallchildren import get_all_children
from functions.setwidgetsstates import set_widgets_states
from functions.hotkeystostring import hotkeys_to_string
from hotkeyslist import hotkeyslist

class FileControls(tk.Frame,object):
    def __init__(self,master,gui,canvas,bg='white',*args,**kwargs):
        if globals.debug > 1: print("filecontrols.__init__")
        self.gui = gui
        self.canvas = canvas
        self.bg = bg
        super(FileControls,self).__init__(master,self.gui,*args,bg=self.bg,**kwargs)
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.skip_amount.set(1)
    
    def create_variables(self):
        if globals.debug > 1: print("filecontrols.create_variables")
        self.skip_amount = tk.IntVar()
        self.current_file = tk.StringVar()
        globals.state_variables.append(self.current_file)
        
    def create_widgets(self):
        if globals.debug > 1: print("filecontrols.create_widgets")
        self.current_file_label = AutoSizeLabel(self,textvariable=self.current_file,truncate='left',anchor='center')
        self.back_button = Button(self,text="<<",width=3,command=self.gui.previous_file)
        self.skip_amount_entry = IntegerEntry(self, variable=self.skip_amount,width=4)
        self.next_button = Button(self,text=">>",width=3,command=self.gui.next_file)
        
        ToolTip.createToolTip(self.back_button, "Go back N files. Press "+hotkeys_to_string('previous file')+" to also update the plot.")
        ToolTip.createToolTip(self.next_button, "Go forward N files. Press "+hotkeys_to_string('next file')+" to also update the plot.")
        
    def place_widgets(self):
        if globals.debug > 1: print("filecontrols.place_widgets")
        self.current_file_label.grid(row=0,column=0,sticky='news')
        self.back_button.grid(row=0,column=1,sticky='ns')
        self.skip_amount_entry.grid(row=0,column=2,sticky='news')
        self.next_button.grid(row=0,column=3,sticky='ns')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0,weight=1)
    
    def disable(self,group):
        if globals.debug > 1: print("filecontrols.disable")
        if group == 'all': children = get_all_children(self)
        elif group == 'toolbar': children = get_all_children(self,wid=self.toolbar)
        elif group == 'skip_buttons': children = [self.back_button,self.skip_amount_entry,self.next_button]
        set_widgets_states(children, 'disabled')

    def enable(self,group):
        if globals.debug > 1: print("filecontrols.enable")
        if group == 'all': children = get_all_children(self)
        elif group == 'toolbar': children = get_all_children(self,wid=self.toolbar)
        elif group == 'skip_buttons': children = [self.back_button,self.skip_amount_entry,self.next_button]
        set_widgets_states(children, 'normal')

    def set_state(self,widgets,state):
        if globals.debug > 1: print("filecontrols.set_state")
        for widget in widgets:
            if 'state' in widget.configure():
                widget.configure(state=state)
