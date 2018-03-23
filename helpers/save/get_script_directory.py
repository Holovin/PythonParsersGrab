import inspect
import os
import sys


def get_script_directory(follow_symlinks=True):
    if getattr(sys, 'frozen', False):
        path = os.path.abspath(sys.executable)

    else:
        path = inspect.getabsfile(get_script_directory)

    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)