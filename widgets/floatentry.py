from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    from flashingentry import FlashingEntry
else:
    import tkinter as tk
    from tkinter import ttk
    from widgets.flashingentry import FlashingEntry

# The only difference is we don't allow the user to type
# anything that isn't a float
class FloatEntry(FlashingEntry,object):
    def __init__(self,master,validate='focusout',disallowed_values=[],**kwargs):
        self.disallowed_values = disallowed_values
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
        testtext = newtext.replace("d","e").replace("D","E").strip()
        testtext = testtext.replace(",",".") # Weird Europeans!
        
        try:
            float(testtext)
        except ValueError:
            self.flash()
            return False

        self._textvariable.set(testtext)
        return True

    
    # Override the set method so that we try to fit the text within the widget,
    # but only to a minimum size of "0.0"
    def format_text(self, *args, **kwargs):
        # Technically this function gets called 2 times, but I am not sure why.
        # This should not affect the result of the function, though

        number = self.textvariable.get()
        width = self.cget('width')

        self._textvariable.set((("%-"+str(width)+"G") % number).strip())
        
