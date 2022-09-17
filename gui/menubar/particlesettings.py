from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

import globals
import matplotlib
from widgets.popupwindow import PopupWindow
from widgets.multiartisteditor import MultiArtistEditor
from widgets.colorpicker import ColorPicker
from lib.scatterplot import ScatterPlot, set_neighbor_color

class ParticleSettings(PopupWindow,object):
    def __init__(self, gui, artists, show=False):
        self.gui = gui
        super(ParticleSettings,self).__init__(
            self.gui,
            title="Particle settings",
            oktext="Done",
            okcommand=lambda *args,**kwargs: self.withdraw(),
            name='particlesettings',
            show=show,
            grab=False,
            width=700,
            height=400,
            resizeable=(True,True),
        )
        
        self.cancelbutton.pack_forget()

        self.artists = artists

        self.create_widgets()
        self.place_widgets()

    def create_widgets(self,*args,**kwargs):
        self.multi_artist_editor = MultiArtistEditor(
            self.gui,
            self.contents,
            self.artists,
        )
        self.extra_frame = tk.Frame(self.contents)
        self.neighbor_colors_frame = tk.Frame(self.extra_frame,relief='sunken',bd=1)
        self.neighbor_colors_label = ttk.Label(
            self.neighbor_colors_frame,
            text="Neighbor colors",
        )
        self.neighbor_colors_colorpicker = ColorPicker(
            self.gui,
            self.neighbor_colors_frame,
            command=self.update_neighbor_color,
            default=globals.neighbor_particle_color,
        )
        
    def place_widgets(self,*args,**kwargs):
        self.neighbor_colors_label.pack(side='left',fill='x')
        self.neighbor_colors_colorpicker.pack(side='left',padx=5)
        self.neighbor_colors_frame.pack(side='top',fill='x',ipadx=5,ipady=5)
        self.extra_frame.pack(side='top',fill='x',pady=(0,5))

        self.multi_artist_editor.pack(side='top',fill='both',expand=True)

    def close(self,*args,**kwargs):
        self.withdraw(*args,**kwargs)

    def update_neighbor_color(self,*args,**kwargs):
        set_neighbor_color(self.neighbor_colors_colorpicker.color.get())
        self.gui.interactiveplot._update()
