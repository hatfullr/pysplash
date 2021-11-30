from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

from functions.downloaddatafromserver import download_data_from_server

class MenuBar(tk.Menu, object):
    def __init__(self,root,gui,*args,**kwargs):
        self.root = root
        self.gui = gui
        kwargs['tearoff'] = 0
        super(MenuBar,self).__init__(self.root,*args,**kwargs)
        self.init()
        self.root.configure(menu=self)
        
    def init(self):
        self.create_functionsmenu()
        self.create_datamenu()

    def create_functionsmenu(self):
        menu = Menu(self,name='functions',tearoff=0)
        menu.add_command(label='Make rotation movie', command=self.gui.make_rotation_movie)
        self.add_cascade(label='Functions',menu=menu)

    def create_datamenu(self):
        menu = Menu(self,name='data',tearoff=0)
        menu.add_command(label='Download data from server', command=lambda gui=self.gui: download_data_from_server(gui))
        self.add_cascade(label='Data',menu=menu)
        
    def future_feature(self, *args, **kwargs):
        raise Exception("Future feature")
        
class Menu(tk.Menu, object):
    def __init__(self,master,*args,**kwargs):
        super(Menu,self).__init__(master,*args,**kwargs)
        self.index = 0
        
    def add_command(self,*args,**kwargs):
        super(Menu,self).add_command(*args,**kwargs)
        self.index += 1
        
    def insert_separator(self):
        super(Menu,self).insert_separator(self.index)
        self.index += 1
        
