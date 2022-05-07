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
from functions.getallchildren import get_all_children
from functions.setwidgetsstates import set_widgets_states
from widgets.tooltip import ToolTip
from hotkeyslist import hotkeyslist, hotkeys_to_string

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

        self.winfo_toplevel().bind("<<ResizeStopped>>",self.set_current_file_displayed)
        self.current_file.trace('w',self.set_current_file_displayed)
        self.skip_amount.set(1)
    
    def create_variables(self):
        if globals.debug > 1: print("filecontrols.create_variables")
        self.skip_amount = tk.IntVar()
        self.current_file = tk.StringVar()
        self.current_file_displayed = tk.StringVar()
        
    def create_widgets(self):
        if globals.debug > 1: print("filecontrols.create_widgets")
        self.current_file_label = tk.Label(self,textvariable=self.current_file_displayed,padx=10,bg=self.bg)
        self.back_button = Button(self,text="<<",width=3,command=self.gui.previous_file)
        self.skip_amount_entry = IntegerEntry(self, variable=self.skip_amount)
        self.next_button = Button(self,text=">>",width=3,command=self.gui.next_file)
        
        ToolTip.createToolTip(self.back_button, "Go back N files. Press "+hotkeys_to_string('previous file')+" to also update the plot.")
        ToolTip.createToolTip(self.next_button, "Go forward N files. Press "+hotkeys_to_string('next file')+" to also update the plot.")

        
        
    def place_widgets(self):
        if globals.debug > 1: print("filecontrols.place_widgets")
        self.current_file_label.grid(row=0,column=1,sticky='ew')
        self.back_button.grid(row=0,column=2)
        self.skip_amount_entry.grid(row=0,column=3,sticky='news')
        self.next_button.grid(row=0,column=4)

        self.columnconfigure(1,weight=4)
        self.columnconfigure(3,weight=1)

    def set_current_file_displayed(self,*args,**kwargs):
        if globals.debug > 1: print("filecontrols.set_current_file_displayed")
        padx = self.current_file_label.cget('padx')
        text = self.current_file.get()
        allowed_width = self.current_file_label.winfo_width() - 2*padx

        fontname = self.current_file_label.cget('font')
        if sys.version_info.major < 3:
            font = tkFont(name=fontname,exists=True)
        else:
            font = tkFont.nametofont(fontname)
        
        text_width = font.measure(text)
        
        if text_width > allowed_width:
            annotation_width = font.measure('...')
            desired_width = allowed_width - annotation_width
            while font.measure(text) > desired_width and len(text) > 0:
                text = text[1:]
            text = '...'+text
        
        self.current_file_displayed.set(text)
            
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
