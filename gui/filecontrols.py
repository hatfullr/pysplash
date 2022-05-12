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

        #self.winfo_toplevel().bind("<Configure>",self.set_current_file_displayed,add="+")
        #self.current_file.trace('w',self.set_current_file_displayed)
        self.skip_amount.set(1)
    
    def create_variables(self):
        if globals.debug > 1: print("filecontrols.create_variables")
        self.skip_amount = tk.IntVar()
        self.current_file = tk.StringVar()
        self.current_file_displayed = tk.StringVar()
        
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

    def set_current_file_displayed(self,*args,**kwargs):
        if globals.debug > 1: print("filecontrols.set_current_file_displayed")
        self.update_idletasks()
        #padx = self.current_file_label.cget('padx')
        text = self.current_file.get()
        allowed_width = self.current_file_label.winfo_width() #- 2*padx

        fontname = str(self.current_file_label.cget('font'))
        if sys.version_info.major < 3:
            font = tkFont(name=fontname,exists=True)
        else:
            font = tkFont.nametofont(fontname)

        reqwidth = font.measure(text)
        #if reqwidth > allowed_width:
        #    #print("In here")
        #    approx_char_width = len(text)/reqwidth
        #    Nchars_allowed = int(allowed_width / approx_char_width)
        #    text = "..."+text[-(Nchars_allowed-3):]
        
        #width = int(allowed_width / font.measure("A"))
        #if len(text) > width: text = "..."+text[-width+3:]
        #text_width = font.measure(text)
        
        #if text_width > allowed_width:
            
        #annotation_width = font.measure('...')
        #desired_width = allowed_width - annotation_width
        #while font.measure(text) > desired_width and len(text) > 0:
        #    text = text[1:]
        #text = '...'+text

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
