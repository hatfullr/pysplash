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
import numpy as np

# The only difference is we don't allow the user to type
# anything that isn't a float
class FloatEntry(FlashingEntry,object):
    def __init__(self,master,validate='focusout',extra_validatecommands=[],variable=None,disallowed_values=[],**kwargs):
        self.disallowed_values = disallowed_values
        self.extra_validatecommands = extra_validatecommands
        self.special_characters = [["."],["E"],["+","-"]]
        self.numbers = ["1","2","3","4","5","6","7","8","9","0"]
        if 'validatecommand' in kwargs.keys(): kwargs.pop('validatecommand')
        self._textvariable = tk.StringVar()

        if 'textvariable' in kwargs.keys():
            raise TypeError("Keyword 'textvariable' is not valid")

        self.bid = None
        
        self.variable = variable
        
        super(FloatEntry,self).__init__(master,textvariable=self._textvariable,**kwargs)
        self.configure(
            validate=validate,
            validatecommand=(self.register(self.validatecommand),'%P'),
        )
        
        if self.variable:
            if not isinstance(self.variable, tk.DoubleVar):
                raise TypeError("Keyword argument 'variable' must be of type tk.DoubleVar. Received type '"+type(self.variable).__name__+"'")
            self.tvtrace_id = self.variable.trace("w", self.format_text)

        self.format_text()


    def validatecommand(self, newtext):
        # Allow empty text
        if not newtext:
            self.on_validate_success()
            return True
        
        # Reformat the text so it is in a regular format for us to check
        newtext = newtext.replace("d","e").replace("D","E").strip()
        newtext = newtext.replace(",",".") # Weird Europeans!
        
        try:
            float(newtext)
        except ValueError:
            self.on_validate_fail()
            raise
            return False

        if float(newtext) in self.disallowed_values:
            self.on_validate_fail()
            return False
        
        if all([command(newtext) for command in self.extra_validatecommands]):
            self.variable.set(float(newtext))
            self._textvariable.set(newtext)
            self.on_validate_success()
            return True
        else:
            self.on_validate_fail()
            return False

    def on_validate_fail(self, *args, **kwargs):
        self.flash()
        self.bid = self.bind("<FocusOut>", lambda *args, **kwargs: self.focus())
    def on_validate_success(self, *args, **kwargs):
        if self.bid: self.unbind("<FocusOut>", self.bid)
        self.bid = None
    
    # Try to fit the text within the widget, but only to a minimum size of "0.0"
    def format_text(self, *args, **kwargs):
        # Technically this function gets called 2 times, but I am not sure why.
        # This should not affect the result of the function, though
        #print(self.variable.get())
        number = self.variable.get()
        fontname = str(self.cget('font'))
        if version_info.major < 3:
            font = tkFont(name=fontname, exists=True)
        else:
            font = tkFont.nametofont(fontname)
        width = int(self.winfo_width() / font.measure("A"))
        #print(width)
        #total_width = max(3, self.cget('width'))

        # Test the generic conversion
        #testtext = "%-G" % number
        
        #precision = 1
        #if "." in testtext:
        #    decimalplace = testtext.index(".")
        #    precision = max(precision, total_width - testtext.index("."))
        
        self._textvariable.set(("%-*.*G" % (width,width-2,number)).strip())

