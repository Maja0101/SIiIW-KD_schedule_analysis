import time
import sys
import os
import inspect
import logging
from functools import wraps

logger = logging.getLogger('basic-logger')
logger.setLevel(logging.DEBUG)

basic_handler = logging.StreamHandler(sys.stderr)
basic_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(basic_handler)

inline_logger = logging.getLogger('inline-logger')
inline_logger.setLevel(logging.DEBUG)

inline_handler = logging.StreamHandler(sys.stderr)
inline_handler.setFormatter(logging.Formatter("%(message)s"))
inline_handler.terminator = ''
inline_logger.addHandler(inline_handler)

def log_inline(msg, *args, **kwargs):
    inline_logger.debug(msg, *args, **kwargs)

def log_inline_end():
    inline_logger.debug('\n')

def log_debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)

SUPRESS = {
    'tabu.py', 
    'user_route.py',
}

def log_time(files_to_suppress=None):
    to_suppress = set(files_to_suppress or [])

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            caller_file = os.path.basename(inspect.currentframe().f_back.f_code.co_filename)
            should_log = caller_file not in to_suppress

            def log_if_allowed(msg, *a, **kw):
                if should_log:
                    logger.info(msg, *a, **kw)

            kwargs["_log_if_allowed"] = log_if_allowed

            before = time.perf_counter()

            result = func(*args, **kwargs)

            if should_log:
                after = time.perf_counter()
                logger.info(
                    "%s was executed in %.6f s",
                    func.__name__,
                    after - before
                )

            return result
        
        return wrapper
    
    return decorator