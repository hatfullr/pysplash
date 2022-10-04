import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
    
# A widget which displays text on top of a frame in some given position

class Message(tk.Label, object):
    def __init__(self, master, anchor, *args, **kwargs):
        self.anchor = anchor
        if 'textvariable' in kwargs.keys():
            raise Exception("textvariable keyword is not allowed for Message objects")
        super(Message,self).__init__(master,*args,**kwargs)
        self.visible = False
        self.show()
        self.persist = False
        self._after_id = None

    def set(self, value, *args, **kwargs):
        self.configure(text=value)
    def get(self, *args, **kwargs):
        return str(self.cget('text'))

    # If persist is True, then this message will not be overwritten by
    # other messages until its duration has ended, even if another
    # persistant message is created.
    def show(self, *args, **kwargs):
        if not self.visible:
            relxy = (1,1) # se default
            if   self.anchor == "nw"     : relxy = (0  ,   0)
            elif self.anchor == "n"      : relxy = (0.5,   0)
            elif self.anchor == "ne"     : relxy = (1  ,   0)
            elif self.anchor == "w"      : relxy = (0  , 0.5)
            elif self.anchor == "center" : relxy = (0.5, 0.5)
            elif self.anchor == "e"      : relxy = (1  , 0.5)
            elif self.anchor == "sw"     : relxy = (0  ,   1)
            elif self.anchor == "s"      : relxy = (0.5,   1)
            self.place(relx=relxy[0], rely=relxy[1], anchor=self.anchor)
            self.visible = True
        
    def hide(self, *args, **kwargs):
        if self.visible:
            self.place_forget()
            self.visible = False

    # When check != None, then only clear the message if check is equal
    # to the current message text
    def clear(self, check=None):
        if check is not None and check != self.get(): return
        
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.hide()
        self.persist = False

    # Give duration=None for an infinite duration. If persist=True, then the
    # message will not be overwitten by any subsequent messages unless if
    # any of those subsequent messages are called with force=True.
    def __call__(self, value, duration=2000, persist=False, force=False):
        if self.persist and not force: return
        self.configure(text=value)
        self.persist = persist
        
        self.show()

        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        
        if duration is not None:
            self._after_id = self.after(duration, self.clear)

    def destroy(self, *args, **kwargs):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        super(Message, self).destroy(*args, **kwargs)
