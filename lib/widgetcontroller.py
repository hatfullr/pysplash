from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk


# A widget controller controls only the widget states (so far). Any time
# you wish to set the state of a widget based on multiple variables, you
# should create a widget controller. When all widget controllers for a
# widget return True for their variables the widget's 'configure' method
# is called and kwargs_true are used as the input. Likewise when all return
# False, kwargs_false are used.


widget_controllers = {}

class WidgetController:
    def __init__(self, widget, *variables, comparison=None, default={}, true={}, false={}):
        self.widget = widget
        self.variables = variables
        self.true = true
        self.false = false
        self.default = default
        if comparison is None: comparison = [True]*len(self.variables)
        elif len(self.variables) == 1: comparison = [comparison]
        self.comparison = comparison

        if len(variables) != len(self.comparison):
            raise ValueError("keyword 'comparison' must have the same length as 'variables'")

        for variable in self.variables:
            if isinstance(variable, tk.Variable):
                variable.trace('w', self.update_widget)
            else:
                raise TypeError("argument 'variables' must contain only tk.Variable types, not '"+type(variable).__name__+"'")
            
        if self.widget not in widget_controllers.keys():
            widget_controllers[self.widget] = self
        else:
            raise ValueError("cannot create multiple WidgetControllers for a single widget")
            #for controller in widget_controllers[self.widget]:
            #    if controller.variables == self.variables and controller.comparison == self.comparison:
            #        for key, val in true.items():
            #            if key in controller.true.keys() and controller.true[key] != val:
            #                raise ValueError("keyword '"+str(key)+"' with value '"+str(val)+"' in true does not have the same value as the same keyword in '"+str(controller)+"' ("+str(controller.true[key])+")")
            #        for key, val in false.items():
            #            if key in controller.false.keys() and controller.false[key] != val:
            #                raise ValueError("keyword '"+str(key)+"' with value '"+str(val)+"' in false does not have the same value as the same keyword in '"+str(controller)+"' ("+str(controller.false[key])+")")
            #        for key, val in default.items():
            #            if key in controller.default.keys() and controller.default[key] != val:
            #                raise ValueError("keyword '"+str(key)+"' with value '"+str(val)+"' in default does not have the same value as the same keyword in '"+str(controller)+"' ("+str(controller.default[key])+")")
            #widget_controllers[self.widget] += [self]
            
        self.widget.bind("<Map>", self.update_widget, add="+")

    def __str__(self): return "WidgetController("+str(self.widget)+")"

    def update_widget(self, *args, **kwargs):
        kwargs = {}

        alltrue = True
        allfalse = True
        for variable, comparison in zip(self.variables, self.comparison):
            if isinstance(comparison, (list, tuple)):
                if variable.get() in comparison: allfalse = False
                else: alltrue = False
            else:
                if variable.get() == comparison: allfalse = False
                else: alltrue = False

        if alltrue:
            kwargs = self.true
        elif allfalse:
            kwargs = self.false
        else:
            kwargs = self.default
        
        self.widget.configure(**kwargs)
