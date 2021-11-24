import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    from tkFont import Font as tkFont
    from customtoolbar import CustomToolbar
else:
    import tkinter as tk
    import tkinter.font as tkFont
    from gui.customtoolbar import CustomToolbar
import globals

class PlotControls(tk.Frame,object):
    def __init__(self,gui,canvas,bg='white',*args,**kwargs):
        if globals.debug > 1: print("plotcontrols.__init__")
        self.gui = gui
        self.canvas = canvas
        self.bg = bg
        super(PlotControls,self).__init__(self.gui,*args,bg=self.bg,**kwargs)
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.winfo_toplevel().bind("<<ResizeStopped>>",self.set_current_file_displayed)
        self.current_file.trace('w',self.set_current_file_displayed)
        self.skip_amount.set(1)
    
    def create_variables(self):
        if globals.debug > 1: print("plotcontrols.create_variables")
        self.skip_amount = tk.StringVar()
        self.current_file = tk.StringVar()
        self.current_file_displayed = tk.StringVar()
        
    def create_widgets(self):
        if globals.debug > 1: print("plotcontrols.create_widgets")
        self.toolbar = CustomToolbar(self,self.gui,self.canvas,bg=self.bg)
        self.current_file_label = tk.Label(self,textvariable=self.current_file_displayed,padx=10,bg=self.bg)
        self.back_button = tk.Button(self,text="<<",width=2,height=1,padx=5,pady=5)
        self.skip_amount_entry = tk.Entry(self,textvariable=self.skip_amount,width=5)
        self.next_button = tk.Button(self,text=">>",width=2,height=1,padx=5,pady=5)
        
    def place_widgets(self):
        if globals.debug > 1: print("plotcontrols.place_widgets")
        self.toolbar.grid(row=0,column=0)
        self.current_file_label.grid(row=0,column=1,sticky='ew')
        self.back_button.grid(row=0,column=2)
        self.skip_amount_entry.grid(row=0,column=3)
        self.next_button.grid(row=0,column=4)

        self.columnconfigure(1,weight=1)

    def set_current_file_displayed(self,*args,**kwargs):
        if globals.debug > 1: print("plotcontrols.set_current_file_displayed")
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

    def get_all_children(self, finList=[], wid=None):
        if globals.debug > 1: print("plotcontrols.get_all_children")
        if wid is None: _list = self.winfo_children()
        else: _list = wid.winfo_children()        
        for item in _list:
            finList.append(item)
            self.get_all_children(finList=finList,wid=item)
        return finList
            
    def disable(self,group):
        if globals.debug > 1: print("plotcontrols.disable")
        if group == 'all': children = self.get_all_children()
        elif group == 'toolbar': children = self.get_all_children(wid=self.toolbar)
        elif group == 'skip_buttons': children = [self.back_button,self.skip_amount_entry,self.next_button]
        self.set_state(children,'disabled')

    def enable(self,group):
        if globals.debug > 1: print("plotcontrols.enable")
        if group == 'all': children = self.get_all_children()
        elif group == 'toolbar': children = self.get_all_children(wid=self.toolbar)
        elif group == 'skip_buttons': children = [self.back_button,self.skip_amount_entry,self.next_button]
        self.set_state(children,'normal')

    def set_state(self,widgets,state):
        if globals.debug > 1: print("plotcontrols.set_state")
        for widget in widgets:
            if 'state' in widget.configure():
                widget.configure(state=state)
