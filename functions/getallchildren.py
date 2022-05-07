import globals

def get_all_children(widget, wid=None):
    children = widget.winfo_children()
    for child in children:
        for grandchild in get_all_children(child):
            children.append(grandchild)
    # Reduce the list down to only unique entries
    seen = set()
    uniq = []
    for x in children:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq

