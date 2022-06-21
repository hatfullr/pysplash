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
    def __init__(self,master,left=[],right=[],labels=(None,None),selectmode=('extended','extended'),sort=(False,False)):
        self.labels = labels
        self.selectmode = selectmode
        self.sort = sort
        super(SelectFilter,self).__init__(master)
        
        self._create_widgets()
        self._place_widgets()

        self.left = left
        self.right = right

        for smode, lbox in zip(self.selectmode, [self.listbox_left,self.listbox_right]):
            if smode == 'dragdrop':
                lbox.bind("<<MovedSelected>>", lambda *args, **kwargs: self.event_generate("<<ValuesUpdated>>"), add = "+")

        self.listbox_left.bind("<<ListboxSelect>>", self._on_left_selected, add="+")
        self.listbox_right.bind("<<ListboxSelect>>", self._on_right_selected, add="+")
        self.listbox_left.container.bind("<FocusOut>", self._on_left_focus_out, add="+")
        self.listbox_right.container.bind("<FocusOut>", self._on_right_focus_out, add="+")
                
    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, value):
        if self.sort[0]: self._left = sorted(value)
        else: self._left = value
        self.listbox_left.delete(0,'end')
        for i,val in enumerate(self._left):
            self.listbox_left.insert(i,val)

    @property
    def right(self):
        return self._right

    @right.setter
    def right(self, value):
        if self.sort[1]: self._right = sorted(value)
        else: self._right = value
        self.listbox_right.delete(0,'end')
        for i,val in enumerate(self._right):
            self.listbox_right.insert(i,val)

    def _create_widgets(self,*args,**kwargs):
        self.__left_frame = tk.Frame(self)
        self.__middle_frame = tk.Frame(self)
        self.__right_frame = tk.Frame(self)

        if self.labels[0] is not None:
            self.__left_label = ttk.Label(self.__left_frame,text=self.labels[0],anchor='center')
        if self.labels[1] is not None:
            self.__right_label = ttk.Label(self.__right_frame,text=self.labels[1],anchor='center')

        # exportselection=False makes the <<ListboxSelect>> event work properly. Not quite sure why.
        self.listbox_left = ListboxScrollbar(self.__left_frame,selectmode=self.selectmode[0],exportselection=False)
        self.listbox_right = ListboxScrollbar(self.__right_frame,selectmode=self.selectmode[1],exportselection=False)

        self.left_button = Button(
            self.__middle_frame,
            text="<",width=2,
            command=self.move_selected_left,
            state='disabled',
        )
        self.right_button = Button(
            self.__middle_frame,
            text=">",
            width=2,
            command=self.move_selected_right,
            state='disabled',
        )

    def _place_widgets(self,*args,**kwargs):
        if self.labels[0] is not None:
            self.__left_label.pack(side='top',fill='x',expand=True)
        if self.labels[1] is not None:
            self.__right_label.pack(side='top',fill='x',expand=True)
        
        self.listbox_left.pack(side='top',fill='both',expand=True)
        self.listbox_right.pack(side='top',fill='both',expand=True)

        self.right_button.pack(side='top',pady=(0,2.5))
        self.left_button.pack(side='top',pady=(2.5,0))
        
        self.__left_frame.pack(side='left',fill='both',expand=True)
        self.__middle_frame.pack(side='left',padx=5)
        self.__right_frame.pack(side='left',fill='both',expand=True)

    # Returns the index 
    def move_selected_left(self,*args,**kwargs):
        indices = self.listbox_right.curselection()
        
        moved = [self.right[i] for i in indices]
        self.right = [val for val in self.right if val not in moved]
        self.left += moved

        self.event_generate("<<ValuesUpdated>>")
        
        self.listbox_right.focus()
        if len(indices) == 1: # If we only moved 1 item, try setting the selection to the next item
            next_item = max(0,min(indices[0], len(self.listbox_right.get(0,'end'))-1))
            self.listbox_right.select_set(next_item)
            self.listbox_right.event_generate("<<ListboxSelect>>")

    def move_selected_right(self,*args,**kwargs):
        indices = self.listbox_left.curselection()
        
        moved = [self.left[i] for i in indices]
        self.left = [val for val in self.left if val not in moved]
        self.right += moved

        self.event_generate("<<ValuesUpdated>>")
        
        self.listbox_left.focus()
        if len(indices) == 1: # If we only moved 1 item, try setting the selection to the next item
            next_item = max(0,min(indices[0], len(self.listbox_left.get(0,'end'))-1))
            self.listbox_left.select_set(next_item)
            self.listbox_left.event_generate("<<ListboxSelect>>")

    def update_values(self,left=None,right=None):
        if left is not None: self.left = left
        if right is not None: self.right = right
        if left is not None or right is not None: self.event_generate("<<ValuesUpdated>>")

    def _on_left_selected(self, *args, **kwargs):
        self.left_button.configure(state='disabled')
        self.right_button.configure(state='normal')
        self.update_idletasks()

    def _on_right_selected(self, *args, **kwargs):
        self.left_button.configure(state='normal')
        self.right_button.configure(state='disabled')
        self.update_idletasks()

    def _on_left_focus_out(self,*args,**kwargs):
        current_focus = self.winfo_toplevel().focus_get()
        if current_focus not in [self.listbox_left, self.listbox_right, self.left_button, self.right_button]:
            self.left_button.configure(state='disabled')
            self.right_button.configure(state='disabled')

        if current_focus not in [self.listbox_left, self.right_button]:
            self.listbox_left.selection_clear(0,'end')
        
    def _on_right_focus_out(self,*args,**kwargs):
        current_focus = self.winfo_toplevel().focus_get()
        if current_focus not in [self.listbox_left, self.listbox_right, self.left_button, self.right_button]:
            self.left_button.configure(state='disabled')
            self.right_button.configure(state='disabled')

        if current_focus not in [self.listbox_right, self.left_button]:
            self.listbox_right.selection_clear(0,'end')

