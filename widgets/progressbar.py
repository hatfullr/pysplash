from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

class ProgressBar(ttk.Frame,object):
    style_initialized = False
    
    def __init__(self,master,textvariable=None,maximum=100,style="ProgressBar.TFrame",borderwidth=1,relief='sunken',*args,**kwargs):
        ttkstyle = ttk.Style()
        if not ProgressBar.style_initialized:
            # https://stackoverflow.com/a/56678946/4954083
            ttkstyle.map(
                "ProgressBar.TFrame",
                background = [
                    ('!disabled', ttkstyle.lookup("TProgressbar",'troughcolor',state=['!disabled'])),
                    ('disabled', ttkstyle.lookup("TProgressbar",'troughcolor',state=['disabled'])),
                ],
                darkcolor = [
                    ('!disabled', ttkstyle.lookup("TProgressbar",'darkcolor',state=['!disabled'])),
                    ('disabled', ttkstyle.lookup("TProgressbar",'darkcolor',state=['disabled'])),
                ],
                lightcolor = [
                    ('!disabled', ttkstyle.lookup("TProgressbar",'lightcolor',state=['!disabled'])),
                    ('disabled', ttkstyle.lookup("TProgressbar",'lightcolor',state=['disabled'])),
                ],
                bordercolor = [
                    ('!disabled', ttkstyle.lookup("TProgressbar",'bordercolor',state=['!disabled'])),
                    ('disabled', ttkstyle.lookup("TProgressbar",'bordercolor',state=['disabled'])),
                ],
            )
            ProgressBar.style_initialized = True

        self.font = kwargs.pop('font', None)
            
        self.maximum = maximum
        super(ProgressBar,self).__init__(
            master,
            *args,
            style=style,
            borderwidth=borderwidth,
            relief=relief,
            **kwargs)
        self._state = ["normal"]
        self.state(self._state)

        self._canvas = tk.Canvas(self,bd=0,highlightthickness=0)
        self._canvas.place(relx=0,rely=0,relwidth=1,relheight=1)

        self._progress_rectangle = self._canvas.create_rectangle(0, 0, 0, 0)
        self._text = self._canvas.create_text(0, 0, text="", font=self.font)
        
        self.value = tk.DoubleVar(value=0)

        self.value.trace('w', self._update_progress)

        self._update_progress

        self.bind("<Configure>", self._resize_canvas)
        self._canvas_width = self.winfo_reqwidth()
        self._canvas_height = self.winfo_reqheight()
        self._canvas.addtag_all("all")


    def set_text(self,new_text):
        self._canvas.itemconfig(self._text, text=new_text)

    def state(self, newstate):
        if "normal" in newstate: newstate[newstate.index("normal")] = "!disabled"
        if newstate != [None]:
            super(ProgressBar,self).state(newstate)
            self._state = newstate
    
    def _get_state(self):
        result = self._state
        if "normal" in self._state:
            result[result.index("normal")] = "!disabled"
        return result
        
    def configure(self, *args, **kwargs):
        self.state([kwargs.pop('state',None)])
        if 'value' in kwargs.keys(): self.value.set(kwargs.pop('value'))
        self.font = kwargs.pop('font', self.font)
        super(ProgressBar,self).configure(*args,**kwargs)
        
    def get_progress_color(self, *args, **kwargs):
        return ttk.Style().lookup("TProgressbar", 'background', state=self._get_state())
    def get_background_color(self, *args, **kwargs):
        return ttk.Style().lookup("TProgressbar", "troughcolor", state=self._get_state())
    
    def _update_progress(self, *args, **kwargs):
        x1 = int(self.value.get()/float(self.maximum)  * self._canvas_width)
        
        # Update the progress rectangle coordinates
        self._canvas.coords(
            self._progress_rectangle,
            0,
            0,
            x1,
            self._canvas_height,
        )
        # Update the progress rectangle color
        color = self.get_progress_color()
        self._canvas.itemconfig(self._progress_rectangle, fill=color, outline=color)
            

    def _resize_canvas(self, event):
        wscale = float(event.width)/self._canvas_width
        hscale = float(event.height)/self._canvas_height
        self._canvas_width = event.width
        self._canvas_height = event.height
        self._canvas.config(width=self._canvas_width, height=self._canvas_height, bg=self.get_background_color())
        self._canvas.scale("all",0,0,wscale,hscale)

        # Make sure the text is positioned in the center
        center = (self._canvas_width / 2 - 2*self.cget('borderwidth'), self._canvas_height / 2 - 2*self.cget('borderwidth'))
        self._canvas.coords(
            self._text,
            center,
        )
