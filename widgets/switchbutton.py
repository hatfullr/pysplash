from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

class SwitchButton(tk.Button,object):
    def __init__(self,master,command=(None,None),variable=None,relief='raised',**kwargs):
        self.master = master

        # False for not-pressed and True for pressed
        if variable is None: self.variable = tk.BooleanVar(value=False)
        else: self.variable = variable

        if self.variable.get(): relief='sunken'
        
        super(SwitchButton,self).__init__(self.master,command=self.command,relief=relief,**kwargs)
        
        self._command = command
    
    def command(self,*args,**kwargs):
        if self.cget('state') != 'disabled':
            if not hasattr(self._command,"__len__"): command = [self._command,self._command]
            else: command = self._command
            relief = self.cget('relief')
            if relief == 'raised':
                self.configure(relief='sunken')
                self.variable.set(True)
                if command[0] is not None: command[0](*args,**kwargs)
            else:
                self.configure(relief='raised')
                self.variable.set(False)
                if command[1] is not None: command[1](*args,**kwargs)
        
