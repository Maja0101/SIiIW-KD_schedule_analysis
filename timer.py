import time
import sys
import os
import inspect

def suppress_timer(files):
    files = set(files)
    for frame in inspect.stack()[1:]:
        try:
            name = os.path.basename(frame.filename)
            if name in files:
                return True
        except Exception:
            continue
    return False

def timer(func, files_to_suppress=['tabu.py', 'user_route.py']):
    def wrap(*args, **kwargs):
        if suppress_timer(files_to_suppress):
            res = func(*args, **kwargs)
        else:
            before = time.time()
            res = func(*args, **kwargs)
            after = time.time()
            print(f"{func.__name__} was executed in {after - before:.6f} s", file=sys.stderr)
        return res
    return wrap