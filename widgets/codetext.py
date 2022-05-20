from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    import __builtin__ as builtins
else:
    import tkinter as tk
    from tkinter import ttk
    import builtins
    
import re
import types

# This is just a tk.Text widget that can do syntax highlighting
# Can't figure out how to highlight strings and comment blocks,
# so that isn't implemented here yet...

class CodeText(tk.Text,object):
    reserved_names = [
        'class',
        'self',
        'print',
        'if',
        'else',
        'elif',
        'is',
        'and',
        'or',
        'in',
        'def',
        'with',
        'as',
        'assert',
        'break',
        'continue',
        'del',
        'except',
        'finally',
        'try',
        'for',
        'from',
        'global',
        'import',
        'lambda',
        'nonlocal',
        'not',
        'pass',
        'raise',
        'return',
        'while',
        'with'
        'yield',
        'False',
        'None',
        'True',
    ]
    builtin_function_names = [name for name, obj in vars(builtins).items() 
                              if isinstance(obj, types.BuiltinFunctionType)]
    exception_names = [
        'BaseException',
        'Exception',
        'ArithmeticError',
        'BufferError',
        'LookupError',
        'AssertionError',
        'AttributeError',
        'EOFError',
        'FloatingPointError',
        'GeneratorExit',
        'ImportError',
        'ModuleNotFoundError',
        'IndexError',
        'KeyError',
        'KeyboardInterrupt',
        'MemoryError',
        'NameError',
        'NotImplementedError',
        'OSError',
        'OverflowError',
        'RecursionError',
        'ReferenceError',
        'RuntimeError',
        'StopIteration',
        'StopAsyncIteration',
        'SyntaxError',
        'IdentificationError',
        'TabError',
        'SystemError',
        'SystemExit',
        'TypeError',
        'UnboundLocalError',
        'UnicodeError',
        'UnicodeEncodeError',
        'UnicodeDecodeError',
        'UnicodeTranslateError',
        'ValueError',
        'ZeroDivisionError',
        'EnvironmentError',
        'IOError',
        'WindowsError',
        'BlockingIOError',
        'ChildProcessError',
        'ConnectionError',
        'BrokenPipeError',
        'ConnectionAbortedError',
        'ConnectionRefusedError',
        'ConnectionResetError',
        'FileExistsError',
        'FileNotFoundError',
        'InterruptedError',
        'IsADirectoryError',
        'NotADirectoryError',
        'PermissionError',
        'ProcessLookupError',
        'TimeoutError',
        'Warning',
        'UserWarning',
        'DeprecationWarning',
        'PendingDeprecationWarning',
        'SyntaxWarning',
        'RuntimeWarning',
        'FutureWarning',
        'ImportWarning',
        'UnicodeWarning',
        'BytesWarning',
        'ResourceWarning'
    ]

    def __init__(self,master,*args,**kwargs):
        kwargs['font'] = kwargs.get('font', 'TkFixedFont')
        kwargs['wrap'] = kwargs.get('wrap','none')
        
        frame = tk.Frame(master)
        self.hscrollbar = ttk.Scrollbar(frame,orient='horizontal')
        self.vscrollbar = ttk.Scrollbar(frame,orient='vertical')
        
        kwargs['xscrollcommand'] = self.hscrollbar.set
        kwargs['yscrollcommand'] = self.vscrollbar.set
        super(CodeText,self).__init__(frame,*args,**kwargs)
        self.hscrollbar.configure(command=self.xview)
        self.vscrollbar.configure(command=self.yview)
        
        frame.columnconfigure(0,weight=1)
        frame.rowconfigure(0,weight=1)
        self.grid(row=0,column=0,sticky='news')
        self.hscrollbar.grid(row=1,column=0,sticky='ew')
        self.vscrollbar.grid(row=0,column=1,sticky='ns')
        
        self.pack = frame.pack
        self.grid = frame.grid
        self.place = frame.place
        
        self.unbind("<Tab>")
        def tab(event):
            self.insert(self.index('insert'),'    ')
            return "break"
        self.bind("<Tab>",tab)
        
        self.root = master.winfo_toplevel()
        # Chosen from Emacs
        self.colors = {
            'reserved'       : '#a020f0',
            'reserved_types' : '#008b8e',
            'builtins'       : '#4c3d8b',
            'variables'      : '#a0522d',
            'functions'      : '#0400ff',
            'comments'       : '#b2232a',
            'strings'        : '#8b2252',
            'exceptions'     : '#228b22',
        }
        
        self.ntags = 0
        self.bind("<KeyRelease>",self.highlight)

        # Highlight the text whenever the text is modified
        #self.bind("<KeyPress>", self.highlight)
        self.bind("<<TextModified>>", self.highlight)
        self.bind("<Button-2>", self.highlight)
        
    def highlight(self,*args,**kwargs):
        # Search the text for any keywords and highlight them

        # Clear all the current tags
        for tag in self.tag_names():
            self.tag_delete(tag)
        
        text = self.get('1.0','end')

        function = False
        comment = False
        index = 0
        index_end = 0
        self.ntags = 0
        
        for lineno,line in enumerate(text.splitlines()):
            index = 0
            index_end = 0
            comment = False
            splits = re.split('\W+',line)
            finds = re.findall('\W+',line+'\n')
            for i,(s,f) in enumerate(zip(splits,finds)):
                color = None

                if comment:
                    color = self.colors['comments']
                elif '#' in f: # Begin comment
                    comment = True
                    color = self.colors['comments']
                    index = line.index('#')
                elif function:
                    color = self.colors['functions']
                    function = False
                elif s in CodeText.reserved_names:
                    if s == 'def': function = True
                    if s[0].isupper(): color = self.colors['reserved_types']
                    else: color = self.colors['reserved']
                elif s in CodeText.exception_names: color = self.colors['exceptions']
                elif '=' in f: color = self.colors['variables']
                elif s in CodeText.builtin_function_names: color = self.colors['builtins']
                
                if comment:
                    index_end = len(line)
                else:
                    index_end = index+len(s)
                
                if color is not None:
                    self.tag_add(
                        str(self.ntags),
                        str(lineno+1)+'.'+str(index),
                        str(lineno+1)+'.'+str(index_end),
                    )
                    self.tag_configure(
                        str(self.ntags),
                        foreground=color,
                    )
                    self.ntags += 1
                
                if not comment: index += len(s+f)

    def insert(self, *args, **kwargs):
        super(CodeText,self).insert(*args,**kwargs)
        self.event_generate("<<TextModified>>")

    def delete(self, *args, **kwargs):
        super(CodeText,self).delete(*args,**kwargs)
        self.event_generate("<<TextModified>>")
