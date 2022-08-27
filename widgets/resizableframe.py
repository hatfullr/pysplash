from sys import version_info, platform
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk
import enum

class CursorResizeEnum(enum.IntEnum):
    Normal = 0
    Left = 1
    TopLeft = 2
    Top = 3
    TopRight = 4
    Right = 5
    BottomRight = 6
    Bottom = 7
    BottomLeft = 8
    """
    # We might not need to do the code below, I'm not sure.
    if platform == "win32":
        TopLeft = "size_nw_se"
        TopRight = "size_ne_sw"
        BottomLeft = "size_ne_sw"
        BottomRight = "size_nw_se"
    elif platform == "darwin": # Mac OS X
        TopLeft = "resizetopleft"
        TopRight = "resizetopright"
        BottomLeft = "resizebottomleft"
        BottomRight = "resizebottomright"
    """

    @property
    def value(self):
        val = self._value_ #super(CursorResizeEnum, self).value
        #if self in [CursorResizeEnum.Left, CursorResizeEnum.Right]: val = "sb_h_double_arrow"
        #elif self in [CursorResizeEnum.Top, CursorResizeEnum.Bottom]: val = "sb_v_double_arrow"
        #elif self == CursorResizeEnum.TopLeft: val = "top_left_corner"
        #elif self == CursorResizeEnum.TopRight: val = "top_right_corner"
        #elif self == CursorResizeEnum.BottomLeft: val = "bottom_left_corner"
        #elif self == CursorResizeEnum.BottomRight: val = "bottom_right_corner"
        #else: val = ''
        if int(self) in [1, 5]: return "sb_h_double_arrow"
        elif int(self) in [3, 7]: return "sb_v_double_arrow"
        elif int(self) == 2: return "top_left_corner"
        elif int(self) == 4: return "top_right_corner"
        elif int(self) == 8: return "bottom_left_corner"
        elif int(self) == 6: return "bottom_right_corner"
        return ''
    
# Keyword "resizable" is for the (x, y) directions
class ResizableFrame(tk.Frame, object):
    def __init__(self, master, mousedetectionwidth=10, resizable=(True, True), **kwargs):
        super(ResizableFrame, self).__init__(master,**kwargs)
        self.mousedetectionwidth = mousedetectionwidth
        self.resizable = resizable

        self._toplevel = self.winfo_toplevel()
        self._toplevel.bind("<Motion>", self.onmotion, add="+")

        self._bid = None

    def getcursor(self, event):
        # Detect if the mouse is near the edge of the frame
        width = self.winfo_width()
        height = self.winfo_height()
        rootx = self.winfo_rootx()
        rooty = self.winfo_rooty()

        x0 = self.winfo_rootx()
        y0 = self.winfo_rooty()
        x1 = x0 + width
        y1 = y0 + height
        x,y = event.x_root, event.y_root
        d = self.mousedetectionwidth
        
        on_left = (abs(x-x0) <= d and
                   (y0-d <= y and y <= y1+d))
        on_right = (abs(x-x1) <= d and
                    (y0-d <= y and y <= y1+d))
        on_top = (abs(y-y0) <= d and
                  (x0-d <= x and x <= x1+d))
        on_bottom = (abs(y-y1) <= d and
                     (x0-d <= x and x <= x1+d))
        
        if on_left and on_top: return CursorResizeEnum.TopLeft
        if on_right and on_top: return CursorResizeEnum.TopRight
        if on_left and on_bottom: return CursorResizeEnum.BottomLeft
        if on_right and on_bottom: return CursorResizeEnum.BottomRight
        if on_left: return CursorResizeEnum.Left
        if on_right: return CursorResizeEnum.Right
        if on_top: return CursorResizeEnum.Top
        if on_bottom: return CursorResizeEnum.Bottom

        return CursorResizeEnum.Normal
        
    def onmotion(self, event):
        self.cursor = self.getcursor(event)

        if self.cursor == CursorResizeEnum.Normal:
            if self._bid is not None:
                self._toplevel.unbind("<B1-Motion>", self._bid)
                self._bid = None
        else:
            self._bid = self._toplevel.bind("<B1-Motion>", self.onB1motion)
        
        self.configure(cursor=self.cursor.value)
        self._toplevel.configure(cursor=self.cursor.value)

    def onB1motion(self, event):
        width = self.winfo_width()
        height = self.winfo_height()
        rootx = self.winfo_rootx()
        rooty = self.winfo_rooty()

        miny = self.master.winfo_rooty()
        maxy = miny + self.master.winfo_height()
        minx = self.master.winfo_rootx()
        maxx = minx + self.master.winfo_width()
        
        ytop = rooty
        ybottom = ytop + height
        xleft = rootx
        xright = xleft + width

        if self.cursor in [CursorResizeEnum.Top, CursorResizeEnum.TopLeft, CursorResizeEnum.TopRight]: ytop = event.y_root
        if self.cursor in [CursorResizeEnum.Bottom, CursorResizeEnum.BottomLeft, CursorResizeEnum.BottomRight]: ybottom = event.y_root
        if self.cursor in [CursorResizeEnum.Left, CursorResizeEnum.TopLeft, CursorResizeEnum.BottomLeft]: xleft = event.x_root
        if self.cursor in [CursorResizeEnum.Right, CursorResizeEnum.TopRight, CursorResizeEnum.BottomRight]: xright = event.x_root

        ytop = max(miny,ytop)
        ybottom = min(maxy,ybottom)
        xleft = max(minx,xleft)
        xright = min(maxx,xright)

        relx, rely, anchor=(xleft-minx)/(maxx-minx),(ytop-miny)/(maxy-miny),'nw'
        window_geometry = self._toplevel.geometry()
        self.place(relx=relx,rely=rely,height=ybottom-ytop, width=xright-xleft,anchor=anchor)
        self._toplevel.geometry(window_geometry) # Keep the window at the same size

        self.configure(cursor=self.cursor.value)
        self._toplevel.configure(cursor=self.cursor.value)
