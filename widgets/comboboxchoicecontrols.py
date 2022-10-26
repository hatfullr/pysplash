from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

# This is a Combobox for which individual choices can be disabled

class ComboboxChoiceControls(ttk.Combobox, object):
    styles_initialized = False
    
    def __init__(self, *args, **kwargs):
        if not ComboboxChoiceControls.styles_initialized:
            style = ttk.Style()
            ComboboxChoiceControls.listbox_enabled_choice_style = {
                'fg' : style.lookup("TListbox", "foreground", state=['!disabled']),
                'selectforeground' : style.lookup("TListbox", "foreground", state=['!disabled']),
            }
            ComboboxChoiceControls.listbox_disabled_choice_style = {
                'fg' : style.lookup("TListbox", "foreground", state=['disabled']),
                'selectforeground' : style.lookup("TListbox", "foreground", state=['disabled']),
            }
            style.map(
                "ComboboxChoiceControls.TCombobox",
                fieldbackground=[
                    ('readonly',style.lookup("Entry.TEntry", "fieldbackground", state=['readonly'])),
                    ('disabled',style.lookup("Entry.TEntry", "fieldbackground", state=['disabled'])),
                    ('!disabled',style.lookup("Entry.TEntry", "fieldbackground", state=['!disabled'])),
                ],
                selectbackground=[
                    ('readonly', style.lookup("Entry.TEntry", "fieldbackground", state=['readonly'])),
                    ('disabled', style.lookup("Entry.TEntry", "fieldbackground", state=['disabled'])),
                    ('!disabled', style.lookup("Entry.TEntry", "fieldbackground", state=['!disabled'])),
                ],
                selectforeground=[
                    ('readonly', style.lookup("Entry.TEntry", "fieldforeground", state=['readonly'])),
                    ('disabled', style.lookup("Entry.TEntry", "fieldforeground", state=['disabled'])),
                    ('!disabled', style.lookup("Entry.TEntry", "fieldforeground", state=['!disabled'])),
                ],
                # This controls the annoying little border that gets drawn around the entry value after
                # selecting a value in the popdown
                selectborderwidth=[
                    ('readonly', 0),
                    ('disabled', 0),
                    ('!disabled',0),
                ],
            )
            ComboboxChoiceControls.styles_initialized = True

        kwargs['style'] = kwargs.get('style', "ComboboxChoiceControls.TCombobox")
        disabled = kwargs.pop('disabled', [])
        if not isinstance(disabled, (tuple,list)): disabled = [disabled]
        super(ComboboxChoiceControls, self).__init__(*args, **kwargs)

        # Update the listbox in the popdown toplevel so that
        # we can reference its name correctly
        self.tk.eval('ttk::combobox::ConfigureListbox %s' % (self))
        self._listbox = tk.Listbox()
        self._listbox._w = '%s.popdown.f.l' % (self) # Reference its name

        # Prevent the user from choosing disabled selections
        def block_disabled_selection(*args,**kwargs):
            cursel = self._listbox.curselection()
            if len(cursel) != 0:
                choice = list(self['values'])[cursel[0]]
                for selection in cursel:
                    choice = list(self['values'])[selection]
                    if self._choices[choice]['state'] == 'disabled':
                        return "break"
        self._listbox.bind("<<ListboxSelect>>",block_disabled_selection,add="+")
        self._listbox.bind("<ButtonRelease-1>",block_disabled_selection,add="+")
        self._listbox.bind("<ButtonPress-1>",block_disabled_selection,add="+")

        self._listbox.bind("<Configure>", self._set_choice_states,add="+")

        self._choices = {}
        for key in list(self['values']):
            self._add_choice(key)

        for choice in disabled:
            self.disable_choice(choice)


        # Here we remove the regular scroll wheel binding on the combobox and replace
        # it with our own, which skips over disabled choices.
        def on_mouse_wheel(event):
            if event.num == 5 or event.delta < 0:
                self.next()
            elif event.num == 4 or event.delta > 0:
                self.previous()
            return "break"

        self.bind("<MouseWheel>", on_mouse_wheel, add="+")
        self.bind("<Button-4>", on_mouse_wheel, add="+")
        self.bind("<Button-5>", on_mouse_wheel, add="+")

        self._listbox.bind("<Up>", self.previous, add="+")
        self._listbox.bind("<Down>", self.next, add="+")

    def __setitem__(self,item,value):
        super(ComboboxExtraOptions,self).__setitem__(item,value)
        if item == 'values': self._on_values_set()

    def set(self,value):
        super(ComboboxExtraOptions,self).set(self._sanitize_selection(value))

    def configure(self, *args, **kwargs):
        result = super(ComboboxChoiceControls, self).configure(*args, **kwargs)
        if 'values' in kwargs.keys(): self._on_values_set()
        self.event_generate("<Configure>")
        return result
    def config(self, *args, **kwargs): return self.configure

    # This is a safeguard in case the textvariable somehow gets set to
    # the value of a disabled choice.
    def _sanitize_selection(self, text):
        values = list(self['values'])
        if text in values:
            current_idx = self.current()
            if self._choices[text]['state'] == 'disabled':
                self.next()
                if self.current() == current_idx: # Going to the next value failed
                    text = ""
        return text

    def _add_choice(self, name):
        if name not in list(self['values']):
            raise ValueError("cannot add choice '"+str(name)+"' because it is not in the list of values for this combobox")
        listbox_values = self._listbox.get(0,'end')
        self._choices[name] = {
            'state' : 'enabled',
            'previous_selectbackground' : self._listbox.itemcget(listbox_values.index(name), "selectbackground"),
        }

    def _on_values_set(self, *args, **kwargs):
        # Update the listbox we use internally
        self._listbox.delete(0,'end')
        self._listbox.insert('end', *list(self['values']))
        self._update_choices()
        
    def _update_choices(self,*args,**kwargs):
        # Remove choices which are no longer available
        toremove = []
        for choice in self._choices.keys():
            if choice not in list(self['values']):
                toremove.append(choice)
        for choice in toremove: self._choices.pop(choice)
        
        # Add any new choices
        for choice in list(self['values']):
            #print(choice)
            if choice not in self._choices.keys():
                self._add_choice(choice)
        
        # Update the states of the choices
        for choice, val in self._choices.items():
            if val['state'] == 'disabled': self.disable_choice(choice)
            elif val['state'] == 'enabled': self.enable_choice(choice)
            else: raise ValueError("found unrecognized choice state '"+str(val['state'])+"'. This should never happen.")

    def _set_choice_states(self, *args, **kwargs):
        values = self._listbox.get(0,'end')
        for choice, val in self._choices.items():
            idx = values.index(choice)
            if val['state'] == 'enabled':
                options = ComboboxChoiceControls.listbox_enabled_choice_style
                options['selectbackground'] = self._choices[choice]['previous_selectbackground']
                self._listbox.itemconfig(idx, **options)
                self._choices[choice]['state'] = 'enabled'
            elif val['state'] == 'disabled':
                options = ComboboxChoiceControls.listbox_disabled_choice_style
                self._choices[choice]['previous_selectbackground'] = self._listbox.itemcget(idx, "selectbackground")
                options['selectbackground'] = self._listbox.cget('background')
                self._listbox.itemconfig(idx, **options)
                self._choices[choice]['state'] = 'disabled'
            else:
                raise ValueError("unrecognized state '"+str(val['state'])+"'. Must be one of 'enabled' or 'disabled'")
            
    # Choose the next value in the list of values if possible, otherwise do nothing
    # If the current value isn't in the list of values, do nothing
    def next(self,*args,**kwargs):
        values = list(self['values'])
        index = self.current()
        position = index
        start = index + 1 if index < len(values) - 1 else 0
        for i in range(start, start + len(values)):
            position = i
            if i >= len(values): position -= len(values)
            if self._choices[values[position]]['state'] == 'enabled':
                self.current(position)
                if self._listbox.winfo_ismapped():
                    self._listbox.selection_clear(min(self._listbox.curselection()), max(self._listbox.curselection()))
                    self._listbox.selection_set(position)
                    return "break"
                return

    def previous(self,*args,**kwargs):
        values = list(self['values'])
        index = self.current()
        position = index
        start = index - 1 if index > 0 else len(values) - 1
        for i in range(start, start - len(values), -1):
            position = i
            if i < 0: position += len(values)
            if self._choices[values[position]]['state'] == 'enabled':
                self.current(position)
                if self._listbox.winfo_ismapped():
                    self._listbox.selection_clear(min(self._listbox.curselection()), max(self._listbox.curselection()))
                    self._listbox.selection_set(position)
                    return "break"
                return

    # Selectively 'disable' a given value in the list of values
    def disable_choice(self, choice):
        if isinstance(choice, int): choice = list(self['values'])[choice]
        self._choices[choice]['state'] = 'disabled'

    def enable_choice(self, choice):
        if isinstance(choice, int): choice = list(self['values'])[choice]
        self._choices[choice]['state'] = 'enabled'
