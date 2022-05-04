import globals

def get_all_children(widget, finList=[], wid=None):
    if globals.debug > 1: print("get_all_children")
    if wid is None: _list = widget.winfo_children()
    else: _list = wid.winfo_children()
    # make sure the list does not include the given widget
    if widget in _list: _list.remove(widget)
    for item in _list:
        finList.append(item)
        get_all_children(widget, finList=finList,wid=item)
    if widget in finList: finList.remove(widget)
    return finList
