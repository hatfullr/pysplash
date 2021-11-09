from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.collections import PathCollection

class CustomToolbar(NavigationToolbar2Tk):
    def __init__(self,master,canvas,**kwargs):
        self.toolitems = (
            (u'Home', u'', u'home', u'home'),
            (u'Pan', u'', u'move', u'pan'),
            (u'Zoom', u'', u'zoom_to_rect', u'zoom'),
            (u'Subplots', u'', u'subplots', u'configure_subplots'),
            (u'Save', u'', u'filesave', u'save_figure'),
            )
        self.master = master
        self.canvas = canvas
        self.toolbar = NavigationToolbar2Tk
        self.toolbar._old_Button = self.toolbar._Button
        self.toolbar._Button = self._new_Button
        self.toolbar.__init__(self,self.canvas,self.master)
        self.toolbar.home = self.new_home
        
        self.configure(**kwargs)

        # Remove the "x=... y=..." labels
        for child in self.children:
            if type(child).__name__ == 'Label':
                child.pack_forget()

    def _new_Button(self, *args, **kwargs):
        b = self._old_Button(*args, **kwargs)
        # It expects dpi=100, but we have a different dpi. Because shit is
        # stupid, we have to first increase the image size then decrease it
        # using integers.
        b._ntimage = b._ntimage.zoom(self.canvas.figure.dpi,self.canvas.figure.dpi)
        b._ntimage = b._ntimage.subsample(100,100)
        self.height = b._ntimage.height()
        b.config(height=self.height,image=b._ntimage)
        return b
        
    def new_home(self,*args):
        # The original "home" function looks like this:
        #"""Restore the original view."""
        #self.toolbar._nav_stack.home()
        #self.toolbar.set_history_buttons(self.toolbar)
        #self.toolbar._update_view(self.toolbar)

        self.toolbar.home(self.toolbar)
        
        # We want to do everything the original home function does,
        # but this time correctly set the plotting limits.
        
        # ax[0] is the axis we can see. Not sure what ax[1] is.
        ax = self.canvas.figure.axes[0]
        margin = ax.margins()
        xmin = np.inf
        xmax = -np.inf
        ymin = np.inf
        ymax = -np.inf
        
        # This will work only for scatter plots. Revise in the future if needed.
        for child in ax.get_children():
            if isinstance(child,PathCollection):
                xy = child.get_offsets()
                xmin = min(xmin,np.nanmin(xy[:,0]))
                xmax = max(xmax,np.nanmax(xy[:,0]))
                ymin = min(ymin,np.nanmin(xy[:,1]))
                ymax = max(ymax,np.nanmax(xy[:,1]))

        dx = xmax-xmin
        dy = ymax-ymin
        ax.set_xlim(xmin - dx*margin[0], xmax + dx*margin[0])
        ax.set_ylim(ymin - dy*margin[1], ymax + dy*margin[1])
        self.canvas.draw()
