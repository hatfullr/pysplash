# This dictionary determines the hotkey bindings for various things.
# You can edit the list in "keylist" to as you see fit. The "type"
# can be either "global" or "local", where "global" means the
# hotkey will work everywhere when the application has focus, even
# when e.g. typing in an entry box, and "local" means the hotkey will
# only work when the focus is not set on any particular widget.

hotkeyslist = {
    # Controls hotkeys
    "next file" : {
        "keylist" : ["<Right>"],
        "display" : "RightArrow",
        "modifiers" : [],
        "type" : "global",
    },
    "previous file" : {
        "keylist" : ["<Left>"],
        "display" : "LeftArrow",
        "modifiers" : [],
        "type" : "global",
    },
    "update plot" : {
        "keylist" : ["<space>"],
        "display" : "Spacebar",
        "modifiers" : [],
        "type" : "local",
    },
    "import data" : {
        "keylist" : ["<i>"],
        "display" : "Ctrl+i",
        "modifiers" : ["<Control>"],
        "type" : "global",
    },
    "save" : {
        "keylist" : ["<s>"],
        "display" : "Ctrl+s",
        "modifiers" : ["<Control>"],
        "type" : "global",
    },

    # Plot hotkeys
    "start pan" : {
        "keylist" : ["<ButtonPress-2>"],
        "display" : "MMBPress",
        "modifiers" : [],
        "type" : "local",
    },
    "drag pan" : {
        "keylist" : ["<B2-Motion>"],
        "display" : "MMBMotion",
        "modifiers" : [],
        "type" : "global",
    },
    "stop pan" : {
        "keylist" : ["<ButtonRelease-2>"],
        "display" : "MMBRelease",
        "modifiers" : [],
        "type" : "global",
    },
    "zoom" : {
        # Bind <Button-4> and <Button-5> for tkinter on Linux machines
        "keylist" : ["<MouseWheel>", "<Button-4>", "<Button-5>"],
        "display" : "MouseWheel",
        "modifiers" : [],
        "type" : "local",
    },
    "zoom x" : {
        "keylist" : ["<MouseWheel>", "<Button-4>", "<Button-5>"],
        "display" : "Ctrl+MouseWheel",
        "modifiers" : ["<Control>"],
        "type" : "local",
    },
    "zoom y" : {
        "keylist" : ["<MouseWheel>", "<Button-4>", "<Button-5>"],
        "display" : "Shift+MouseWheel",
        "modifiers" : ["<Shift>"],
        "type" : "local",
    },
    "rotate +x" : {
        "keylist" : [","],
        "display" : ",",
        "modifiers" : [],
        "type" : "local",
    },
    "rotate -x" : {
        "keylist" : ["."],
        "display" : ".",
        "modifiers" : [],
        "type" : "local",
    },
    "rotate +y" : {
        "keylist" : ["["],
        "display" : "[",
        "modifiers" : [],
        "type" : "local",
    },
    "rotate -y" : {
        "keylist" : ["]"],
        "display" : "]",
        "modifiers" : [],
        "type" : "local",
    },
    "rotate +z" : {
        "keylist" : ["\\"],
        "display" : "\\",
        "modifiers" : [],
        "type" : "local",
    },
    "rotate -z" : {
        "keylist" : ["/"],
        "display" : "/",
        "modifiers" : [],
        "type" : "local",
    },
}



