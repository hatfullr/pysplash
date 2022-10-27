# We use these overrides so that we can save the values of all used variables
# to a file, which we can then load when the app is started again.

import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

import os
import globals
import json

def save():
    # Make sure the preferences for sure contain up-to-date values. The reason is
    # because we cannot hook into _tk.globalsetvar, which modifies variables
    # internally, e.g. in Entry widgets etc.
    preferences = TkVariable.preferences
    for variable in TkVariable.variables:
        if str(variable.master) not in TkVariable.preferences.keys():
            preferences[str(variable.master)] = {}
        preferences[str(variable.master)][variable.name] = variable.get()
        
    with open(TkVariable.preferences_path, 'w') as f:
        json.dump(preferences, f, indent=4)

# Get the value of a saved variable by its name, returning the first name match
# among all widgets if widget is None
def get(name,widget=None):
    if widget is None:
        for w in TkVariable.preferences.values():
            if name in w.keys():
                if w[name] is not None:
                    w[name]
        raise Exception("failed to find the widget that "+str(name)+" belongs to")
    elif str(widget) in TkVariable.preferences.keys():
        return TkVariable.preferences[str(widget)].get(name, None)
        #if result is None:
        #    raise Exception("failed to find the widget that "+str(name)+" belongs to")
        #return result


class TkVariable(tk.Variable, object):
    preferences_path = os.path.join(globals.profile_path,"preferences.json")
    variables = []
    preferences = {}
    
    def __init__(self, master, value, name):
        # If the preferences haven't been loaded yet, do that
        if TkVariable.preferences == {} and os.path.isfile(TkVariable.preferences_path):
            with open(TkVariable.preferences_path,'r') as f:
                f.seek(0,2)
                filesize = f.tell()
                if filesize != 0:
                    f.seek(0)
                    TkVariable.preferences = json.load(f)

        self.master = master
        self.name = name
                    
        # Save the value as the current preference if the preference is not set
        if str(self.master) not in TkVariable.preferences.keys():
            TkVariable.preferences[str(self.master)] = {}
            TkVariable.preferences[str(self.master)][self.name] = value
        # Load the value from preferences, if there are any
        else:
            if self.name in TkVariable.preferences[str(self.master)].keys():
                value = TkVariable.preferences[str(self.master)][self.name]
            else:
                TkVariable.preferences[str(self.master)][self.name] = value

        super(TkVariable,self).__init__(master=self.master, value=value)
        TkVariable.variables += [self]
        
    def set(self, value):
        # Save as a preference whenever a variable is set
        TkVariable.preferences[str(self.master)][self.name] = value
        return super(TkVariable, self).set(value)

    def __eq__(self, other):
        if not isinstance(other, (TkVariable, tk.Variable)):
            return NotImplemented
        return (self._name == other._name and
                self._tk == other._tk)


class StringVar(TkVariable, object):
    _default = tk.StringVar._default
    def __init__(self, master, value, name):
        super(StringVar, self).__init__(master, value, name)
    def get(self): # Copied from tk.StringVar
        value = self._tk.globalgetvar(self._name)
        if isinstance(value, str):
            return value
        return str(value)

class IntVar(TkVariable, object):
    _default = tk.IntVar._default
    def __init__(self, master, value, name):
        super(IntVar, self).__init__(master, value, name)
    def get(self): # Copied from tk.IntVar
        """Return the value of the variable as an integer."""
        value = self._tk.globalgetvar(self._name)
        try:
            return self._tk.getint(value)
        except (TypeError, tk.TclError):
            return int(self._tk.getdouble(value))

class DoubleVar(TkVariable, object):
    _default = tk.DoubleVar._default
    def __init__(self, master, value, name):
        super(DoubleVar, self).__init__(master, value, name)
    def set(self, value):
        if value is None:
            raise ValueError("setting a DoubleVar to None is not permitted")
        return super(DoubleVar,self).set(value)
    def get(self): # Copied from tk.DoubleVar
        """Return the value of the variable as a float."""
        return self._tk.getdouble(self._tk.globalgetvar(self._name))

class BooleanVar(TkVariable, object):
    _default = tk.BooleanVar._default
    def __init__(self, master, value, name):
        super(BooleanVar, self).__init__(master, value, name)
        
    # Copied from tk.BooleanVar
    def set(self, value):
        """Set the variable to VALUE."""
        super(BooleanVar, self).set(value) # Added this
        return self._tk.globalsetvar(self._name, self._tk.getboolean(value))

    initialize = set

    def get(self):
        """Return the value of the variable as a bool."""
        try:
            return self._tk.getboolean(self._tk.globalgetvar(self._name))
        except tk.TclError:
            raise ValueError("invalid literal for getboolean()")
