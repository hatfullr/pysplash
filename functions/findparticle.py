from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
import os
import globals
import numpy as np
from widgets.popupwindow import PopupWindow
from widgets.integerentry import IntegerEntry
from functions.hotkeystostring import hotkeys_to_string
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import lib.tkvariable as tkvariable
import traceback
import matplotlib.patches

class FindParticle(PopupWindow,object):
    recenter_plot = True
    def __init__(self, gui):
        if globals.debug > 1: print("findparticle.__init__")
        self.gui = gui
        
        # Setup the window
        super(FindParticle,self).__init__(
            self.gui,
            title="Find particle",
            oktext="Find (Enter)",
            okcommand=self.on_ok_button,
            show=True,
            name='findparticle',
        )

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.entry.bind("<Return>", lambda *args, **kwargs: self.okbutton.invoke(), add="+")
        self.entry.focus()
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("findparticle.create_variables")
        self.particle = IntVar(self,0,'particle')
        self.recenter_plot = BooleanVar(self, True, "recenter_plot")

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("findparticle.create_widgets")
        self.description = ttk.Label(
            self.contents,
            text="Enter the zero'th-indexed ID number of a particle you would like to locate on the current plot. A circle will appear that collapses onto the location of that particle on the plot. If you wish to follow this particle from file-to-file, try using Particle > Track instead.\nYou can press "+hotkeys_to_string("quick find particle")+" to quickly repeat this function without a prompt.",
            wraplength=self.width-2*self.cget('padx'),
            justify='left',
        )

        self.frame = tk.Frame(self.contents)
        self.entry = IntegerEntry(
            self.frame,
            variable=self.particle,
            allowblank=False,
        )
        
        self.recenter_plot_checkbutton = ttk.Checkbutton(
            self.frame,
            text="Recenter plot",
            variable=self.recenter_plot,
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("findparticle.place_widgets")
        self.description.pack(side='top',fill='both')
        self.entry.pack(side='left',fill='x', expand=True)
        self.recenter_plot_checkbutton.pack(side='left',padx=(5,0))
        self.frame.pack(side='top',fill='x')

    def find_particle(self, *args, **kwargs):
        if globals.debug > 1: print("findparticle.find_particle")
        # See if the particle ID is in the data set
        data = self.gui.data

        # Make extra sure the variable is properly set
        validated = self.entry.validatecommand(self.entry.get())
        if not validated: return None
        value = self.entry.variable.get()
        
        if (data is not None and
            value in np.arange(len(data['data'][list(data['data'].keys())[0]]))):
            return value
        else:
            self.gui.message("Failed to find particle "+str(value),duration=5000)
            self.entry.event_generate("<<ValidateFail>>")
            return None

    def on_ok_button(self,*args,**kwargs):
        if globals.debug > 1: print("findparticle.on_okay_button")
        tkvariable.save()
        particle = self.find_particle() # Do validations
        if particle is not None:
            self.close()
            FindParticle.find(self.gui)

    # time is the amount of time in seconds it takes for the circle to
    # shrink down onto its target
    @staticmethod
    def find(gui, recenter=True, time=1., fps=60.):
        if globals.debug > 1: print("findparticle.find")
        
        if globals.time_mode:
            gui.message("Cannot find particles in time mode")
            return
        if gui.interactiveplot.tracking:
            gui.message("Cannot find particles while tracking")
            return
        if not isinstance(gui.interactiveplot.drawn_object, gui.interactiveplot.plot_types_allowed_finding):
            gui.message("Cannot find particles for this plot type")
            return

        index = tkvariable.get("particle", widget=".!gui.findparticle")
        if index is None:
            gui.message("You must first set a particle to find using Particle > Find")
            return

        ax = gui.interactiveplot.ax
        figure = ax.get_figure()
        canvas = figure.canvas
        
        recenter_plot = tkvariable.get("recenter_plot", widget=".!gui.findparticle")

        if recenter_plot is None: recenter_plot = FindParticle.recenter_plot
        
        xy = gui.interactiveplot.get_xy_data()[index]
        
        if recenter_plot and recenter:
            xlim = np.array(ax.get_xlim())
            ylim = np.array(ax.get_ylim())

            center = np.array([0.5*sum(xlim), 0.5*sum(ylim)])
            new_center = np.array(xy)

            dc = new_center - center
            xlim += dc[0]
            ylim += dc[1]
                
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
            
            bid = None
            def func(*args, **kwargs):
                FindParticle.find(gui, recenter=False, time=time, fps=fps)
                gui.unbind("<<AfterPlotUpdate>>", bid)
                
            bid = gui.bind("<<AfterPlotUpdate>>", func)
            gui.interactiveplot.update()
            return

        
        # Get the xy location in screen space
        xyscreen = ax.transData.transform(xy)

        # Get the dimensions of the axis in screen space
        axsize = ax.get_window_extent(renderer=canvas.get_renderer())
        radius = ((0.5*axsize.width)**2 + (0.5*axsize.height)**2)**0.5
        
        circle = matplotlib.patches.Circle(
            xyscreen,radius,
            linewidth=1,
            edgecolor='k',
            facecolor='none',
            transform=None,
        )

        ax.add_artist(circle)

        
        speed = radius / time
        nframes = int(fps * time)
        interval = int(1000. / fps) # in ms
        speed = radius / float(interval)
        dr = speed * time

        def update(*args,**kwargs):
            circle.set_radius(max(circle.get_radius()-dr, 0))
            canvas.draw_idle()

            if circle.get_radius() > 0.:
                gui.interactiveplot.after(interval, update)
            else:
                circle.remove()
        
        update()

        
        
