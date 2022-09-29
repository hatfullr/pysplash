import globals

try:
    from numba import cuda, types
    has_jit = True
except ImportError:
    has_jit = False

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
            self.daemon = True # Needed so that we can kill the thread mid-execution
            self.queue = Queue()
            self.started = False
            self._after_id = None
            self.isStop = False
            if start: self.start()

        def stop(self,*args,**kwargs):
            if globals.debug > 1: print("threadedtask.stop")
            self.isStop = True
            if self in globals.threaded_tasks: globals.threaded_tasks.remove(self)
        
        def start(self,*args,**kwargs):
            if globals.debug > 1: print("threadedtask.start")
            self.started = True
            self.isStop = False
            super(ThreadedTask,self).start(*args,**kwargs)

        def run(self,*args,**kwargs):
            if globals.debug > 1: print("threadedtask.run")
            if self not in globals.threaded_tasks: globals.threaded_tasks.append(self)
            self.queue.put(self.target(*self.args,**self.kwargs),timeout=1)
            self._after_id = None
            self.process_queue()
            
        def process_queue(self,*args,**kwargs):
            if globals.debug > 1: print("threadedtask.process_queue")

            # Have only 1 instance of process_queue running at any given time
            if None not in [self.root, self._after_id]:
                self.root.after_cancel(self._after_id)

            if self.isStop:
                if self in globals.threaded_tasks: globals.threaded_tasks.remove(self)
            else:
                if self.queue.empty(): # Not finished yet
                    if self.update is not None:
                        self.update(*self.update_args,**self.update_kwargs)
                    if self.root is not None:
                        self._after_id = self.root.after(10, self.process_queue)
                else: # Finished
                    self.queue.get(0)
                    if globals.debug > 1: print("threadedtask finished")
                    if self.callback is not None:
                        self.callback(*self.callback_args,**self.callback_kwargs)
                    if self in globals.threaded_tasks: globals.threaded_tasks.remove(self)
        
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
