from __future__ import absolute_import
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
