from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

from widgets.message import Message

class LoadingWheel(Message, object):
    
    def __init__(self,master,*args,**kwargs):
        self._states = [
	    "⢀⠀",
	    "⡀⠀",
	    "⠄⠀",
	    "⢂⠀",
	    "⡂⠀",
	    "⠅⠀",
	    "⢃⠀",
	    "⡃⠀",
	    "⠍⠀",
	    "⢋⠀",
	    "⡋⠀",
	    "⠍⠁",
	    "⢋⠁",
	    "⡋⠁",
	    "⠍⠉",
	    "⠋⠉",
            "⠋⠉",
            "⠉⠙",
            "⠉⠙",
            "⠉⠩",
            "⠈⢙",
            "⠈⡙",
            "⢈⠩",
            "⡀⢙",
            "⠄⡙",
            "⢂⠩",
            "⡂⢘",
            "⠅⡘",
            "⢃⠨",
            "⡃⢐",
            "⠍⡐",
            "⢋⠠",
            "⡋⢀",
            "⠍⡁",
            "⢋⠁",
            "⡋⠁",
            "⠍⠉",
            "⠋⠉",
            "⠋⠉",
            "⠉⠙",
            "⠉⠙",
            "⠉⠩",
            "⠈⢙",
            "⠈⡙",
            "⠈⠩",
            "⠀⢙",
            "⠀⡙",
            "⠀⠩",
            "⠀⢘",
            "⠀⡘",
            "⠀⠨",
            "⠀⢐",
            "⠀⡐",
            "⠀⠠",
            "⠀⢀",
            "⠀⡀",
        ]
        self._state = 0
        self._spinning = False
        self._after_id = None
        self.rate = kwargs.pop('rate',50)
        frame = tk.Frame(master)
        
        super(LoadingWheel,self).__init__(master,*args,**kwargs)
    
    def _spin(self,*args,**kwargs):
        next_state = self._state + 1 if self._state + 1 < len(self._states) else 0
        self.configure(text=self._states[next_state])
        self._state = next_state
        if self._spinning:
            if self._after_id is not None:
                self.after_cancel(self._after_id)
            self._after_id = self.after(self.rate, self._spin)

    def show(self,*args,**kwargs):
        if not self._spinning:
            self._spinning = True
            self._spin()
            super(LoadingWheel,self).show(*args,**kwargs)

    def hide(self,*args,**kwargs):
        if self._spinning:
            self._spinning = False
            if self._after_id is not None:
                self.after_cancel(self._after_id)
                self._after_id = None
            super(LoadingWheel,self).hide(*args,**kwargs)
