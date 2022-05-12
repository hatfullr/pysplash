from hotkeyslist import hotkeyslist

def hotkeys_to_string(name):
    return ", ".join(["'"+key+"'" for key in hotkeyslist[name]["keylist"]])
