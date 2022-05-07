# This dictionary determines the hotkey bindings for various things.
# Do not edit the keys, only edit the values if you so desire.

hotkeyslist = {
    "next file" : ["<Right>"],
    "previous file" : ["<Left>"],
}


def hotkeys_to_string(name):
    return ", ".join(["'"+key+"'" for key in hotkeyslist[name]])
