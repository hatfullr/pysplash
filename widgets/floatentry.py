from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    from tkFont import Font as tkFont
    from flashingentry import FlashingEntry
else:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.font as tkFont
    from widgets.flashingentry import FlashingEntry
from functions.stringtofloat import string_to_float
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar, TkVariable
import numpy as np
import traceback

# The only difference is we don't allow the user to type
# anything that isn't a float
class FloatEntry(FlashingEntry,object):
    def __init__(self,master,validate='focusout',allowblank=True,extra_validatecommands=[],variable=None,disallowed_values=[],clamp=(None,None),periodic=False,**kwargs):
        self.disallowed_values = disallowed_values
        self.extra_validatecommands = extra_validatecommands
        self.allowblank = allowblank
        self.clamp = clamp
        self.periodic = periodic
        self._textvariable = tk.StringVar()
        if 'validatecommand' in kwargs.keys(): kwargs.pop('validatecommand')
        if 'textvariable' in kwargs.keys():
            raise TypeError("Keyword 'textvariable' is not valid")

        self.bid = None
        
        self.variable = variable
        
        super(FloatEntry,self).__init__(master,textvariable=self._textvariable,**kwargs)
        self.configure(
            validate=validate,
            validatecommand=(self.register(self.validatecommand),'%P'),
        )
        
        if self.variable is not None:
            if not isinstance(self.variable, (tk.DoubleVar, DoubleVar)):
                raise TypeError("Keyword argument 'variable' must be of type tk.DoubleVar or DoubleVar. Received type '"+type(self.variable).__name__+"'")
        else: self.variable = tk.DoubleVar()

        self.variable.trace("w", self.format_text)
        self.do_clamp = self.clamp[0] is not None or self.clamp[1] is not None
        if self.do_clamp: self.variable.trace("w", self.clamp_variable)

        # The widget doesn't have the right width until it's mapped
        self.bind("<Map>", lambda *args,**kwargs: self.format_text())
        self.bind("<<ValidateFail>>", self.on_validate_fail,add="+")
        self.bind("<<ValidateSuccess>>", self.on_validate_success,add="+")

    def validatecommand(self, newtext):
        # Allow empty text
        if not newtext and self.allowblank:
            self.event_generate("<<ValidateSuccess>>")
            return True
        
        # Reformat the text so it is in a regular format for us to check
        newtext = newtext.replace("d","e").replace("D","E").strip()
        newtext = newtext.replace(",",".") # Weird Europeans!
        
        try:
            string_to_float(newtext)
        except Exception:
            print(traceback.format_exc())
            self.event_generate("<<ValidateFail>>")
            return False

        if string_to_float(newtext) in self.disallowed_values:
            self.event_generate("<<ValidateFail>>")
            return False
        
        if all([command(newtext) for command in self.extra_validatecommands]):
            self.variable.set(string_to_float(newtext))
            self._textvariable.set(newtext)
            self.event_generate("<<ValidateSuccess>>")
            return True
        else:
            self.event_generate("<<ValidateFail>>")
            return False

        # We passed all tests, so return True
        self.event_generate("<<ValidateSuccess>>")
        return True

    def on_validate_fail(self, *args, **kwargs):
        self.flash()
        self.bid = self.bind("<FocusOut>", lambda *args, **kwargs: self.focus(),add="+")
        
    def on_validate_success(self, *args, **kwargs):
        if self.bid: self.unbind("<FocusOut>", self.bid)
        self.bid = None
        if self.do_clamp: self.clamp_variable()
    
    # Try to fit the text within the widget, but only to a minimum size of "0.0"
    def format_text(self, *args, **kwargs):
        # Technically this function gets called 2 times, but I am not sure why.
        # This should not affect the result of the function, though
        number = self.variable.get()
        fontname = str(self.cget('font'))
        if version_info.major < 3: font = tkFont(name=fontname, exists=True)
        else: font = tkFont.nametofont(fontname)
        width = int(self.winfo_width() / font.measure("A"))
        precision = width
        newtext = ("%-*.*G" % (width,precision,number)).strip()
        while font.measure(newtext) > self.winfo_width():
            precision -= 1
            if precision < 0: break
            newtext = ("%-*.*G" % (width,precision,number)).strip()
        self._textvariable.set(newtext)

    def clamp_variable(self, *args, **kwargs):
        value = self.variable.get()

        clamp = list(self.clamp)
        
        if isinstance(clamp[0], (tk.DoubleVar, DoubleVar)): clamp[0] = clamp[0].get()
        if isinstance(clamp[1], (tk.DoubleVar, DoubleVar)): clamp[1] = clamp[1].get()

        clamp0, clamp1 = clamp

        if clamp0 is not None and clamp1 is not None:
            if self.periodic:
                # Figure out how many times the value winds around the clamp range
                diff = max(clamp) - min(clamp)
                nwinds = 0
                if value >= max(clamp):
                    nwinds = (value - max(clamp))/diff
                    nfrac = nwinds % 1
                    self.variable.set(min(clamp) + diff*nfrac)
                elif value < min(clamp):
                    nwinds = (min(clamp)-value)/diff
                    nfrac = nwinds % 1
                    self.variable.set(max(clamp) - diff*nfrac)
            else:
                if value < min(clamp): self.variable.set(min(clamp))
                elif value > max(clamp): self.variable.set(max(clamp))
        elif (clamp0 is not None and clamp1 is None) and value < clamp0:
            self.variable.set(clamp0)
        elif (clamp0 is None and clamp1 is not None) and value > clamp1:
            self.variable.set(clamp1)

        self.format_text()
