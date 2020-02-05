from threading import Thread
from concurrent.futures import Future
from webapp.helper import log
from concurrent.futures import ThreadPoolExecutor

tp = ThreadPoolExecutor(10) 


def call_with_future(fn, future, args, kwargs):
    try:
        result = fn(*args, **kwargs)
        future.set_result(result)
        log('Threading done')
    except Exception as exc:
        future.set_exception(exc)

def threaded(fn):
    def wrapper(*args, **kwargs):
        future = Future()
        log('Lets thread this')
        Thread(target=call_with_future, args=(fn, future, args, kwargs)).start()
        return future
    return wrapper

def poolthreaded(fn):
    def wrapper(*args, **kwargs):
        return tp.submit(fn, *args, **kwargs)  # returns Future object
    return wrapper