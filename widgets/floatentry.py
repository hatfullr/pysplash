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
    def __init__(self,master,validate='key',disallowed_values=[],**kwargs):
        self.disallowed_values = disallowed_values
        self.special_characters = ["e","E","d","D","+","-",".",","]
        if 'validatecommand' in kwargs.keys(): kwargs.pop('validatecommand')
        super(FloatEntry,self).__init__(master,**kwargs)
        self.configure(
            validate=validate,
            validatecommand=(self.register(self.validatecommand),'%P'),
        )
        self.focusbinding = None
        self.doing_focus_out_validate = False
        
    def validatecommand(self,newtext):
        # Allow the entry to be empty
        if not newtext: return True

        if not self.doing_focus_out_validate:
            # If the entry has any special characters in it, switch behavior
            # from validation on user typing to validation on losing focus.
            if self.focusbinding is None and any([c in newtext for c in self.special_characters]):
                self.focusbinding = self.bind("<FocusOut>", self.on_focus_out)

            if self.focusbinding is not None: return True

        newtext = newtext.replace("d","e").replace("D","E").replace(",",".") # Weird europeans!
            
        # Disallow anything else that would cause any problem
        try:
            float(newtext)
        except:
            self.flash()
            return False

        if float(newtext) in self.disallowed_values:
            self.flash()
            return False
        
        return True

    def on_focus_out(self, event):
        # Run the validation command when we lose focus. If it fails, then
        # reset the focus to this widget until the user fixes the problem
        self.doing_focus_out_validate = True
        if self.validate():
            self.unbind("<FocusOut>",self.focusbinding)
            self.focusbinding = None
        else: self.focus_set()

        self.doing_focus_out_validate = False
