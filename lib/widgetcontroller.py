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
    def __init__(self, widget, *variables, comparison=None, default={}, true={}, false={}, verbose=False):
        self.widget = widget
        self.variables = variables
        self.true = true
        self.false = false
        self.default = default
        self.verbose = verbose
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
            
        self.widget.bind("<Map>", self.update_widget, add="+")

    def __str__(self): return "WidgetController("+str(self.widget)+")"

    def update_widget(self, *args, **kwargs):
        kwargs = {}

        alltrue = True
        allfalse = True
        results = []
        variables = []
        comparisons = []
        for variable, comparison in zip(self.variables, self.comparison):
            variables.append(variable.get())
            comparisons.append(comparison)
            if isinstance(comparison, (list, tuple)):
                results.append(variable.get() in comparison)
                #if variable.get() in comparison: allfalse = False
                #else: alltrue = False
            else:
                results.append(variable.get() == comparison)
                #if variable.get() == comparison: allfalse = False
                #else: alltrue = False

        alltrue = all(results)
        allfalse = all([result == False for result in results])
                
        

        if alltrue:
            kwargs = self.true
        elif allfalse:
            kwargs = self.false
        else:
            kwargs = self.default

        if self.verbose:
            print(self.widget)
            print("   ",variables)
            print("   ",comparisons)
            print("   ",results)
            print("   ",kwargs)
        
        self.widget.configure(**kwargs)
