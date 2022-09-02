from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

import matplotlib as mpl
from widgets.button import Button
from widgets.popupwindow import PopupWindow
from widgets.floatentry import FloatEntry
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import globals

class ConfigureSubplots(PopupWindow, object):
    def __init__(self, gui):
        if globals.debug > 1: print("configuresubplots.__init__")
        self.gui = gui
        super(ConfigureSubplots,self).__init__(
            self.gui,
            title="Configure subplots",
            oktext="Done",
            okcommand=self.close,
            cancelcommand=self.cancel,
            name='configuresubplots',
        )

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.variables = [
            self.gui.interactiveplot.top,
            self.gui.interactiveplot.bottom,
            self.gui.interactiveplot.left,
            self.gui.interactiveplot.right,
            self.gui.interactiveplot.hspace,
            self.gui.interactiveplot.wspace,
        ]

        for variable in self.variables:
            variable.trace('w', self.subplots_adjust)

        self.original_values = [var.get() for var in self.variables]
        self.after_id = None


    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("configuresubplots.create_variables")

        
    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("configuresubplots.create_widgets")

        self.default_button = Button(
            self.buttons_frame,
            text="Default",
            command=self.reset_to_default,
        )
        
        self.reset_button = Button(
            self.buttons_frame,
            text="Reset",
            command=self.reset,
        )

        def create_slider(label, variable, clamp=(None,None), from_=0, to=1):
            label = ttk.Label(self.contents,text=label,anchor='e')
            slider = ttk.Scale(self.contents,from_=from_,to=to,orient='horizontal',variable=variable)
            value = FloatEntry(self.contents,allowblank=False,variable=variable,width=5,clamp=clamp)
            return label, slider, value
        
        self.top_label, self.top_slider, self.top_value = create_slider(
            'top',
            self.gui.interactiveplot.top,
            clamp=(self.gui.interactiveplot.bottom,1.),
        )
        self.bottom_label, self.bottom_slider, self.bottom_value = create_slider(
            'bottom',
            self.gui.interactiveplot.bottom,
            clamp=(0.,self.gui.interactiveplot.top),
        )
        self.left_label, self.left_slider, self.left_value = create_slider(
            'left',
            self.gui.interactiveplot.left,
            clamp=(0.,self.gui.interactiveplot.right),
        )
        self.right_label, self.right_slider, self.right_value = create_slider(
            'right',
            self.gui.interactiveplot.right,
            clamp=(self.gui.interactiveplot.left,1.),
        )
        self.hspace_label, self.hspace_slider, self.hspace_value = create_slider(
            'hspace',
            self.gui.interactiveplot.hspace,
            clamp=(-1.,1.),
            from_=-1,to=1,
        )
        self.wspace_label, self.wspace_slider, self.wspace_value = create_slider(
            'wspace',
            self.gui.interactiveplot.wspace,
            clamp=(-1.,1.),
            from_=-1,to=1,
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("configuresubplots.place_widgets")
        
        self.default_button.pack(side='left')
        self.reset_button.pack(side='left',padx=5)

        slider_sticky = 'news'
        label_sticky = 'news'
        value_sticky='news'
        label_padx = 5
        slider_padx = 0
        value_padx = 0

        label_pady = 0
        slider_pady = 0
        value_pady = 0

        self.contents.columnconfigure(0,weight=0)
        self.contents.columnconfigure(1,weight=1)
        
        self.top_label.grid(row=0,column=0,sticky=label_sticky,padx=label_padx,pady=label_pady)
        self.top_slider.grid(row=0,column=1,sticky=slider_sticky,padx=slider_padx,pady=slider_pady)
        self.top_value.grid(row=0,column=2,sticky=value_sticky,padx=value_padx,pady=value_pady)
        
        self.bottom_label.grid(row=1,column=0,sticky=label_sticky,padx=label_padx,pady=label_pady)
        self.bottom_slider.grid(row=1,column=1,sticky=slider_sticky,padx=slider_padx,pady=slider_pady)
        self.bottom_value.grid(row=1,column=2,sticky=value_sticky,padx=value_padx,pady=value_pady)
        
        self.left_label.grid(row=2,column=0,sticky=label_sticky,padx=label_padx,pady=label_pady)
        self.left_slider.grid(row=2,column=1,sticky=slider_sticky,padx=slider_padx,pady=slider_pady)
        self.left_value.grid(row=2,column=2,sticky=value_sticky,padx=value_padx,pady=value_pady)
        
        self.right_label.grid(row=3,column=0,sticky=label_sticky,padx=label_padx,pady=label_pady)
        self.right_slider.grid(row=3,column=1,sticky=slider_sticky,padx=slider_padx,pady=slider_pady)
        self.right_value.grid(row=3,column=2,sticky=value_sticky,padx=value_padx,pady=value_pady)
        
        self.hspace_label.grid(row=4,column=0,sticky=label_sticky,padx=label_padx,pady=label_pady)
        self.hspace_slider.grid(row=4,column=1,sticky=slider_sticky,padx=slider_padx,pady=slider_pady)
        self.hspace_value.grid(row=4,column=2,sticky=value_sticky,padx=value_padx,pady=value_pady)
        
        self.wspace_label.grid(row=5,column=0,sticky=label_sticky,padx=label_padx,pady=label_pady)
        self.wspace_slider.grid(row=5,column=1,sticky=slider_sticky,padx=slider_padx,pady=slider_pady)
        self.wspace_value.grid(row=5,column=2,sticky=value_sticky,padx=value_padx,pady=value_pady)

    def reset(self,*args,**kwargs):
        if globals.debug > 1: print("configuresubplots.reset")
        for var,val in zip(self.variables,self.original_values): var.set(val)

    def reset_to_default(self,*args,**kwargs):
        if globals.debug > 1: print("configuresubplots.reset_to_default")
        values = [
            mpl.rcParams['figure.subplot.top'],
            mpl.rcParams['figure.subplot.bottom'],
            mpl.rcParams['figure.subplot.left'],
            mpl.rcParams['figure.subplot.right'],
            mpl.rcParams['figure.subplot.hspace'],
            mpl.rcParams['figure.subplot.wspace'],
        ]
        for var,val in zip(self.variables,values): var.set(val)

    def cancel(self,*args,**kwargs):
        if globals.debug > 1: print("configuresubplots.cancel")
        self.reset()
        super(ConfigureSubplots,self).close()
        self.gui.interactiveplot.canvas.draw()

    def close(self,*args,**kwargs):
        self.gui.interactiveplot.update()
        super(ConfigureSubplots,self).close(*args,**kwargs)

    def subplots_adjust(self,*args,**kwargs):
        if globals.debug > 1: print("configuresubplots.subplots_adjust")

        kwargs = {var.name:var.get() for var in self.variables}

        if kwargs['left'] < kwargs['right'] and kwargs['bottom'] < kwargs['top']:
            self.gui.interactiveplot.subplots_adjust(**kwargs)
            if self.after_id is not None:
                self.after_cancel(self.after_id)
            self.after_id = self.after(100, lambda *args,**kwargs: self.gui.interactiveplot.canvas.draw())
