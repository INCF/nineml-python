from __future__ import absolute_import
from io import IOBase
from future.utils import PY3
from os.path import normpath, join
import sys


# TODO: DOCUMENT THESE:
def join_norm(*args):
    return normpath(join(*args))


def restore_sys_path(func):
    """Decorator used to restore the sys.path
    to the value it was before the function call.
    This is useful for loading modules.
    """
    def newfunc(*args, **kwargs):
        oldpath = sys.path[:]
        try:
            return func(*args, **kwargs)
        finally:
            sys.path = oldpath
    return newfunc


def is_file_handle(handle):
    if PY3:
        return isinstance(handle, IOBase)
    else:
        return isinstance(handle, file)
