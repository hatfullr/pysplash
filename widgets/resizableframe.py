from sys import version_info, platform
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk
import enum

class CursorResizeEnum(enum.Enum):
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
        val = super(CursorResizeEnum, self).value
        if self in [CursorResizeEnum.Left, CursorResizeEnum.Right]: val = "sb_h_double_arrow"
        elif self in [CursorResizeEnum.Top, CursorResizeEnum.Bottom]: val = "sb_v_double_arrow"
        elif self == CursorResizeEnum.TopLeft: val = "top_left_corner"
        elif self == CursorResizeEnum.TopRight: val = "top_right_corner"
        elif self == CursorResizeEnum.BottomLeft: val = "bottom_left_corner"
        elif self == CursorResizeEnum.BottomRight: val = "bottom_right_corner"
        else: val = ''
        return val
    
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
        
        on_left = abs(event.x_root - rootx) <= self.mousedetectionwidth
        on_right = abs(event.x_root - (rootx + width)) <= self.mousedetectionwidth
        on_top = abs(event.y_root - rooty) <= self.mousedetectionwidth
        on_bottom = abs(event.y_root - (rooty + height)) <= self.mousedetectionwidth

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
