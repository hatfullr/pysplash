from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
    
from widgets.verticalscrolledframe import VerticalScrolledFrame
from widgets.floatentry import FloatEntry
from widgets.integerentry import IntegerEntry
from widgets.entry import Entry

import lib.tkvariable as tkvariable
from lib.tkvariable import DoubleVar, IntVar, StringVar, BooleanVar

import collections

import matplotlib
import numpy as np
from copy import deepcopy

# A frame which contains options for editing the properties of a given artist

class ArtistEditor(VerticalScrolledFrame, object):
    hidden = {
        "all" : [
            "animated",
            "transformed_clip_path_and_affine",
            "path_effects",
            "children",
            "unitless_position",
        ],
        
        "kernel" : [
            "height",
            "width",
            "angle",
            "radius",
            "center",
            "visible",
        ],

        matplotlib.image.AxesImage : [
            "size",
            "clim",
            "extent",
        ],

        matplotlib.spines.Spine : [
            "verts",
        ],

        matplotlib.axis.Axis : [
            "label_text",
            "scale",
            "view_interval",
            "data_interval",
        ],
    }
    
    def __init__(self, master, artist, name, *args, **kwargs):
        self.artist = artist
        self.name = name
        super(ArtistEditor,self).__init__(master,*args,**kwargs)

        # Get valid properties
        self.properties = {}
        self.initial_properties = {}
        for name, value in self.artist.properties().items():
            if self.is_name_hidden(name): continue
            
            # Length 4 arrays are colors
            if (not isinstance(value, (float,int,str,tuple,list,np.ndarray)) or
                (isinstance(value, (tuple,list,np.ndarray)) and len(value) > 4)):
                continue
            
            try: self.artist.set(**{name:value})
            except AttributeError as e:
                if "object has no property '" not in str(e): raise
                else: continue
            else:
                self.properties[name] = value
                self.initial_properties[name] = value
        
        self.labels = collections.OrderedDict()
        self.widgets = collections.OrderedDict()
        self.variables = collections.OrderedDict()
        
        for name, value in self.properties.items():
            variable, widget = self.make(name,value)

            if None not in [variable,widget]:
                self.labels[name] = ttk.Label(self.interior,text=name)
                self.variables[name] = variable
                self.widgets[name] = widget
        
        self.interior.grid_columnconfigure(1,weight=1)
        
        for row,name in enumerate(self.labels.keys()):
            self.labels[name].grid(row=row,column=0,sticky='news')
            self.widgets[name].grid(row=row,column=1,sticky='news')
        
        for name,variable in self.variables.items():
            if isinstance(variable, (list,tuple,np.ndarray)):
                for v in variable:
                    v.trace('w', lambda *args,name=name: self.on_variable_changed(name))
            else: variable.trace('w', lambda *args,name=name: self.on_variable_changed(name))

        self.bind("<Map>", self.initialize, add="+")
        def reset_initialized(*args,**kwargs): self.initialized = False
        self.bind("<Unmap>", reset_initialized)
        self.initialized = False

    def get_artist_properties(self, *args, **kwargs):
        properties = self.artist.properties()
        return {key:properties[key] for key in self.properties.keys()}

    def is_name_hidden(self, name):
        if name in ArtistEditor.hidden['all']: return True
        for key,val in ArtistEditor.hidden.items():
            if not isinstance(key,str):
                if isinstance(self.artist, key) and name in val: return True
            elif self.name == key and name in val: return True
        return False

    def initialize(self, *args, **kwargs):
        # Update the variables to the artist's values
        for name, variable in self.variables.items():
            if isinstance(self.variables[name], (tuple,list,np.ndarray)):
                for var, prop in zip(self.variables[name], self.properties[name]):
                    var.set(prop)
            else:
                self.variables[name].set(self.properties[name])
        self.initialized = True
    
    def update_artist(self, *args, **kwargs):
        for name, variable in self.variables.items():
            if self.is_name_hidden(name): continue
            if isinstance(self.variables[name], (list,tuple,np.ndarray)):
                self.properties[name] = [v.get() for v in self.variables[name]]
            else: self.properties[name] = self.variables[name].get()
        if self.properties != self.initial_properties:
            self.artist.set(**self.properties)
            fig = self.artist.get_figure()
            if fig is not None:
                fig.canvas.draw_idle()
                fig.canvas.flush_events()
                self.initial_properties = {key:value for key,value in self.properties.items()}

    def on_variable_changed(self, name):
        if not self.initialized: return
        if isinstance(self.widgets[name], Entry):
            try: self.update_artist()
            except ValueError: pass
        else:
            self.update_artist()

    def make(self, name, value, master=None):
        if master is None: master = self.interior
        
        variable = None
        widget = None
        
        if isinstance(value, float):
            pref = tkvariable.get(name,widget=self)
            if pref is None: pref = value
            variable = DoubleVar(self,pref,name)
            
            widget  = FloatEntry(
                master,
                variable=variable,
            )
        elif isinstance(value, int):
            pref = tkvariable.get(name,widget=self)
            if pref is None: pref = value
            variable = IntVar(self,pref,name)
            
            widget = IntegerEntry(
                master,
                variable=variable,
            )
        elif isinstance(value, str):
            pref = tkvariable.get(name,widget=self)
            if pref is None: pref = value
            variable = StringVar(self,pref,name)

            widget = Entry(
                master,
                textvariable=variable,
            )

        # This means it's a color or possibly something else
        elif isinstance(value, (tuple,list,np.ndarray)):
            variable = []
            widget = tk.Frame(self.interior)
            for i,v in enumerate(value):
                var, wid = self.make(name+str(i),v,master=widget)
                if var is not None:
                    variable.append(var)
                    wid.pack(side='left',fill='both',expand=True)

        return variable, widget
