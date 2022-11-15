# coding=utf-8
from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

from widgets.comboboxchoicecontrols import ComboboxChoiceControls

# This widget is like a regular Combobox, but at the very bottom or very top
# are extra user-defined options separated by a divider. The extra options
# are included in the values list, but the divider is not
class ComboboxExtraOptions(ComboboxChoiceControls, object):
    def __init__(self, *args, divider = "─", **kwargs):
        self._where = kwargs.pop('where','bottom')
        if self._where not in ['top','bottom']:
            raise ValueError("unrecognized value '"+str(self._where)+"' for keyword 'where'. Must be either 'top' or 'buttom'")

        self._divider = divider
        
        self._extra = kwargs.pop('extra', [])
        if 'values' in kwargs.keys():
            kwargs['values'] = self._construct_values(kwargs['values'])
        if 'extra' in kwargs.keys():
            disabled = kwargs.get('disabled', [self.divider])
            if self.divider not in disabled:
                disabled.append(self.divider)
            kwargs['disabled'] = disabled
        super(ComboboxExtraOptions,self).__init__(*args,**kwargs)

    def __setitem__(self,item,value):
        if item == 'extra':
            self._extra = value
            self.configure(values=self.values)
            return
        super(ComboboxExtraOptions,self).__setitem__(item,value)
    
    @property
    def divider(self):
        width = 0
        if hasattr(self, 'tk'): width = self.cget('width') # True only if __init__ is finished
        if width == 0: width = 20 # 20 is the Tkinter default width for a combobox
        return self._divider * width
    
    @property
    def values(self):
        values = list(self['values'])
        if len(values) > 0:
            return self._construct_values(values)
        else: return self._extra
    
    @property
    def where(self): return self._where
    @where.setter
    def where(self, value):
        if value not in ['top','bottom']:
            raise ValueError("can only set 'where' to 'top' or 'bottom', not '"+str(value))
        self._where = value
        self.configure(values=self.values)
    
    def _construct_values(self, values):
        if self.where == 'bottom':
            if len(self._extra) > 0: return values + [self.divider] + self._extra
            return values
        elif self.where == 'top':
            if len(self._extra) > 0: return self._extra + [self.divider] + values
            return values
        else:
            raise ValueError("where is '"+str(self.where)+"' which is neither 'top' nor 'bottom'. This should never happen.")
    
    def configure(self,*args,**kwargs):
        original_values = self.values
        self._extra = kwargs.pop('extra', self._extra)
        
        if 'values' in kwargs.keys():
            new_values = kwargs['values']
            old_values = self.values
            for val in self._extra:
                old_values.remove(val)
                if val in new_values: new_values.remove(val)
            if self.divider in old_values: old_values.remove(self.divider)
            if self.divider in new_values: new_values.remove(self.divider)
            kwargs['values'] = self._construct_values(new_values)
        result = super(ComboboxExtraOptions,self).configure(*args,**kwargs)
        if self.divider in kwargs.get('values',[]):
            self.disable_choice(self.divider)
        return result
    
    def config(self,*args,**kwargs):
        return self.configure(*args,**kwargs)
