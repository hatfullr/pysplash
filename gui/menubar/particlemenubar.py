from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

import numpy as np
import matplotlib

import lib.tkvariable as tkvariable
from lib.tkvariable import BooleanVar
from functions.findparticle import FindParticle
from functions.annotateparticle import AnnotateParticle
from gui.menubar.menu import Menu
from gui.menubar.particlesettings import ParticleSettings
from lib.scatterplot import ScatterPlot
import kernel

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

        self.add_command(
            "Annotate",
            command=lambda *args,**kwargs: AnnotateParticle(self.gui),
            state='disabled',
            hotkey="annotate particle",
            bind=False,
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

        self.annotate_neighbors = BooleanVar(self, None, "annotate_neighbors")
        self.add_checkbutton(
            "Annotate neighbors",
            variable=self.annotate_neighbors,
            command=self.update_neighbor_annotations,
            state='disabled',
        )
        
        self.add_command(
            "Settings",
            command=self.settings.deiconify,
        )

        self.neighbor_annotations = []
        
        self.gui.interactiveplot.track_id.trace('w', self.on_track_id_set)
        self.gui.interactiveplot.ax.add_artist(self.kernel)
        
        if not self.gui.interactiveplot.tracking:
            self.show_kernel.set(False)
            self.show_neighbors.set(False)
        
        self.after_id = None

        self.gui.bind("<<PlotUpdate>>",self.update_kernel,add="+")
        self.gui.bind("<<BeforePlotUpdate>>", self.update_neighbors, add="+")
        self.gui.bind("<<BeforePlotUpdate>>", self.update_kernel, add="+")
        self.gui.bind("<<PlotUpdate>>", self.update_neighbor_annotations, add="+")
        self._clearing_neighbors = False

    def on_track_id_set(self, *args, **kwargs):
        state = 'normal' if self.gui.interactiveplot.tracking else 'disabled'
        self.set_state(state, label="Show kernel")
        self.set_state(state, label="Show neighbors")
        self.set_state(state, label="Annotate neighbors")
        self.update_kernel()
        self.update_neighbors()
        self.update_neighbor_annotations()

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
                radius = kernel.compact_support*self.gui.get_display_data('h')[track_id],
            )

    def on_show_neighbors(self,*args,**kwargs):
        self.gui.interactiveplot.update()
        #if self.show_neighbors.get(): self.set_state('normal', label="Annotate neighbors")
        #else: self.set_state('disabled', label="Annotate neighbors")

    def update_neighbors(self, *args, **kwargs):
        if self.gui.interactiveplot.tracking and self.show_neighbors.get() and self.gui.data is not None:

            neighbors = self.get_neighbors(self.gui.interactiveplot.track_id.get())
            
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

    def get_neighbors(self, particle):
        x = self.gui.get_physical_data('x')
        y = self.gui.get_physical_data('y')
        z = self.gui.get_physical_data('z')
        h = kernel.compact_support*self.gui.get_physical_data('h')
        xyz = np.column_stack((x,y,z))
        dr2 = np.sum((xyz - xyz[particle])**2,axis=-1)
        return dr2 <= h[particle]**2

    def update_neighbor_annotations(self,*args,**kwargs):
        if not self.gui.interactiveplot.tracking or self.gui.data is None: return

        # Do nothing if we are showing a data from an image
        if self.gui.data.is_image: return
        
        if self.neighbors is None:
            self.neighbors = self.get_neighbors(self.gui.interactiveplot.track_id.get())

        particles = []
        annotations = []
        for particle, annotation in self.gui.interactiveplot.plot_annotations.items():
            try: int(particle)
            except: continue
            particles.append(int(particle))
            annotations.append(annotation)
        track_id = self.gui.interactiveplot.track_id.get()
        for particle, annotation in zip(particles,annotations):
            if particle == track_id: continue
            if particle not in self.neighbors:
                self.gui.interactiveplot.plot_annotations.remove(str(particle))

        if self.annotate_neighbors.get():
            keys = []
            for key in self.gui.interactiveplot.plot_annotations.keys():
                try: int(key)
                except: continue
                keys.append(key)
                
            for neighbor in np.arange(len(self.neighbors))[self.neighbors]:
                if neighbor == track_id: continue
                if neighbor not in keys:
                    self.gui.interactiveplot.annotate_particle(ID=neighbor,draw=False)
        self.gui.interactiveplot.draw()

