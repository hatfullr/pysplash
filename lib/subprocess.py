import multiprocessing

class Subprocess(multiprocessing.Process,object):
    def __init__(
            self,
            master,
            target=None,
            args=[],
            kwargs={},
            callback=None,
            callback_args=[],
            callback_kwargs={},
    ):
        self.root = master.winfo_toplevel()
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.callback = callback
        self.callback_args = callback_args
        self.callback_kwargs = callback_kwargs
        super(Subprocess,self).__init__(
            target=self.target,
            args=self.args,
            kwargs=self.kwargs,
        )
        self.queue = multiprocessing.Queue()
        self._after_id = None
    
    def run(self,*args,**kwargs):
        self.queue.put("Process %s" % (self.name))
        self.target(*self.args,**self.kwargs)
        self.process_queue()

    def process_queue(self,*args,**kwargs):
        if self.queue.empty(): # Not finished yet
            if self._after_id is not None:
                self.root.after_cancel(self._after_id)
            self._after_id = self.root.after(10, self.process_queue)
        else: # Finished
            self.queue.get(0)
            if self.callback is not None:
                self.callback(*self.callback_args,**self.callback_kwargs)
            #self.close()
