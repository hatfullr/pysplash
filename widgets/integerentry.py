from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    from flashingentry import FlashingEntry
else:
    import tkinter as tk
    from tkinter import ttk
    from widgets.flashingentry import FlashingEntry
import traceback

# The only difference is we don't allow the user to type
# anything that isn't an integer
class IntegerEntry(FlashingEntry,object):
    def __init__(self,master,validate='focusout',allowblank=True,extra_validatecommands=[],variable=None,disallowed_values=[],**kwargs):
        self.disallowed_values = disallowed_values
        self.extra_validatecommands = extra_validatecommands
        self.allowblank = allowblank
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
            if not isinstance(self.variable, tk.IntVar):
                raise TypeError("Keyword argument 'variable' must be of type tk.IntVar. Received type '"+type(self.variable).__name__+"'")
        else: self.variable = tk.IntVar()

        self.variable.trace("w", self.format_text)

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
        self.variable.set(int(self.get()))
    
    def format_text(self, *args, **kwargs):
        self._textvariable.set(str(self.variable.get()))
