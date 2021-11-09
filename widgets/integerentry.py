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
# anything that isn't an integer
class IntegerEntry(FlashingEntry,object):
    def __init__(self,master,validate='key',disallowed_values=[],**kwargs):
        self.disallowed_values = disallowed_values
        if 'validatecommand' in kwargs.keys(): kwargs.pop('validatecommand')
        super(IntegerEntry,self).__init__(master,**kwargs)
        self.configure(
            validate=validate,
            validatecommand=(self.register(self.validatecommand),'%P'),
        )
        
    def validatecommand(self,newtext):
        # Allow the entry to be empty
        if not newtext: return True

        # Disallow anything else that would cause any problem
        try:
            int(newtext)
        except:
            self.flash()
            return False

        if int(newtext) in self.disallowed_values:
            self.flash()
            return False
        
        return True
