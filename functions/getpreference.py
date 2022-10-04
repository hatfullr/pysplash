from lib.tkvariable import TkVariable

# Used to retrieve custom preferences (or any preference if known)
def get_preference(widget, name, error=False):
    if str(widget) in TkVariable.preferences.keys():
        if name in TkVariable.preferences[str(widget)].keys():
            return TkVariable.preferences[str(widget)][name]
    if error: raise Exception("failed to find preference '"+str(name)+"' for widget '"+str(widget)+"'")
    else: return None
