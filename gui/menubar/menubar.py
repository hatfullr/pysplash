from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

from gui.menubar.menu import Menu
from gui.menubar.functionsmenubar import FunctionsMenuBar
from gui.menubar.datamenubar import DataMenuBar
from gui.menubar.plotmenubar import PlotMenuBar

class MenuBar(Menu, object):
    def __init__(self,root,gui,*args,**kwargs):
        self.root = root
        self.gui = gui
        kwargs['tearoff'] = 0
        super(MenuBar,self).__init__(self.root,*args,**kwargs)
        
        self.add_cascade(
            label="Functions",
            menu=FunctionsMenuBar(self,gui),
        )
        self.add_cascade(
            label="Data",
            menu=DataMenuBar(self,gui),
        )
        self.add_cascade(
            label="Plot",
            menu=PlotMenuBar(self,gui),
        )

        self.root.configure(menu=self)
        
    def future_feature(self, *args, **kwargs):
        raise Exception("Future feature")
        

        
