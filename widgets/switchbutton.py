from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from widgets.button import Button

class SwitchButton(Button,object):
    def __init__(self,master,command=(None,None),variable=None,*args,**kwargs):
        # False for not-pressed and True for pressed
        self.variable = variable
        if self.variable is None: self.variable = tk.BooleanVar(value=False)
        if not isinstance(self.variable, tk.BooleanVar):
            raise TypeError("Keyword argument 'variable' must be of type tk.BooleanVar. Received '"+type(self.variable).__name__+"'")
        
        super(SwitchButton,self).__init__(master,command=self.command,*args,**kwargs)
        
        # Set the initial button state
        self.state(['pressed'] if self.variable.get() else ['!pressed'])
        
        self._command = command
        
        self.variable.trace('w',self.on_variable_changed)
        
    def on_variable_changed(self, *args, **kwargs):
        # Make the button state always follow exactly the state of the variable
        variable = self.variable.get()
        self.state(['pressed'] if variable else ['!pressed'])
        
        if 'disabled' not in self.state():
            if not hasattr(self._command,"__len__"): command = [self._command,self._command]
            else: command = self._command
            
            if variable: # Variable has just been set from False to True
                if command[0] is not None: command[0](*args, **kwargs)
            # Variable has just been set from True to False
            elif command[1] is not None: command[1](*args, **kwargs)

    def command(self,*args,**kwargs):
        if 'disabled' not in self.state():
            # Flip the variable, setting off chain of events in on_variable_changed
            self.variable.set(not self.variable.get())
    
        
