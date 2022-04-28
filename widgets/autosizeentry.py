from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk

class AutoSizeEntry(ttk.Entry, object):
    def __init__(self, master, *args, **kwargs):

        super(AutoSizeEntry, self).__init__(master, *args, **kwargs)

        #self.bind("<Configure>", self.on_configure)

    def on_configure(self, *args, **kwargs):
        print("Hello")
