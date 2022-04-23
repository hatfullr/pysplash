from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    from flashingentry import FlashingEntry
else:
    import tkinter as tk
    from tkinter import ttk
    from widgets.flashingentry import FlashingEntry
import numpy as np

# The only difference is we don't allow the user to type
# anything that isn't a float
class FloatEntry(FlashingEntry,object):
    def __init__(self,master,validate='focusout',extra_validatecommands=[],**kwargs):
        self.extra_validatecommands = extra_validatecommands
        self.special_characters = [["."],["E"],["+","-"]]
        self.numbers = ["1","2","3","4","5","6","7","8","9","0"]
        if 'validatecommand' in kwargs.keys(): kwargs.pop('validatecommand')
        self._textvariable = tk.StringVar()
        self.textvariable = kwargs.pop('textvariable')
        
        super(FloatEntry,self).__init__(master,textvariable=self._textvariable,**kwargs)
        self.configure(
            validate=validate,
            validatecommand=(self.register(self.validatecommand),'%P'),
        )
        
        if self.textvariable:
            self.tvtrace_id = self.textvariable.trace("w", self.format_text)


    def validatecommand(self, newtext):
        # Allow empty text
        if not newtext: return True

        # Reformat the text so it is in a regular format for us to check
        newtext = newtext.replace("d","e").replace("D","E").strip()
        newtext = newtext.replace(",",".") # Weird Europeans!
        
        try:
            float(newtext)
        except ValueError:
            self.flash()
            return False

        if all([command(newtext) for command in self.extra_validatecommands]):
            self.textvariable.set(float(newtext))
            self._textvariable.set(newtext)
            return True
        else:
            self.flash()
            return False

    
    # Try to fit the text within the widget, but only to a minimum size of "0.0"
    def format_text(self, *args, **kwargs):
        # Technically this function gets called 2 times, but I am not sure why.
        # This should not affect the result of the function, though
        number = self.textvariable.get()
        total_width = max(3, self.cget('width'))

        # Test the generic conversion
        testtext = "%-G" % number
        
        precision = 0
        if "." in testtext:
            decimalplace = testtext.index(".")
            precision = total_width - testtext.index(".")
            
        self._textvariable.set("%-.*G" % (precision,number))

