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
            if not isinstance(self.variable, tk.DoubleVar):
                raise TypeError("Keyword argument 'variable' must be of type tk.DoubleVar. Received type '"+type(self.variable).__name__+"'")
        else: self.variable = tk.DoubleVar()

        self.variable.trace("w", self.format_text)
        self.do_clamp = self.clamp[0] is not None or self.clamp[1] is not None
        if self.do_clamp: self.variable.trace("w", self.clamp_variable)

        # The widget doesn't have the right width until it's mapped
        self.bind("<Map>", lambda *args,**kwargs: self.format_text())

    def validatecommand(self, newtext):
        # Allow empty text
        if not newtext and self.allowblank:
            self.on_validate_success()
            return True
        
        # Reformat the text so it is in a regular format for us to check
        newtext = newtext.replace("d","e").replace("D","E").strip()
        newtext = newtext.replace(",",".") # Weird Europeans!
        
        try:
            string_to_float(newtext)
        except Exception:
            self.on_validate_fail()
            print(traceback.format_exc())
            return False

        if string_to_float(newtext) in self.disallowed_values:
            self.on_validate_fail()
            return False
        
        if all([command(newtext) for command in self.extra_validatecommands]):
            self.variable.set(string_to_float(newtext))
            self._textvariable.set(newtext)
            self.on_validate_success()
            return True
        else:
            self.on_validate_fail()
            return False

        # We passed all tests, so return True
        self.on_validate_success()
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

        if self.clamp[0] is not None and self.clamp[1] is not None:
            if self.periodic:
                # Figure out how many times the value winds around the clamp range
                diff = max(self.clamp) - min(self.clamp)
                nwinds = 0
                if value >= max(self.clamp):
                    nwinds = (value - max(self.clamp))/diff
                    nfrac = nwinds % 1
                    self.variable.set(min(self.clamp) + diff*nfrac)
                elif value < min(self.clamp):
                    nwinds = (min(self.clamp)-value)/diff
                    nfrac = nwinds % 1
                    self.variable.set(max(self.clamp) - diff*nfrac)
            else:
                if value < min(self.clamp): self.variable.set(min(self.clamp))
                elif value > max(self.clamp): self.variable.set(max(self.clamp))
        elif (self.clamp[0] is not None and self.clamp[1] is None) and value < self.clamp[0]:
            self.variable.set(self.clamp[0])
        elif (self.clamp[0] is None and self.clamp[1] is not None) and value > self.clamp[1]:
            self.variable.set(self.clamp[1])

        self.format_text()
