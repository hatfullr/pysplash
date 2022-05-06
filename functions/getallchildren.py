import globals

def get_all_children(widget, wid=None):
    children = widget.winfo_children()
    for child in children:
        for grandchild in get_all_children(child):
            children.append(grandchild)
    return children

