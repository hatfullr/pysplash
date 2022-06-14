from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
import textwrap

class WarningMessage(tk.Toplevel,object):
    def __init__(self,root,message,details='None'):
        self.details = details
        style = ttk.Style()
        self.root = root
        self.pad = root.pad
        self.total_pad = 2*self.pad
        
        super(WarningMessage,self).__init__(
            background=style.lookup('TFrame','background',state=['!disabled']),
            pady=self.pad,
            padx=self.pad,
        )
        
        self.withdraw()
        
        # Cross-platform (probably) window sizing
        self.width = int(self.root.winfo_screenwidth() / 4)

        self.configure(width=self.width)
        
        # Set other window options
        self.title("Warning")
        self.resizable(False,False)
        self.tk.call('wm','iconphoto',self._w,'::tk::icons::warning')
        
        # Create the widgets
        self.message_frame = tk.Frame(
            self,
            background=self.cget('background'),
        )
        self.text_frame = ttk.Frame(self)
        self.button_frame = ttk.Frame(self)
        self.textbox = tk.Text(self.text_frame,wrap='word')

        self.message = ttk.Label(
            self.message_frame,
            text=message,
            justify='left',
            background=self.cget('background'),
            wraplength=self.width,
        )
        
        self.ok_button = ttk.Button(
            self.button_frame,
            text="Ok",
            command=self.on_ok,
        )
        if self.details.strip() != "None":
            self.details_button = ttk.Button(
                self.button_frame,
                text="Details",
                command=self.toggle_details,
            )
        
            self.vscrollb = ttk.Scrollbar(self.text_frame,command=self.textbox.yview)
        
            self.textbox.config(yscrollcommand=self.vscrollb.set)
            self.textbox.insert('1.0', self.details)

        self.minsize(width=self.width,height=0)
        self.maxsize(width=self.width,height=0)
        
        # Pack the widgets
        self.message.pack(anchor='w')
        self.message_frame.pack(side='top',fill='x',pady=(0,self.pad))
        self.ok_button.pack(side='left',padx=self.pad)
        if self.details.strip() != "None": self.details_button.pack(side='right',padx=self.pad)
        self.button_frame.pack()
        if self.details.strip() != "None": self.text_frame.pack(side='bottom',pady=(self.pad,0))
        
        self.details_expanded = False
        self.set_expanded_height = True

        self.tk.eval('tk::PlaceWindow '+str(self)+' center')

        if self.details.strip() != "None": self.textbox.configure(state='disabled')
        
        self.grab_set()
        self.transient(self.root)
        self.wait_window()
        
    def toggle_details(self):
        if self.details_expanded:
            self.vscrollb.pack_forget()
            self.textbox.pack_forget()
            self.text_frame.pack_forget()
            self.details_expanded = False
        else:
            self.vscrollb.pack(side='right',fill='y')
            self.textbox.pack()
            self.text_frame.pack(side='bottom',pady=(self.pad,0))
            if self.set_expanded_height:
                self.maxsize(width=self.width,height=3*self.winfo_height())
                self.set_expanded_height = False
            self.details_expanded = True
