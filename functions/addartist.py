from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.popupwindow import PopupWindow
from widgets.codetext import CodeText
import matplotlib.artist
import traceback
import globals



class AddArtist(PopupWindow,object):

    def __init__(self, gui):
        if globals.debug > 1: print("addartist.__init__")
        self.gui = gui
        super(AddArtist,self).__init__(
            self.gui,
            title="Add artist",
            oktext="Add",
            okcommand=self.add_artist,
        )

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self._after_id = None


    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.create_variables")
        self.error_text = tk.StringVar(value="")

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.create_widgets")

        self.description = ttk.Label(
            self.contents,
            text="Write any Python Matplotlib plotting code below. You can reference the axis in the plot using the pre-defined variable 'ax'. Your code must assign the variable 'artist' as a Matplotlib Artist.",
            wraplength = self.width-2*self.cget('padx'),
            justify='left',
        )
        self.codetext = CodeText(self.contents)
        self.codetext.insert('0.0',"import matplotlib\nartist = ")

        self.error_label = ttk.Label(self.buttons_frame,textvariable=self.error_text)

    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.place_widgets")

        self.description.pack(side='top',fill='x',pady=(0,self.cget('pady')))
        self.codetext.pack(side='top',fill='both',expand=True)
        self.error_label.pack(side='left',fill='x',expand=True)
        
    def add_artist(self,*args,**kwargs):
        if globals.debug > 1: print("addartist.add_artist")

        ax = self.gui.interactiveplot.ax
        
        # Evaluate the Python script given in the CodeText block
        code = self.codetext.get('0.0','end')
        result = {}
        try:
            exec(code,{'ax':ax},result)
        except:
            print(traceback.format_exc())
            self.error("Error. See terminal for traceback", terminal=False)
            return
        
        if 'artist' not in result:
            self.error("'artist' unassigned")
            return
        
        artist = result['artist']
        if not isinstance(artist, matplotlib.artist.Artist):
            self.error(text="'artist' is type '"+type(artist).__name__+"', not '"+matplotlib.artist.Artist.__name__+"'")
            return
        
        ax.add_artist(artist)
        self.close()

    def error(self, text="", duration=5000, terminal=True):
        if globals.debug > 1: print("addartist.error")
        if terminal: print(text)
        self.error_text.set(text)

        if self._after_id is not None: self.after_cancel(self._after_id)
        self._after_id = self.after(duration, self.clear_error)

    def clear_error(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.clear_error")
        
        if self._after_id is not None: self.after_cancel(self._after_id)
        self._after_id = None
        self.error_text.set("")
