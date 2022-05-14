from hotkeyslist import hotkeyslist

def hotkeys_to_string(name):
    l = hotkeyslist[name]["keylist"]
    return "("+(", ".join([key_to_string(key) for key in l]))+")"

# This is just to make a more readable keybinding in the GUI
def key_to_string(key):
    return key[1:-1].replace("Control-","Ctrl+").replace("Shift-","Shift+").replace("Alt-","Alt+").replace("space","Spacebar")
