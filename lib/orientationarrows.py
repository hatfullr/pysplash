from functions.rotate import rotate
import numpy as np
import matplotlib.patches
import matplotlib.lines

# This is for plotting red, green, and blue arrows (for x,
# y, and z axes respecitvely) to indicate the orientation
# in the interactive plot 
class OrientationArrows:
    def __init__(self,gui,ax,x0=0.9,y0=0.9,size=0.05,color=('red','limegreen','royalblue'),length_includes_head=True,**kwargs):
        self.gui = gui
        self.ax = ax
        self.x0 = x0
        self.y0 = y0
        self.size = size
        self.color = color
        self.length_includes_head = length_includes_head
        self.kwargs = kwargs

        self.visible = True

        #self.ax.callbacks.connect("xlim changed",self.update)
        #self.ax.callbacks.connect("ylim changed",self.update)
        
        self.artists = []

    def clear(self,*args,**kwargs):
        for artist in self.artists:
            artist.remove()
        self.artists = []
        self.ax.get_figure().canvas.draw_idle()
        
    def draw(self,*args,**kwargs):
        # This function gets called only when the Update button gets pressed
        
        # x and y are given in pixel coordinates

        # Recalculate the unit vectors in case the size has changed
        unit_vectors = np.array([
            [self.size,0.       ,0.       ],
            [0.       ,self.size,0.       ],
            [0.       ,0.       ,self.size],
        ])
        
        # Get the current rotation from the gui
        anglexdeg = self.gui.controls.rotation_x.get()
        angleydeg = self.gui.controls.rotation_y.get()
        anglezdeg = self.gui.controls.rotation_z.get()

        for i, row in enumerate(unit_vectors):
            unit_vectors[i] = rotate(
                unit_vectors[i][0],
                unit_vectors[i][1],
                unit_vectors[i][2],
                anglexdeg,
                angleydeg,
                anglezdeg,
            )

        self.clear()

        # This is the size of 1 pixel in axis coordinates
        pos = self.ax.transAxes.inverted().transform([[0,0],[1,1]])
        px_width = pos[1][0]-pos[0][0]
        px_height = pos[1][1]-pos[0][1]
        
        for i, unit_vector in enumerate(unit_vectors):
            dx = unit_vector[0]
            dy = unit_vector[1]
            if abs(dx) >= px_width or abs(dy) >= px_height:
                artist = matplotlib.patches.FancyArrow(
                    self.x0,
                    self.y0,
                    dx,
                    dy,
                    color=self.color[i],
                    length_includes_head=self.length_includes_head,
                    width=0.003,
                    transform=self.ax.transAxes,
                    zorder=1.e30,
                    **self.kwargs
                )
                self.artists.append(artist)
                self.ax.add_artist(artist)
            else:
                # This arrow is pointing either directly into or out of the screen
                # This only happens when the 2 axes are perpendicular
                dz = unit_vector[2]

                radius = 0.12*self.size
                line_length = 0.6*radius
                
                artist = matplotlib.patches.Circle(
                    (self.x0,self.y0),
                    radius=radius,
                    color=self.color[i],
                    transform=self.ax.transAxes,
                    zorder=1.e30+1,
                )
                self.artists.append(artist)
                self.ax.add_artist(artist)
                
                if dz > 0:
                    # Pointing out of the screen
                    artist = matplotlib.patches.Circle(
                        (self.x0,self.y0),
                        radius=radius*0.1,
                        color='black',
                        transform=self.ax.transAxes,
                        zorder=1.e30+2,
                    )
                else:
                    # Pointing into the screen
                    vertices = np.array([
                        [self.x0-line_length,self.y0-line_length],
                        [self.x0+line_length,self.y0+line_length],
                        [np.nan,np.nan],
                        [self.x0+line_length,self.y0-line_length],
                        [self.x0-line_length,self.y0+line_length],
                    ])
                    artist = matplotlib.lines.Line2D(
                        vertices[:,0],
                        vertices[:,1],
                        color='black',
                        zorder=1.e30+2,
                        transform=self.ax.transAxes,
                        linewidth=0.5,
                    )
                self.artists.append(artist)
                self.ax.add_artist(artist)
                        
                
