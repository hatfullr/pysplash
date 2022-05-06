from widgets.flashingentry import FlashingEntry

# This widget expects as input some math operation using the data in the gui
# widget. For example "rho * opacity" would multiply together the "rho" and
# "opacity" columns in the gui's data.

class MathEntry(FlashingEntry, object):
    def __init__(self, master, gui, *args, **kwargs):
        super(MathEntry, self).__init__(master, *args, **kwargs)
        self.gui = gui
        self.configure(validate='focusout',validatecommand=(self.register(self.validatecommand),'%P'))

    def get_variables_and_units(self, *args, **kwargs):
        # Add some buffer spaces
        text = " "+self.get()+" "
        text = text.replace("^","**").replace("[","(").replace("]",")")

        operators = ["*","-","+","/","%"]
        separators = operators + [" ", "(", ")"]

        # Get the keys to the data dictionary in GUI
        data = self.gui.data['data']
        variables = {}
        physical_units = {}
        display_units = {}
        for key in data.keys():
            if key in text:
                idx = text.index(key)
                left = idx-1
                right = idx+len(key)
                if text[left] in separators and text[right] in separators:
                    variables[key] = self.gui.get_display_data(key)
                    physical_units[key] = self.gui.get_physical_units(key)
                    display_units[key] = self.gui.get_display_units(key)
        return variables, physical_units, display_units

    def get_data(self, text=None):
        if text is None: text = self.get()
        variables, physical_units, display_units = self.get_variables_and_units()
        return eval(text, variables), eval(text, physical_units), eval(text, display_units)

    def validatecommand(self, newtext):
        # Allow empty text
        if not newtext: return True

        try:
            self.get_data(text=newtext)
        except Exception as e:
            self.flash()
            raise
            return False

        self.gui.interactiveplot.set_draw_type("Integrated Value")
        return True
        
