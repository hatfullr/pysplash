from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

from gui.menubar.menu import Menu
from gui.menubar.functionsmenubar import FunctionsMenuBar
from gui.menubar.datamenubar import DataMenuBar
from gui.menubar.plotmenubar import PlotMenuBar
from gui.menubar.filemenubar import FileMenuBar
from gui.menubar.particlemenubar import ParticleMenuBar
from gui.menubar.about import About

class MenuBar(Menu, object):
    def __init__(self,root,gui,*args,**kwargs):
        self.root = root
        self.gui = gui
        kwargs['tearoff'] = 0
        super(MenuBar,self).__init__(self.root,gui.window,*args,**kwargs)

        self.file = FileMenuBar(self, gui)
        self.functions = FunctionsMenuBar(self, gui)
        self.data = DataMenuBar(self, gui)
        self.plot = PlotMenuBar(self, gui)
        self.particle = ParticleMenuBar(self,gui)

        self.add_cascade(
            label="File",
            menu=self.file,
        )
        self.add_cascade(
            label="Functions",
            menu=self.functions,
        )
        self.add_cascade(
            label="Plot",
            menu=self.plot,
        )
        self.add_cascade(
            label="Data",
            menu=self.data,
        )
        self.add_cascade(
            label="Particle",
            menu=self.particle,
        )
        self.add_command(
            label="About",
            command=lambda *args,**kwargs: About(gui),
        )

        self.root.configure(menu=self)
        
    def future_feature(self, *args, **kwargs):
        raise Exception("Future feature")
