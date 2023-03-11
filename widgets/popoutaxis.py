from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
import globals

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui.interactiveplot import InteractivePlot
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

# Create a popout window with a plot on it that the user can explore
class PopoutAxis(tk.Toplevel, object):
    def __init__(self, gui, *args, **kwargs):
        if globals.debug > 1: print("popoutaxis.__init__")
        self.gui = gui
        
        super(PopoutAxis, self).__init__(self.gui, *args, **kwargs)

        self.fig = matplotlib.figure.Figure(figsize=(6,6), dpi=int(self.gui.dpi))
        self.ax = self.fig.add_subplot(111)

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        # If the user clicks anywhere on the plot, focus the plot.
        for child in self.winfo_children():
            child.bind("<Button-1>", lambda *args, **kwargs: self.canvas.get_tk_widget().focus_set(), add="+")

        InteractivePlot.set_style(self.fig, self.gui.interactiveplot.style.get())

    def create_variables(self):
        if globals.debug > 1: print("popoutaxis.create_variables")
        self.xycoords = tk.StringVar()
        
    def create_widgets(self):
        if globals.debug > 1: print("popoutaxis.create_widgets")
        #self.canvas = CustomCanvas(self.fig, master=self)
        self.canvas = FigureCanvasTkAgg(self.fig,master=self)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        self.xycoords_label = tk.Label(self,textvariable=self.xycoords,bg='white')
        #self.loading_wheel = LoadingWheel(self, 'sw', bg='white')
        if globals.debug > 0:
            self.draw_button = tk.Button(self,text="Draw",command=self.draw)

    def place_widgets(self):
        if globals.debug > 1: print("popoutaxis.place_widgets")
        
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.toolbar.pack(anchor='w',side='top', fill='x')
        
        self.xycoords_label.place(in_=self.canvas.get_tk_widget(),relx=1,rely=1,anchor='se')
        if globals.debug > 0:
            self.draw_button.place(in_=self.canvas.get_tk_widget(),relx=0,rely=1,anchor='sw')
        

    def plot(self, *args, **kwargs):
        if globals.debug > 1: print("popoutaxis.plot")
        self.ax.plot(*args,**kwargs)
        self.canvas.draw()
    
