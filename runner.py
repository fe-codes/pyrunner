from multiprocessing import Process, Pipe, Lock
import sys, os, signal

class RunnerProcess(object):
    class Child(Process):
        def __init__(self, child_conn, lock, RunnableClass, *args, **kwargs):
            Process.__init__(self)
            self.child_conn = child_conn
            self.lock = lock
            self.Runnable = RunnableClass
            self.args = args
            self.kwargs = kwargs

            def handler(signum, frame):
                child_conn.close()

            #signal.signal(signal.SIGTERM, handler)


        # child
        def get_request(self):
            #self.lock.acquire()
            args, kwargs = self.child_conn.recv()
            #self.lock.release()
            #print 5
            return args, kwargs
        # child
        def response(self, data, exception=False):
            #self.lock.acquire()
            self.child_conn.send((data, exception))
            #print 'child:', exception,data
            #self.lock.release()

        def run(self):
            # in child process
            # prepare
            runner = self.Runnable(*self.args, **self.kwargs)
            # serve the function
            while True:
                try:
                    args, kwargs = self.get_request()
                    result = runner(*args, **kwargs)
                    self.response(result)
                except EOFError:
                    break
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    sys.excepthook(exc_type, exc_value, exc_traceback)
                    self.response((e, exc_type, exc_value, None), exception=True)
            # exit
            #self.child_conn.close() # should be maintained by the parent?

    def __init__(self, RunnableClass, *args, **kwargs):
        self.parent_conn, self.child_conn = Pipe()
        self.lock = Lock()
        self.child = RunnerProcess.Child(self.child_conn, self.lock, RunnableClass, *args, **kwargs)

        self.raise_error = False

        auto_start=True
        if auto_start:
            self.child.start()

    # parent
    def request(self, *args, **kwargs):
        #self.lock.acquire()
        self.parent_conn.send((args,kwargs))
        #self.lock.release()

    # parent
    def get_response(self):
        #self.lock.acquire()
        data, exception = self.parent_conn.recv()
        #print 'parent:', exception, data
        #self.lock.release()
        return data, exception

    def __call__(self, *args, **kwargs):
        # in parent process
        self.lock.acquire()
        self.request(*args, **kwargs)
        data, exception = self.get_response()
        self.lock.release()
        #print 'data:', data
        #print 'exception:', exception
        if exception:
            e, exc_type, exc_value, exc_traceback = data
            #filename = os.path.split(exc_traceback.tb_frame.f_code.co_filename)[1]
            #lineno = exc_tb.tb_lineno
            #print 'Exception in Child Process: ', exc_type, filename, '@', lineno
            #sys.excepthook(exc_type, exc_value, exc_traceback)
            if self.raise_error:
                raise e
        return data

    def __del__(self):
        # in parent process
        self.parent_conn.close()
        self.child_conn.close()
        # make sure killing self?
        if self.child.is_alive():
            self.child.terminate()
        self.child.join()
