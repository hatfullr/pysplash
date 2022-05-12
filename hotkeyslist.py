# This dictionary determines the hotkey bindings for various things.
# You can edit the list in "keylist" to as you see fit. The "type"
# can be either "global" or "local", where "global" means the
# hotkey will work everywhere when the application has focus, even
# when e.g. typing in an entry box, and "local" means the hotkey will
# only work when the focus is not set on any particular widget.

hotkeyslist = {
    "next file" : {
        "keylist" : ["<Right>"],
        "type" : "global",
    },
    "previous file" : {
        "keylist" : ["<Left>"],
        "type" : "global",
    },
    "update plot" : {
        "keylist" : ["<space>"],
        "type" : "local",
    },
}



