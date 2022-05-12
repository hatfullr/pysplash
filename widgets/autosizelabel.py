import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    import ttk
    from tkFont import Font as tkFont
else:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.font as tkFont

# "truncate" can be one of "left", "right", "both", or None
class AutoSizeLabel(ttk.Label, object):
    truncate_values = ['left','right','both',None]
    truncate_str = ", ".join(["'"+str(t)+"'" for t in truncate_values])
    def __init__(self, master, *args, **kwargs):
        self.truncate = kwargs.pop('truncate', 'both')
        if self.truncate not in AutoSizeLabel.truncate_values:
            raise ValueError("Keyword 'truncate' must be one of "+AutoSizeLabel.truncate_str+". Received '"+str(self.truncate)+"'")
        self._textvariable = kwargs.pop('textvariable',tk.StringVar())
        self.textvariable = tk.StringVar()
        kwargs['textvariable'] = self.textvariable
        
        super(AutoSizeLabel, self).__init__(master, *args, **kwargs)

        self._font = self.get_font()
        self.bind("<Map>", self.on_mapped, add="+")

    def get_font(self, name=None, *args, **kwargs):
        if name is None: name = str(self.cget('font'))
        if sys.version_info.major < 3:
            return tkFont(name=name,exists=True)
        else:
            return tkFont.nametofont(name)

    def configure(self, *args, **kwargs):
        self._font = self.get_font(kwargs.get('font',None))
        super(AutoSizeLabel,self).configure(*args,**kwargs)

    def on_mapped(self, *args, **kwargs):
        self._textvariable.trace("w", self.fit_to_width)
        self.winfo_toplevel().bind("<Configure>", self.fit_to_width, add="+")

    def fit_to_width(self, *args, **kwargs):
        # Fit the textvariable to be the correct width, appending "..." to the front if it's too long
        width = self.winfo_width()
        text = self._textvariable.get()
        textwidth = self._font.measure(text)
        if textwidth > width and self.truncate is not None:
            # Truncate the text
            if self.truncate == 'left':
                for i in range(len(text)):
                    if self._font.measure("..."+text[i:]) < width:
                        text = "..."+text[i:]
                        break
            elif self.truncate == 'right':
                for i in range(len(text),0,-1):
                    if self._font.measure(text[:i]+"...") < width:
                        text = text[:i]+"..."
                        break
            elif self.truncate == 'both':
                center = int(0.5*len(text))
                for i in range(0, center):
                    if self._font.measure("..."+text[i:-(i+1)]+"...") < width:
                        text = "..."+text[i:-(i+1)]+"..."
                        break
        self.textvariable.set(text)
