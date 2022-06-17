from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

from widgets.listboxscrollbar import ListboxScrollbar
from widgets.button import Button

class SelectFilter(tk.Frame,object):
    def __init__(self,master,left=[],right=[],labels=(None,None),selectmode=('extended','extended')):
        self.labels = labels
        self.selectmode = selectmode
        super(SelectFilter,self).__init__(master)
        
        self._create_widgets()
        self._place_widgets()

        self.left = left
        self.right = right

        for smode, lbox in zip(self.selectmode, [self.__listbox_left,self.__listbox_right]):
            if smode == 'dragdrop':
                lbox.bind("<<MovedSelected>>", lambda *args, **kwargs: self.event_generate("<<ValuesUpdated>>"), add = "+")
                
    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, value):
        # Disallow duplicates
        self._left = value#tuple(v for i,v in enumerate(value) if v not in value[:i])
        self.__listbox_left.delete(0,'end')
        for i,val in enumerate(value):
            self.__listbox_left.insert(i,val)

    @property
    def right(self):
        return self._right

    @right.setter
    def right(self, value):
        # Disallow duplicates
        self._right = value#tuple(v for i,v in enumerate(value) if v not in value[:i])
        self.__listbox_right.delete(0,'end')
        for i,val in enumerate(value):
            self.__listbox_right.insert(i,val)

    def _create_widgets(self,*args,**kwargs):
        self.__left_frame = tk.Frame(self)
        self.__middle_frame = tk.Frame(self)
        self.__right_frame = tk.Frame(self)

        if self.labels[0] is not None:
            self.__left_label = ttk.Label(self.__left_frame,text=self.labels[0],anchor='center')
        if self.labels[1] is not None:
            self.__right_label = ttk.Label(self.__right_frame,text=self.labels[1],anchor='center')

        self.__listbox_left = ListboxScrollbar(self.__left_frame,selectmode=self.selectmode[0])
        self.__listbox_right = ListboxScrollbar(self.__right_frame,selectmode=self.selectmode[1])

        self.__left_button = Button(self.__middle_frame,text="<",width=2,command=self.move_selected_left)
        self.__right_button = Button(self.__middle_frame,text=">",width=2,command=self.move_selected_right)

    def _place_widgets(self,*args,**kwargs):
        if self.labels[0] is not None:
            self.__left_label.pack(side='top',fill='x',expand=True)
        if self.labels[1] is not None:
            self.__right_label.pack(side='top',fill='x',expand=True)
        
        self.__listbox_left.pack(side='top',fill='both',expand=True)
        self.__listbox_right.pack(side='top',fill='both',expand=True)

        self.__right_button.pack(side='top',pady=(0,2.5))
        self.__left_button.pack(side='top',pady=(2.5,0))
        
        self.__left_frame.pack(side='left',fill='both',expand=True)
        self.__middle_frame.pack(side='left',padx=5)
        self.__right_frame.pack(side='left',fill='both',expand=True)

    # Returns the index 
    def move_selected_left(self,*args,**kwargs):
        indices = self.__listbox_right.curselection()
        
        moved = [self.right[i] for i in indices]
        self.right = [val for val in self.right if val not in moved]
        self.left += moved

        self.event_generate("<<ValuesUpdated>>")
        
        self.__listbox_right.focus()
        if len(indices) == 1: # If we only moved 1 item, try setting the selection to the next item
            next_item = max(0,min(indices[0], len(self.__listbox_right.get(0,'end'))-1))
            self.__listbox_right.select_set(next_item)
            self.__listbox_right.event_generate("<<ListboxSelect>>")

    def move_selected_right(self,*args,**kwargs):
        indices = self.__listbox_left.curselection()
        
        moved = [self.left[i] for i in indices]
        self.left = [val for val in self.left if val not in moved]
        self.right += moved

        self.event_generate("<<ValuesUpdated>>")
        
        self.__listbox_left.focus()
        if len(indices) == 1: # If we only moved 1 item, try setting the selection to the next item
            next_item = max(0,min(indices[0], len(self.__listbox_left.get(0,'end'))-1))
            self.__listbox_left.select_set(next_item)
            self.__listbox_left.event_generate("<<ListboxSelect>>")

    def update_values(self,left=None,right=None):
        if left is not None: self.left = left
        if right is not None: self.right = right
        if left is not None or right is not None: self.event_generate("<<ValuesUpdated>>")

