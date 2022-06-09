import signal
import sys

def quit(signum, frame):
    sys.exit(1)

def sigint_decorator(func):
    def inner(*args, **kwargs):
        signal.signal(signal.SIGINT, quit) #signal.SIG_IGN
        return func(*args, **kwargs)
    return inner