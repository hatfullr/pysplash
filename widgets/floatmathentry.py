
from widgets.floatentry import FloatEntry

# This widget supports simple math operations with no variables

class FloatMathEntry(FloatEntry, object):
    def __init__(self, *args, **kwargs):
        super(FloatMathEntry, self).__init__(*args, **kwargs)

    def validatecommand(self, newtext):
        # First evaluate the string, then test it like normal
        result = eval(newtext)
        
        return super(FloatMathEntry, self).validatecommand(str(result))
