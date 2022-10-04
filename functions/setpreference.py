from lib.tkvariable import TkVariable

# Used to add custom preferences for things that are not Tk variables
def set_preference(widget, name, value):
    if str(widget) not in TkVariable.preferences:
        TkVariable.preferences[str(widget)] = {name:value}
    else:
        TkVariable.preferences[str(widget)][name] = value
