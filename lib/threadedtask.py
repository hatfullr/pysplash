support_threading = True
if support_threading:
    from multiprocessing import Queue
    from sys import version_info
    if version_info.major >= 3: import queue
    else: import Queue as queue
    import threading
    import sys
    from globals import debug

    class ThreadedTask(threading.Thread,object):
        def __init__(self, master, target=None, start=True, args=[], kwargs={},
                     callback=None,callback_args=[],callback_kwargs={}):
            self.root = master.winfo_toplevel()
            self.target = target
            self.args = args
            self.kwargs = kwargs
            self.callback = callback
            self.callback_args = callback_args
            self.callback_kwargs = callback_kwargs
            super(ThreadedTask,self).__init__(target=self.target,args=self.args,kwargs=self.kwargs)
            self.queue = Queue()
            self.started = False
            self._after_id = None
            if start: self.start()

        def start(self,*args,**kwargs):
            self.started = True
            if debug > 0: print("threadedtask: started")
            super(ThreadedTask,self).start(*args,**kwargs)
            
        def run(self,*args,**kwargs):
            self.queue.put(self.target(*self.args,**self.kwargs),timeout=1)
            self._after_id = None
            self.process_queue()
            
        def process_queue(self,*args,**kwargs):
            if self.queue.empty(): # Not finished yet
                if self._after_id is not None:
                    self.root.after_cancel(self._after_id)
                self._after_id = self.root.after(10, self.process_queue)
                return
            else: # Finished
                self.queue.get(0)
                if debug > 0: print("threadedtask: finished")
                if self.callback is not None:
                    self.callback(*self.callback_args,**self.callback_kwargs)
        if version_info.major < 3:
            def isAlive(self,*args,**kwargs):
                return self.is_alive(*args,**kwargs)
            
                
else:
    class ThreadedTask:
        def __init__(self, master, target=None, start=True, args=[], kwargs={},
                     callback=None,callback_args=[],callback_kwargs={}):
            if target is not None: target(*args,**kwargs)
            if callback is not None: callback(*callback_args,**callback_kwargs)
        def is_alive(self,*args,**kwargs): return False
        def isAlive(self,*args,**kwargs): return False
