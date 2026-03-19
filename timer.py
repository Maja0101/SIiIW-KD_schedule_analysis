import time
import sys

def timer(func):
    def wrap(*args, **kwargs):
        before = time.time()
        res = func(*args, **kwargs)
        after = time.time()
        print(f"{func.__name__} was executed in {after - before:.6f} s", file=sys.stderr)
        return res
    return wrap