from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk

class Button(ttk.Label, object):
    def __init__(self, master, *args, **kwargs):
        self.switch = kwargs.pop('switch', False)
        self.command = kwargs.pop('command', None)
        padding = kwargs.pop('padding', "1 1 1 1") #"0 -1 0 0")
        style = kwargs.pop('style','TButton')

        s = ttk.Style()
        s.map(
            style,
            relief=[
                (('pressed','disabled'),'sunken'),
                (('pressed','!disabled'), 'sunken'),
                (('!pressed','disabled'),'raised'),
                (('!pressed','!disabled'),'raised'),
            ],
        )
        
        super(Button, self).__init__(master, *args, padding=padding, style=style, **kwargs)

        # Mouse hover behavior
        self.bind("<Enter>", self.on_enter, add='+')
        self.bind("<Leave>", self.on_leave, add='+')

        # Mouse click behavior
        self.bind("<ButtonPress-1>", self.on_button1,add='+')
        self.bind("<ButtonRelease-1>", self.on_buttonrelease1,add='+')

        self._button1pressed = False
        self._mousein = False

    def destroy(self, *args, **kwargs):
        self.unbind("<Enter>")
        self.unbind("<Leave>")
        self.unbind("<ButtonPress-1>")
        self.unbind("<ButtonRelease-1>")
        super(Button,self).destroy(*args, **kwargs)

    def on_button1(self, *args, **kwargs):
        self._button1pressed = True
        #print(self.state())
        if 'disabled' not in self.state(): self.state(['pressed'])

    def on_buttonrelease1(self, *args, **kwargs):
        self._button1pressed = False
        # If this button is being used to destroy its parent widget, then
        # we need to do a special try/except clause.
        try:
            if 'disabled' not in self.state():
                if self._mousein and self.command is not None: self.command(*args, **kwargs)

                if self.switch and not hasattr(self, 'variable'): raise AttributeError("If a button is a switch, it needs to have the 'variable' attribute")

                if self.switch:
                    if self.variable.get(): self.state(['pressed'])
                    else: self.state(['!pressed'])
                else: self.state(['!pressed'])
        except tk.TclError as e:
            if "invalid command name" in str(e): return
            raise(e)
            
    def on_enter(self, *args, **kwargs):
        self._mousein = True
        if 'disabled' not in self.state():
            self.state(['active'])
            if self._button1pressed: self.state(['pressed'])

    def on_leave(self, *args, **kwargs):
        self._mousein = False
        if 'disabled' not in self.state():
            self.state(['!active'])
            if self._button1pressed: self.state(['!active','pressed'])

    def configure(self, *args, **kwargs):
        self.command = kwargs.pop('command',self.command)
        super(Button, self).configure(*args, **kwargs)
    
    def invoke(self, *args, **kwargs):
        self.command()
    
