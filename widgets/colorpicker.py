from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import colorchooser
    import tkinter.font as tkFont
else:
    import Tkinter as tk
    import ttk
    import tkColorChooser as colorchooser
    from tkFont import Font as tkFont
from lib.tkvariable import StringVar
import numpy as np
import matplotlib.colors
    
class ColorPicker(tk.Button,object):
    def __init__(self,gui,master,command=None,default=None,*args,**kwargs):
        self.root = master.winfo_toplevel()
        self.command = command
        
        kwargs['command'] = self._post
        self.photo = tk.PhotoImage()
        kwargs['image'] = self.photo
        super(ColorPicker,self).__init__(master,*args,**kwargs)

        if default is None: default = 'k'
        self.color = StringVar(self, self.rgb2tk(default), "color")
            
        fontsize_px = gui.fontsize_px
        self.configure(height=fontsize_px,width=fontsize_px,background=self.color.get())
        
    def _post(self,*args,**kwargs):
        color = colorchooser.askcolor(parent=self.root,initialcolor=self.cget('background'))[1]
        if color:
            self.color.set(color)
            self.configure(background=color)
            if self.command is not None: self.command()

    def rgb2tk(self,rgb):
        # translates a list of values to a tkinter friendly color code
        if isinstance(rgb,str): rgb = matplotlib.colors.to_rgb(rgb)
        if len(rgb) == 1: rgb = rgb[0]
        if isinstance(rgb,(np.ndarray,tuple)): rgb = list(rgb)
        if len(rgb) > 3: rgb = rgb[:3] # Discard A from RGBA quantity
        if len(rgb) != 3: raise Exception("Could not factor rgb into an array with size 3")
        for i,c in enumerate(rgb):
            if isinstance(c,float): rgb[i] = int(255*c)
        return "#%02x%02x%02x" % tuple(rgb)
