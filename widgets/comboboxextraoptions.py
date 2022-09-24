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

    styles_initialized = False
    
    def __init__(self, *args, **kwargs):
        if not ComboboxExtraOptions.styles_initialized:
            style = ttk.Style()
            ComboboxExtraOptions.enabled_choice_style = {
                'fg' : style.lookup("TListbox", "foreground", state=['!disabled']),
                'selectforeground' : style.lookup("TListbox", "foreground", state=['!disabled']),
            }
            ComboboxExtraOptions.disabled_choice_style = {
                'fg' : style.lookup("TListbox", "foreground", state=['disabled']),
                'selectforeground' : style.lookup("TListbox", "foreground", state=['disabled']),
            }
            ComboboxExtraOptions.styles_initialized = True
        self._where = kwargs.pop('where','bottom')
        if self._where not in ['top','bottom']:
            raise ValueError("unrecognized value '"+str(self._where)+"' for keyword 'where'. Must be either 'top' or 'buttom'")

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

        self.divider = None
        self._changing_textvariable = False
        self.disabled_choices = []
        self.previous_selectbackground = {}
        
        
    @property
    def where(self): return self._where
    @where.setter
    def where(self, value):
        if value not in ['top','bottom']:
            raise ValueError("can only set 'where' to 'top' or 'bottom', not '"+str(value))
        self._where = value
        self._on_values_set()

    def __getitem__(self,item):
        if item == 'extra': return self._extra
        return super(ComboboxExtraOptions,self).__getitem__(item)

    def __setitem__(self,item,value):
        if item == 'extra':
            self._extra = value
            self._on_values_set()
            return
        super(ComboboxExtraOptions,self).__setitem__(item,value)
        if item == 'values': self._on_values_set()

    def set(self,value):
        super(ComboboxExtraOptions,self).set(self._sanitize_selection(value))

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

        # Get the names of the currently disabled choices
        disabled_choice_names = [item for i,item in enumerate(self.listbox.get(0,'end')) if i in self.disabled_choices]
        
        # Enable all the choices
        for choice in self.disabled_choices: self.enable_choice(choice)

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

        values = list(self['values'])
        self.listbox.delete(0,'end')
        for i, val in enumerate(values):
            self.listbox.insert(i,val)

        if self.divider is not None: self.disable_choice(self.divider)
        # Disable the choices which were previously disabled, by their names
        for name in disabled_choice_names:
            if name in values:
                self.disable_choice(name)

    def _on_listbox_select(self,*args,**kwargs):
        cursel = self.listbox.curselection()
        if len(cursel) != 0 and cursel[0] in self.disabled_choices: return "break"
        
    def _on_listbox_press(self,*args,**kwargs):
        cursel = self.listbox.curselection()
        if len(cursel) != 0 and cursel[0] in self.disabled_choices: return "break"
    
    def _on_listbox_release(self,*args,**kwargs):
        cursel = self.listbox.curselection()
        if len(cursel) != 0 and cursel[0] in self.disabled_choices: return "break"

    def _on_textvariable_changed(self,*args,**kwargs):
        print("textvariable changed",self.textvariable.get())
        if self._changing_textvariable: return

        value = self._sanitize_selection(self.textvariable.get())
        
        self._changing_textvariable = True
        self.textvariable.set(value)
        self._changing_textvariable = False
            
    # This is a safeguard in case the textvariable somehow gets set to
    # the value of the divider.
    def _sanitize_selection(self, selection):
        if selection == self.divider:
            idx = self._find_divider()
            values = list(self['values'])
            
            # If there's no items in the list after the divider, get an item
            # before the divider if there are any, otherwise set the
            # textvariable to an empty string
            if idx + 1 >= len(values) - 1:
                if idx == 0: selection = ''
                else: selection = values[idx - 1]
            else: selection = values[idx + 1]
            if selection is None:
                raise Exception("selection is None. This should never happen.")
        return selection

    # Selectively 'disable' a given value in the list of values
    def disable_choice(self, choice):
        values = list(self['values'])
        if isinstance(choice, str): choice = values.index(choice)
        if choice not in self.disabled_choices:
            options = ComboboxExtraOptions.disabled_choice_style
            self.previous_selectbackground[choice] = self.listbox.itemcget(choice, "selectbackground")
            options['selectbackground'] = self.listbox.cget('background')
            self.listbox.itemconfig(choice, **options)
            self.disabled_choices.append(choice)

    def enable_choice(self, choice):
        values = list(self['values'])
        if isinstance(choice, str): choice = values.index(choice)
        if choice in self.disabled_choices and choice != self._find_divider():
            options = ComboboxExtraOptions.enabled_choice_style
            if choice in self.previous_selectbackground.keys():
                options['selectbackground'] = self.previous_selectbackground.pop(choice)
            self.listbox.itemconfig(choice, **options)
            self.disabled_choices.remove(choice)
