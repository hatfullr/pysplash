import globals
if globals.support_threading:
    from multiprocessing import Queue
    from sys import version_info
    if version_info.major >= 3: import queue
    else: import Queue as queue
    import threading
    import sys

    class ThreadedTask(threading.Thread,object):
        def __init__(self, master=None, target=None, start=True, args=[], kwargs={},
                     callback=None,callback_args=[],callback_kwargs={},
                     update=None,update_args=[],update_kwargs={}):
            if globals.debug > 1: print("threadedtask.__init__")
            if master is not None:
                self.root = master.winfo_toplevel()
            else: self.root = None
            
            self.target = target
            self.args = args
            self.kwargs = kwargs
            self.callback = callback
            self.callback_args = callback_args
            self.callback_kwargs = callback_kwargs
            self.update = update
            self.update_args = update_args
            self.update_kwargs = update_kwargs
            super(ThreadedTask,self).__init__(target=self.target,args=self.args,kwargs=self.kwargs)
            self.queue = Queue()
            self.started = False
            self._after_id = None
            self.isStop = True
            if start: self.start()

        def stop(self,*args,**kwargs):
            if globals.debug > 1: print("threadedtask.stop")
            if self.root is not None:
                if self._after_id is not None:
                    self.root.after_cancel(self._after_id)
            self.isStop = True

        def start(self,*args,**kwargs):
            if globals.debug > 1: print("threadedtask.start")
            self.started = True
            self.isStop = False
            super(ThreadedTask,self).start(*args,**kwargs)
            
        def run(self,*args,**kwargs):
            if globals.debug > 1: print("threadedtask.run")
            self.queue.put(self.target(*self.args,**self.kwargs),timeout=1)
            self._after_id = None
            self.process_queue()
            
        def process_queue(self,*args,**kwargs):
            if globals.debug > 1: print("threadedtask.process_queue")
            if self.queue.empty() and not self.isStop: # Not finished yet
                if self.update is not None:
                    self.update(*self.update_args,**self.update_kwargs)
                if self.root is not None:
                    if self._after_id is not None:
                        self.root.after_cancel(self._after_id)
                    self._after_id = self.root.after(10, self.process_queue)
            else: # Finished
                if self.root is not None:
                    if self._after_id is not None:
                        self.root.after_cancel(self._after_id)
                if self.isStop: return
                self.queue.get(0)
                if globals.debug > 1: print("threadedtask finished")
                if self.callback is not None:
                    self.callback(*self.callback_args,**self.callback_kwargs)
        
        def isAlive(self,*args,**kwargs):
            try: return super(ThreadedTask, self).isAlive(*args,**kwargs)
            except AttributeError as e:
                try: return self.is_alive(*args,**kwargs)
                except AttributeError: raise(e)
            
                
else:
    class ThreadedTask:
        def __init__(self, master, target=None, start=True, args=[], kwargs={},
                     callback=None,callback_args=[],callback_kwargs={}):
            if globals.debug > 1: print("threadedtask.__init__")
            if target is not None: target(*args,**kwargs)
            if callback is not None: callback(*callback_args,**callback_kwargs)
        def is_alive(self,*args,**kwargs): return False
        def isAlive(self,*args,**kwargs): return False
