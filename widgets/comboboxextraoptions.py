# coding=utf-8
from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

# This widget is like a regular Combobox, but at the very bottom or very top
# are extra user-defined options separated by a divider. The extra options
# are included in the values list, but the divider is not
class ComboboxExtraOptions(ttk.Combobox, object):
    divider_character = "─"
    def __init__(self, *args, **kwargs):
        self.where = kwargs.pop('where','bottom')
        if self.where not in ['top','bottom']:
            raise ValueError("Unrecognized value '"+str(self.where)+"' for keyword 'where'. Must be either 'top' or 'buttom'")

        extra = kwargs.pop('extra', [])
        
        super(ComboboxExtraOptions,self).__init__(*args,**kwargs)

        self._extra = extra

        # Update the listbox in the popdown toplevel so that
        # we can reference its name correctly
        self.tk.eval('ttk::combobox::ConfigureListbox %s' % (self))
        self.listbox = tk.Listbox()
        self.listbox._w = '%s.popdown.f.l' % (self) # Reference its name

        # Prevent the user from choosing the divider
        self.listbox.bind("<<ListboxSelect>>",self._on_listbox_select,add="+")
        self.listbox.bind("<ButtonRelease-1>",self._on_listbox_release,add="+")
        self.listbox.bind("<ButtonPress-1>",self._on_listbox_press,add="+")
        
        values = self['values']

        self.divider = None
        
    def __getitem__(self,key):
        if key == 'extra': return self._extra
        return super(ComboboxExtraOptions,self).__getitem__(key)

    def __setitem__(self,key,value):
        if key == 'extra':
            self._extra = value
            self._on_values_set()
            return
        super(ComboboxExtraOptions,self).__setitem__(key,value)
        if key == 'values': self._on_values_set()

    def configure(self,*args,**kwargs):
        values_set = False
        if 'extra' in kwargs.keys():
            self._extra = kwargs.pop('extra')
            values_set = True
        super(ComboboxExtraOptions,self).configure(*args,**kwargs)
        if 'values' in kwargs.keys() or values_set: self._on_values_set()
        self.event_generate("<Configure>")

    def config(self,*args,**kwargs):
        self.configure(*args,**kwargs)

    def _find_divider(self,*args,**kwargs):
        if self.divider in self['values']:
            return self['values'].index(self.divider)
        else: return None

    def _on_values_set(self,*args,**kwargs):
        new_values = list(self['values'])
        
        if len(new_values) == 0: # No divider needed
            super(ComboboxExtraOptions,self).__setitem__('values',tuple(self._extra))
            self.divider = None
        elif len(self._extra) > 0: # Divider needed
            # Remove the old divider
            idx = self._find_divider()
            if idx is not None: new_values.pop(idx)
            
            # Create the new divider
            self.divider = ComboboxExtraOptions.divider_character * self.listbox.cget('width')
            if self.where == 'top':
                new_values = list(self._extra) + [self.divider] + new_values
            else:
                new_values = new_values + [self.divider] + list(self._extra)

            super(ComboboxExtraOptions,self).__setitem__('values',tuple(new_values))
        

    def _on_listbox_select(self,*args,**kwargs):
        cursel = self.listbox.curselection()
        if len(cursel) != 0:
            idx = self._find_divider()
            if idx == cursel[0]:
                self.listbox.selection_clear(0,'end')
                return 'break'
        
    def _on_listbox_press(self,*args,**kwargs):
        cursel = self.listbox.curselection()
        if len(cursel) != 0:
            idx = self._find_divider()
            if idx == cursel[0]:
                return 'break'
    
    def _on_listbox_release(self,*args,**kwargs):
        cursel = self.listbox.curselection()
        if len(cursel) != 0:
            idx = self._find_divider()
            if idx == cursel[0]:
                return 'break'

