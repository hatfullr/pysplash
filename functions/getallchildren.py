# Setting order_by_level to True will return the list of all children
# in order of their "depth" in the heirarchy. That is, the end of the
# list will be populated by widgets which have no children and the
# beginning by widgets which do have children.
import numpy as np

def get_all_children(widget, order_by_level=False):
    def get(widget):
        # Ignore combobox popdown listboxes, as we technically shouldn't
        # even be allowed to reference them
        if "popdown.f.l" in widget._w: return []
        children = widget.winfo_children()
        for child in children:
            for grandchild in get(child):
                if grandchild not in children:
                    children.append(grandchild)
        return children
    children = get(widget)
    # The "order" of a widget in the heirarchy is given simply by
    # counting how many "." are in the widget's name
    if order_by_level:
        orders = [child._w.count(".") for child in children]
        idxs = np.argsort(orders)
        children = [children[i] for i in idxs[::-1]]
    return children

"""
def get_all_children(widget, wid=None, order_by_level=False):
    children = widget.winfo_children()
    for child in children:
        for grandchild in get_all_children(child):
            # Only add to the list if the widget isn't already in the list
            if grandchild not in children:
                children.append(grandchild)

    # The "order" of a widget in the heirarchy is given simply by
    # counting how many "." are in the widget's name
    if order_by_level:
        orders = [child._w.count(".") for child in children]
        idxs = np.argsort(orders)
        children = [children[i] for i in idxs[::-1]]
    return children
"""
