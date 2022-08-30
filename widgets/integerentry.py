from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    from flashingentry import FlashingEntry
else:
    import tkinter as tk
    from tkinter import ttk
    from widgets.flashingentry import FlashingEntry
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import traceback

# The only difference is we don't allow the user to type
# anything that isn't an integer
class IntegerEntry(FlashingEntry,object):
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

        super(IntegerEntry,self).__init__(master,textvariable=self._textvariable,**kwargs)

        self.configure(
            validate=validate,
            validatecommand=(self.register(self.validatecommand),'%P'),
        )
        
        if self.variable is not None:
            if not isinstance(self.variable, (tk.IntVar, IntVar)):
                raise TypeError("Keyword argument 'variable' must be of type tk.IntVar or IntVar. Received type '"+type(self.variable).__name__+"'")
        else: self.variable = tk.IntVar()

        self.variable.trace("w", self.format_text)
        self.do_clamp = self.clamp[0] is not None or self.clamp[1] is not None
        if self.do_clamp: self.variable.trace("w", self.clamp_variable)

        self.bind("<<ValidateFail>>", self.on_validate_fail,add="+")
        self.bind("<<ValidateSuccess>>", self.on_validate_success,add="+")
        
        self.format_text()
            
    def validatecommand(self,newtext):
        # Allow empty text
        if not newtext and self.allowblank:
            self.event_generate("<<ValidateSuccess>>")
            return True

        # Disallow anything else that would cause any problem
        try:
            int(newtext)
        except Exception:
            print(traceback.format_exc())
            self.event_generate("<<ValidateFail>>")
            return False

        if int(newtext) in self.disallowed_values:
            self.event_generate("<<ValidateFail>>")
            return False

        if all([command(newtext) for command in self.extra_validatecommands]):
            self.variable.set(int(newtext))
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
        self.bid = self.bind("<FocusOut>", lambda *args, **kwargs: self.focus())
        
    def on_validate_success(self, *args, **kwargs):
        if self.bid: self.unbind("<FocusOut>", self.bid)
        self.bid = None
        if self.do_clamp: self.clamp_variable()
        else: self.variable.set(int(self.get()))
    
    def format_text(self, *args, **kwargs):
        self._textvariable.set(str(self.variable.get()))

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
