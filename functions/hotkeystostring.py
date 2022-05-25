from hotkeyslist import hotkeyslist

def hotkeys_to_string(name):
    l = hotkeyslist[name]["display"]
    return "("+l+")"
    #modifiers = hotkeyslist[name]['modifiers']
    #string = "("+"+".join([key_to_string(modifier) for modifier in modifiers])
    #if len(modifiers) > 0: string += "+"
    #keys = "/".join([key_to_string(key) for key in l])
    #string += keys
    #return string+")"

# This is just to make a more readable keybinding in the GUI
#def key_to_string(key):
#    return key[1:-1].replace("Control","Ctrl").replace("space","Spacebar")
