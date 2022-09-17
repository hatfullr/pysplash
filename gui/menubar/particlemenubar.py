from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

import numpy as np
import matplotlib

import lib.tkvariable as tkvariable
from lib.tkvariable import BooleanVar
from functions.findparticle import FindParticle
from gui.menubar.menu import Menu
from gui.menubar.particlesettings import ParticleSettings
from lib.scatterplot import ScatterPlot

class ParticleMenuBar(Menu, object):
    def __init__(self, master, gui, tearoff=0, *args, **kwargs):
        self.gui = gui
        super(ParticleMenuBar, self).__init__(
            master,
            self.gui.window,
            *args,
            tearoff=tearoff,
            **kwargs
        )

        self.kernel = matplotlib.patches.Circle(
            (0,0),0,
            visible=False,
            fill=False,
            facecolor='none',
            edgecolor='k',
            lw=1,
        )
        self.neighbors = None

        self.settings = ParticleSettings(
            self.gui,
            {
                'kernel' : self.kernel,
            },
        )

        self.add_command(
            "Find",
            command=lambda *args,**kwargs: FindParticle(self.gui),
            state='disabled',
            hotkey="find particle",
        )

        self.show_kernel = BooleanVar(self, None, "show_kernel")
        
        self.add_checkbutton(
            "Show kernel",
            variable=self.show_kernel,
            command=self.on_show_kernel,
            state='disabled',
        )

        self.show_neighbors = BooleanVar(self, None, "show_neighbors")
        self.add_checkbutton(
            "Show neighbors",
            variable=self.show_neighbors,
            command=self.on_show_neighbors,
            state='disabled',
        )
        
        self.add_command(
            "Settings",
            command=self.settings.deiconify,
        )
        
        self.gui.interactiveplot.track_id.trace('w', self.on_track_id_set)
        self.gui.interactiveplot.ax.add_artist(self.kernel)
        
        if not self.gui.interactiveplot.tracking:
            self.show_kernel.set(False)
            self.show_neighbors.set(False)
        
        self.after_id = None

        self.gui.bind("<<BeforePlotUpdate>>", self.update_neighbors, add="+")
        self.gui.bind("<<BeforePlotUpdate>>", self.update_kernel, add="+")
        self._clearing_neighbors = False

    def on_track_id_set(self, *args, **kwargs):
        state = 'normal' if self.gui.interactiveplot.tracking else 'disabled'
        self.set_state(state, label="Show kernel")
        self.set_state(state, label="Show neighbors")
        self.update_kernel()
        self.update_neighbors()

    def on_show_kernel(self,*args,**kwargs):
        self.update_kernel()
        self.gui.interactiveplot.draw()

    def update_kernel(self, *args, **kwargs):
        self.kernel.set_visible(
            (self.gui.interactiveplot.tracking and
             self.show_kernel.get() and
             self.gui.data is not None and
             (self.gui.controls.axis_controllers['XAxis'].value.get() in ['x','y','z'] and
              self.gui.controls.axis_controllers['YAxis'].value.get() in ['x','y','z'])
             )
        )
        if self.kernel.get_visible():
            track_id = self.gui.interactiveplot.track_id.get()
            self.kernel.set(
                center = self.gui.interactiveplot.origin,
                radius = self.gui.get_display_data('size')[track_id],
            )

    def on_show_neighbors(self,*args,**kwargs):
        self.gui.interactiveplot.update()

    def update_neighbors(self, *args, **kwargs):
        if self.gui.interactiveplot.tracking and self.show_neighbors.get() and self.gui.data is not None:
            x = self.gui.get_physical_data('x')
            y = self.gui.get_physical_data('y')
            z = self.gui.get_physical_data('z')
            size = self.gui.get_physical_data('size')
            
            xyz = np.column_stack((x,y,z))
            
            track_id = self.gui.interactiveplot.track_id.get()
            dr2 = np.sum((xyz - xyz[track_id])**2,axis=-1)
            
            neighbors = dr2 <= size[track_id]**2
            if self.neighbors is None: self.neighbors = neighbors
            elif not np.array_equal(neighbors,self.neighbors):
                toblack = np.logical_and(self.neighbors, ~neighbors)
                self.gui.interactiveplot.color_particles(None, particles=toblack, index=ScatterPlot.default_color_index, update=False)
                self.neighbors = neighbors
            self.gui.interactiveplot.color_particles(None, particles=self.neighbors, index=ScatterPlot.neighbor_color_index,update=False)
        else:
            if self.neighbors is not None:
                if not self._clearing_neighbors:
                    self._clearing_neighbors = True
                    self.gui.interactiveplot.color_particles(None, particles=self.neighbors, index=ScatterPlot.default_color_index,update=True)
                    self.neighbors = None
                    self._clearing_neighbors = False

            
